from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.urls import urlsplit
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup, escape
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from functools import wraps
import requests
import os
import secrets
import sys
import uuid
import json
from dateutil import parser as date_parser
import re
import logging
import time

import ai_service
from sqlalchemy import func

# Security: Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: Trust Render's reverse proxy so request.remote_addr and scheme are correct
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ---------------------------------------------------------------------------
# Environment / deployment mode
# Render always sets RENDER=true; treat that as production unless explicitly
# opted into development via FLASK_ENV.
# ---------------------------------------------------------------------------
FLASK_ENV = os.getenv('FLASK_ENV', '').strip().lower()
IS_DEVELOPMENT = FLASK_ENV == 'development' or os.getenv('FLASK_DEBUG', '').lower() in ('1', 'true')
IS_PRODUCTION = not IS_DEVELOPMENT

# Security: Debug mode must NEVER be enabled in production
app.config['DEBUG'] = IS_DEVELOPMENT

# Google Business Profile review link (local SEO). Set GOOGLE_REVIEW_URL to the
# g.page/r/XXXX/review short link from the GBP dashboard -> "Ask for reviews".
# When unset, review CTAs on the site link to a Google Maps search for the
# business instead (still functional, just less direct).
GOOGLE_REVIEW_URL = os.getenv('GOOGLE_REVIEW_URL', '').strip()
# Fallback points at the actual workshop location (Agbado Station, Ifo), not a
# generic Lagos search, so the review CTA lands on the right Google listing.
GOOGLE_REVIEW_FALLBACK_URL = (
    'https://www.google.com/maps/search/?api=1&query='
    'Moscool+Technical+Services+16+Oredegbe+Street+Agbado+Station+Ifo+Ogun+State'
)
if not GOOGLE_REVIEW_URL:
    GOOGLE_REVIEW_URL = GOOGLE_REVIEW_FALLBACK_URL

# Public site URL used for canonical/OG/sitemap absolute URLs. Falls back to the
# incoming request host when unset (fine for local dev, set it in production).
SITE_URL = os.getenv('SITE_URL', '').rstrip('/')

# Real-world business details (local SEO). The defaults are the verified NAP
# (name/address/phone) for the Agbado Station workshop; override with env vars
# if the business moves. Keeping them identical to the Google Business Profile
# is what makes the local-pack signal work.
BUSINESS_ADDRESS = (os.getenv('BUSINESS_ADDRESS') or
                    '16, Oredegbe Street, Off Ogundele Street, Agbado Station').strip()
BUSINESS_LOCALITY = (os.getenv('BUSINESS_LOCALITY') or 'Ifo').strip()
BUSINESS_REGION = (os.getenv('BUSINESS_REGION') or 'Ogun State').strip()
BUSINESS_PHONE = os.getenv('BUSINESS_PHONE', '+2349033150460').strip()
BUSINESS_EMAIL = os.getenv('BUSINESS_EMAIL', 'dayotunde25@gmail.com').strip()

# Google Analytics 4 measurement ID (G-XXXXXXXXXX). Analytics is only emitted
# when set, so local/dev traffic is never reported.
GA_MEASUREMENT_ID = os.getenv('GA_MEASUREMENT_ID', '').strip()

# AI studio: queued/cron generation publishes only when explicitly enabled.
# The admin form has its own "publish immediately" checkbox; this default is
# for the topic queue and scripts/generate_ai_drafts.py.
AI_AUTO_PUBLISH = os.getenv('AI_AUTO_PUBLISH', 'false').lower() in ('1', 'true', 'yes')

# Expose settings to Jinja via config (templates use config.get(...))
app.config['GOOGLE_REVIEW_URL'] = GOOGLE_REVIEW_URL
app.config['SITE_URL'] = SITE_URL
app.config['BUSINESS_ADDRESS'] = BUSINESS_ADDRESS
app.config['BUSINESS_LOCALITY'] = BUSINESS_LOCALITY
app.config['BUSINESS_REGION'] = BUSINESS_REGION
app.config['BUSINESS_PHONE'] = BUSINESS_PHONE
app.config['BUSINESS_EMAIL'] = BUSINESS_EMAIL
app.config['GA_MEASUREMENT_ID'] = GA_MEASUREMENT_ID

# Auto-seed sample portfolio posts + SEO articles on first boot (idempotent -
# existing slugs are never touched). Enabled in render.yaml so a fresh deploy
# boots with real-looking content. Set to false (or leave unset) to disable;
# the standalone scripts in scripts/ do the same seeding manually.
SEED_SAMPLE_CONTENT = os.getenv('SEED_SAMPLE_CONTENT', 'false').lower() in ('1', 'true', 'yes')

# Security: Load secret key from environment (REQUIRED in production)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    if IS_PRODUCTION:
        logger.critical("SECRET_KEY not configured. Set the SECRET_KEY environment variable in Render -> Environment.")
        raise RuntimeError("SECRET_KEY environment variable must be set in production")
    # Development convenience: generate an ephemeral key (sessions reset per restart)
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    logger.warning("SECRET_KEY not set - using an ephemeral development key. Set SECRET_KEY in production.")

# Security: Session cookie flags
# SECURE: only sent over HTTPS. Render terminates TLS, so enable outside local dev.
app.config['SESSION_COOKIE_SECURE'] = not IS_DEVELOPMENT
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# SQLAlchemy configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///moscool_tech.db')
# Render provides postgres:// URLs; SQLAlchemy 2.x requires postgresql:// scheme.
# The +psycopg2 suffix explicitly selects the installed driver (psycopg2-binary):
# SQLAlchemy 2.1 changed the default for bare postgresql:// URLs to psycopg3,
# which would crash the app with ModuleNotFoundError: No module named 'psycopg'.
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = 'postgresql://' + DATABASE_URL[len('postgres://'):]
if DATABASE_URL.startswith('postgresql://') and '+psycopg2' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

# Security: CSRF protection with sensible time limit
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# File upload configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wmv'}
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/gif',
    'video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-ms-wmv'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'videos'), exist_ok=True)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access this page.'

# Security: Rate limiting for login attempts (per IP, in-memory)
login_attempts = {}

def get_client_ip():
    """Get client IP address. ProxyFix makes request.remote_addr trustworthy."""
    return request.remote_addr or 'unknown'

def is_login_rate_limited(ip_address, max_attempts=5, window_seconds=900):
    """Check if IP has exceeded the allowed number of recent failed attempts"""
    now = datetime.now(timezone.utc)
    attempts = login_attempts.get(ip_address, [])
    
    # Keep only attempts inside the window
    active = [t for t in attempts if (now - t).total_seconds() < window_seconds]
    login_attempts[ip_address] = active
    
    return len(active) >= max_attempts

def record_login_failure(ip_address):
    """Record one failed login attempt for an IP"""
    now = datetime.now(timezone.utc)
    login_attempts.setdefault(ip_address, []).append(now)

def clear_login_rate_limit(ip_address):
    """Reset failed-attempt counter after a successful login"""
    login_attempts.pop(ip_address, None)

def require_admin(f):
    """Decorator to require admin authorization"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning(f"Non-admin user {current_user.username} attempted to access admin page")
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    service_needed = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FeedbackSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String(500), nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False)
    source_id = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    api_source = db.Column(db.String(50), default='manual')
    article_id = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True)
    content = db.Column(db.Text, nullable=False)
    meta_description = db.Column(db.String(160))
    image_url = db.Column(db.String(500))
    image_alt = db.Column(db.String(200))
    video_url = db.Column(db.String(500))
    category = db.Column(db.String(100), default='general')
    post_type = db.Column(db.String(50), default='portfolio')
    price = db.Column(db.Float)
    currency = db.Column(db.String(10), default='NGN')
    negotiable = db.Column(db.Boolean, default=True)
    item_link = db.Column(db.String(500))
    published = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_canonical_url(self):
        """Get canonical URL for SEO (stable when SITE_URL is configured)."""
        path = url_for('post_detail', post_id=self.id)
        if SITE_URL:
            return f"{SITE_URL}{path}"
        return url_for('post_detail', post_id=self.id, _external=True)


# ---------------------------------------------------------------------------
# CRM (leads pipeline) - extension tables only.
#
# These are separate 1:1/1:N tables instead of new columns on contact_submission
# because the app runs `db.create_all()` on boot and does not use migrations:
# adding a column to an existing PostgreSQL table would silently NOT be applied
# and would crash every query that selects it. New tables are safe.
# ---------------------------------------------------------------------------
LEAD_STATUSES = {
    'new': {'label': 'New', 'colour': 'primary'},
    'contacted': {'label': 'Contacted', 'colour': 'info'},
    'quoted': {'label': 'Quoted', 'colour': 'warning'},
    'won': {'label': 'Won', 'colour': 'success'},
    'lost': {'label': 'Lost', 'colour': 'secondary'},
}


class LeadStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact_submission.id'),
                           unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='new', nullable=False)
    estimated_value = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LeadNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact_submission.id'),
                           nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PostFaq(db.Model):
    """FAQs for AI-generated (or manually edited) guide articles."""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, default=0)


class ContentTopic(db.Model):
    """Queue of topics the AI studio works through (drafts by default)."""
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(300), nullable=False)
    keyword = db.Column(db.String(200))
    category = db.Column(db.String(100), default='guides')
    tone = db.Column(db.String(50), default='practical')
    target_words = db.Column(db.Integer, default=1200)
    faq_count = db.Column(db.Integer, default=4)
    status = db.Column(db.String(20), default='queued', index=True)  # queued|generated|failed
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    error = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_at = db.Column(db.DateTime)


class AiGeneration(db.Model):
    """Audit log for every AI call (never stores the prompt or the API key)."""
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(300), nullable=False)
    provider = db.Column(db.String(30))
    model = db.Column(db.String(100))
    status = db.Column(db.String(20), default='success')  # success|error
    error = db.Column(db.String(500))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    duration_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

# Map allowed extensions to their expected MIME types (from magic bytes)
EXTENSION_MIME_MAP = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
    'avi': 'video/x-msvideo',
    'wmv': 'video/x-ms-wmv',
}

def validate_mime_type(file_stream):
    """Detect file MIME type from magic bytes (read more for video containers)"""
    try:
        file_stream.seek(0)
        magic_bytes = file_stream.read(32)
        file_stream.seek(0)
        
        if magic_bytes.startswith(b'\x89PNG'):
            return 'image/png'
        elif magic_bytes.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif magic_bytes.startswith(b'GIF8'):
            return 'image/gif'
        # ISO BMFF containers: MP4 / QuickTime (brand inside 'ftyp' box)
        elif b'ftyp' in magic_bytes[:16]:
            brand = magic_bytes[8:16]
            if b'qt' in brand:
                return 'video/quicktime'
            return 'video/mp4'
        # AVI: RIFF....AVI 
        elif magic_bytes.startswith(b'RIFF') and b'AVI ' in magic_bytes[:16]:
            return 'video/x-msvideo'
        # ASF (WMV): 30 26 B2 75 8E 66 CF 11 ...
        elif magic_bytes.startswith(bytes.fromhex('3026b2758e66cf11')):
            return 'video/x-ms-wmv'
        return None
    except Exception:
        return None

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return the file path. Rejects mismatched or unverifiable files."""
    if not file or not allowed_file(file.filename):
        logger.warning(f"Invalid file upload attempt: {file.filename if file else 'No file'}")
        return None
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    expected_mime = EXTENSION_MIME_MAP.get(ext)

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        return None
    
    detected_mime = validate_mime_type(file)
    # Security: the magic bytes MUST match the extension. Unknown content is rejected.
    if not detected_mime or detected_mime not in ALLOWED_MIME_TYPES or detected_mime != expected_mime:
        logger.warning(f"MIME mismatch for {file.filename}: detected={detected_mime}, expected={expected_mime}")
        return None
    
    try:
        filename = secure_filename(file.filename)
        filename = os.path.basename(filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        relative_path = f"/static/uploads/{subfolder}/{unique_filename}" if subfolder else f"/static/uploads/{unique_filename}"
        return relative_path.lstrip('/')
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return None

def sanitize_input(text, max_length=None):
    """Sanitize user input (strip null bytes, enforce max length)"""
    if not isinstance(text, str):
        return ''
    text = text.replace('\x00', '').strip()
    if max_length:
        text = text[:max_length]
    return text


# ---------------------------------------------------------------------------
# CRM / AI helpers
# ---------------------------------------------------------------------------
def _slugify(title):
    slug = title.lower().replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug).strip('-')
    return slug[:240] or 'article'


def unique_slug(title):
    """Slug that will not collide with an existing post (Post.slug is unique)."""
    base = _slugify(title)
    slug = base
    counter = 2
    while Post.query.filter_by(slug=slug).first() is not None:
        suffix = f'-{counter}'
        slug = base[:240 - len(suffix)] + suffix
        counter += 1
    return slug


def parse_faqs(raw):
    """Parse a JSON list of {"q": ..., "a": ...} into (question, answer) pairs.

    Raises ValueError with a user-safe message on malformed input.
    """
    raw = (raw or '').strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        raise ValueError('FAQs must be valid JSON.')
    if not isinstance(data, list):
        raise ValueError('FAQs must be a JSON list.')
    if len(data) > 10:
        raise ValueError('Add at most 10 FAQs.')
    pairs = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError('Each FAQ must be an object with "q" and "a".')
        question = sanitize_input(str(item.get('q', '')), 300)
        answer = sanitize_input(str(item.get('a', '')), 4000)
        if not question or not answer:
            raise ValueError('Each FAQ needs both a question and an answer.')
        pairs.append((question, answer))
    return pairs


def lead_status_map(contact_ids):
    """Return {contact_id: LeadStatus} for the given ids (empty-safe)."""
    if not contact_ids:
        return {}
    rows = LeadStatus.query.filter(LeadStatus.contact_id.in_(contact_ids)).all()
    return {row.contact_id: row for row in rows}


# Per-user AI call throttle (in-memory, per worker). Complements admin auth and
# keeps a stuck double-click from burning provider quota/cost.
ai_request_log = {}

def ai_is_rate_limited(user_id, max_calls=6, window_seconds=600):
    now = datetime.now(timezone.utc)
    calls = [t for t in ai_request_log.get(user_id, [])
             if (now - t).total_seconds() < window_seconds]
    ai_request_log[user_id] = calls
    return len(calls) >= max_calls


def record_ai_call(user_id):
    ai_request_log.setdefault(user_id, []).append(datetime.now(timezone.utc))


def _log_ai_failure(topic, error, started):
    settings = ai_service.get_settings()
    try:
        db.session.add(AiGeneration(
            topic=(topic or '')[:300],
            provider=settings['provider'],
            model=settings['model'],
            status='error',
            error=str(error)[:500],
            duration_ms=int((time.monotonic() - started) * 1000),
        ))
        db.session.commit()
    except Exception as exc:  # logging must never mask the original error
        db.session.rollback()
        logger.error(f"Could not record AI failure: {exc}")


def generate_ai_post(topic, keyword='', category='guides', tone='practical',
                     target_words=1200, faq_count=4, publish=False, author_id=None,
                     source_topic=None):
    """Generate one article and save it as a Post (+ FAQs + audit log).

    Returns the created Post. Raises ai_service.AiError with a safe message.
    """
    started = time.monotonic()
    settings = ai_service.get_settings()
    try:
        result = ai_service.generate_article(
            topic=topic, keyword=keyword, category=category, tone=tone,
            target_words=target_words, faq_count=faq_count,
        )
    except ai_service.AiError as exc:
        _log_ai_failure(topic, exc, started)
        if source_topic is not None:
            source_topic.status = 'failed'
            source_topic.error = str(exc)[:500]
            db.session.commit()
        raise

    try:
        post = Post(
            title=result['title'][:200],
            slug=unique_slug(result['title']),
            content=result['content'],
            meta_description=result['meta_description'][:160],
            image_alt=result['suggested_image_alt'] or result['title'][:200],
            category=sanitize_input(category, 100) or 'guides',
            post_type='article',
            published=bool(publish),
            author_id=author_id,
        )
        db.session.add(post)
        db.session.flush()  # assign post.id before creating FAQ rows

        for position, faq in enumerate(result.get('faqs') or []):
            db.session.add(PostFaq(
                post_id=post.id,
                question=faq['q'][:300],
                answer=faq['a'],
                position=position,
            ))

        db.session.add(AiGeneration(
            topic=(topic or '')[:300],
            provider=settings['provider'],
            model=settings['model'],
            status='success',
            post_id=post.id,
            duration_ms=int((time.monotonic() - started) * 1000),
        ))

        if source_topic is not None:
            source_topic.status = 'generated'
            source_topic.post_id = post.id
            source_topic.generated_at = datetime.utcnow()
            source_topic.error = None

        db.session.commit()
        return post
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Could not save AI post: {exc}")
        raise ai_service.AiError('The article was generated but could not be saved. Check the server logs.')

@app.template_filter('nl2br')
def nl2br_filter(value):
    """Escape content and convert newlines to <br> tags (safe alternative to |safe)"""
    # Escape first, then insert <br> on the plain string and re-mark as safe:
    # Markup.replace() would HTML-escape the '<br>' replacement.
    escaped = str(escape(value or ''))
    return Markup(escaped.replace('\r\n', '\n').replace('\n', '<br>\n'))


# Lightweight, whitelist-based markup for SEO articles. Everything is HTML-
# escaped first; only the small set of generated tags below is ever injected,
# so author-supplied HTML can never reach the page.
@app.template_filter('article_html')
def article_html_filter(value):
    """Render plain-text article content with proper H2/H3/list structure.

    Supported (line-prefix) conventions in the source text:
        '## '  -> <h2>, '### ' -> <h3>
        '- '   -> <li> (consecutive lines become one <ul>)
        blank line separates paragraphs
    All text is HTML-escaped; only the structural tags below are generated.
    """
    import html as _html
    import re as _re

    def _bold(text):
        """Convert **text** to <strong> (input already escaped)."""
        return _re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)

    raw_lines = str(value or '').replace('\r\n', '\n').split('\n')
    out = []
    list_buffer = []

    def flush_list():
        if list_buffer:
            items = ''.join(f'<li>{_bold(_html.escape(item))}</li>' for item in list_buffer)
            out.append(f'<ul>{items}</ul>')
            list_buffer.clear()

    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            flush_list()
            continue
        if stripped.startswith('### '):
            flush_list()
            out.append(f'<h3>{_html.escape(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            flush_list()
            out.append(f'<h2>{_html.escape(stripped[3:])}</h2>')
        elif stripped.startswith('- '):
            list_buffer.append(stripped[2:])
        else:
            flush_list()
            # Bold **text** -> <strong> after escaping
            out.append(f'<p>{_bold(_html.escape(stripped))}</p>')

    flush_list()
    return Markup(''.join(out))

# Security: per-request nonce so inline JSON-LD is allowed without 'unsafe-inline'
@app.before_request
def set_csp_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)

# Security: Add security headers to all responses
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    
    nonce = getattr(g, 'csp_nonce', '')
    csp = (
        "default-src 'self'; "
        f"script-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com https://www.googletagmanager.com 'nonce-{nonce}'; "
        "style-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com 'unsafe-inline'; "
        "img-src 'self' data: https: unsplash.com images.unsplash.com; "
        "font-src 'self' cdnjs.cloudflare.com; "
        "connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com https://*.analytics.google.com https://www.googletagmanager.com; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    if not app.config['DEBUG']:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Don't cache pages that include user data or admin functionality
    if request.endpoint and (request.endpoint.startswith('admin') or request.endpoint in ('submit_contact', 'submit_feedback', 'admin_login')):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    
    return response

# Security: Error handlers
@app.errorhandler(400)
def bad_request(error):
    return render_template('error.html', code=400, message='Bad Request'), 400

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', code=403, message='Forbidden'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', code=404, message='Page Not Found'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', code=500, message='Internal Server Error'), 500

# Routes
@app.route('/')
def home():
    portfolio_posts = Post.query.filter_by(post_type='portfolio', published=True).order_by(Post.created_at.desc()).limit(6).all()
    sale_posts = Post.query.filter_by(post_type='sale', published=True).order_by(Post.created_at.desc()).limit(6).all()
    # SEO guide articles (content roadmap) - newest 3 for the homepage section
    article_posts = Post.query.filter_by(post_type='article', published=True).order_by(Post.created_at.desc()).limit(3).all()

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    per_page = 6
    news_pagination = NewsArticle.query.order_by(NewsArticle.pub_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    news_articles = news_pagination.items

    return render_template('home.html',
                         portfolio_posts=portfolio_posts,
                         sale_posts=sale_posts,
                         article_posts=article_posts,
                         news_articles=news_articles,
                         news_pagination=news_pagination)

@app.route('/contact', methods=['POST'])
def submit_contact():
    # Honeypot: bots fill hidden fields - silently ignore them
    if request.form.get('company_website'):
        logger.info("Contact form honeypot triggered - submission ignored")
        return redirect(url_for('home') + '#contact')

    name = sanitize_input(request.form.get('name', ''), 100)
    email = sanitize_input(request.form.get('email', ''), 150)
    phone = sanitize_input(request.form.get('phone', ''), 20)
    service_needed = sanitize_input(request.form.get('service_needed', ''), 200)
    message = sanitize_input(request.form.get('message', ''), 2000)

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        flash('Please provide a valid email address.', 'error')
        return redirect(url_for('home') + '#contact')

    if not all([name, email, message]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('home') + '#contact')

    try:
        contact = ContactSubmission(
            name=name,
            email=email,
            phone=phone,
            service_needed=service_needed,
            message=message
        )

        db.session.add(contact)
        db.session.commit()

        flash('Thank you for contacting us. We\'ll get back to you within 2 hours.', 'success')
    except Exception as e:
        logger.error(f"Error submitting contact form: {e}")
        db.session.rollback()
        flash('An error occurred. Please try again later.', 'error')
    
    return redirect(url_for('home') + '#contact')

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    # Honeypot: bots fill hidden fields - silently ignore them
    if request.form.get('company_website'):
        logger.info("Feedback form honeypot triggered - submission ignored")
        return redirect(url_for('home') + '#feedback')

    name = sanitize_input(request.form.get('name', ''), 100)
    email = sanitize_input(request.form.get('email', ''), 150)
    subject = sanitize_input(request.form.get('subject', ''), 200)
    message = sanitize_input(request.form.get('message', ''), 2000)

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        flash('Please provide a valid email address.', 'error')
        return redirect(url_for('home') + '#feedback')

    if not all([name, email, subject, message]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('home') + '#feedback')

    try:
        feedback = FeedbackSubmission(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        db.session.add(feedback)
        db.session.commit()

        flash('Thank you for your feedback! We appreciate your input.', 'success')
    except Exception as e:
        logger.error(f"Error submitting feedback form: {e}")
        db.session.rollback()
        flash('An error occurred. Please try again later.', 'error')
    
    return redirect(url_for('home') + '#feedback')

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id, published=True).first_or_404()
    # Related posts of the same type (excludes the current post)
    related = (Post.query.filter(Post.post_type == post.post_type,
                                 Post.published.is_(True),
                                 Post.id != post.id)
               .order_by(Post.created_at.desc()).limit(3).all())
    # FAQs: DB-backed (AI-generated or admin-edited) first, then the seeded
    # articles' FAQs looked up by slug (kept for backwards compatibility).
    db_faqs = (PostFaq.query.filter_by(post_id=post.id)
               .order_by(PostFaq.position, PostFaq.id).all())
    if db_faqs:
        faqs = [{'q': faq.question, 'a': faq.answer} for faq in db_faqs]
    else:
        import seed_data
        faqs_by_slug = {a['slug']: a['faqs'] for a in seed_data.ARTICLES if a.get('faqs')}
        faqs = faqs_by_slug.get(post.slug, [])
    return render_template('post_detail.html', post=post, related_posts=related,
                           faqs=faqs)

@app.route('/marketplace')
def marketplace():
    marketplace_items = Post.query.filter_by(post_type='sale', published=True).order_by(Post.created_at.desc()).all()
    return render_template('marketplace.html', marketplace_items=marketplace_items)

@app.route('/guides')
def guides():
    """SEO: indexable hub page for all guide articles (internal linking)."""
    articles = (Post.query.filter_by(post_type='article', published=True)
                .order_by(Post.created_at.desc()).all())
    return render_template('guides.html', articles=articles)

@app.route('/robots.txt')
def robots():
    """SEO: Robots.txt for search engine crawling (domain-aware)"""
    base_url = SITE_URL or request.url_root.rstrip('/')
    response = make_response(f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /admin/*
Disallow: /static/uploads/
Disallow: /feedback
Allow: /static/
Allow: /post/
Allow: /guides
Allow: /marketplace

Sitemap: {base_url}/sitemap.xml
""")
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/llms.txt')
def llms_txt():
    """GEO: concise site summary for AI search engines and LLM crawlers."""
    base_url = SITE_URL or request.url_root.rstrip('/')
    articles = (Post.query.filter_by(post_type='article', published=True)
                .order_by(Post.created_at.desc()).limit(20).all())
    lines = [
        '# Moscool Technical Services',
        '',
        '> AC repair, refrigeration, solar and inverter installation, and electrical services',
        '> for homes and businesses in Lagos Mainland and Ogun State, Nigeria.',
        '',
        '## Services',
        '- Air conditioning: installation, servicing, repair and duct cleaning',
        '- Refrigeration: freezers, chillers, cold rooms and display cases',
        '- Solar: hybrid/off-grid system design, installation and maintenance',
        '- Inverters: installation, battery replacement and troubleshooting',
        '- Electrical: wiring, panels, safety inspections and upgrades',
        '',
        '## Service areas',
        'Lagos Mainland (Ikeja, Yaba, Surulere, Maryland, Gbagada, Ogba) and',
        'Ogun State (Magboro, Mowe, Ibafo).',
        '',
        '## Contact',
        f'- Address: {BUSINESS_ADDRESS}, {BUSINESS_LOCALITY}, {BUSINESS_REGION}, Nigeria',
        f'- Phone / WhatsApp: {BUSINESS_PHONE}',
        f'- Email: {BUSINESS_EMAIL}',
        f'- Website: {base_url}/',
        '- Hours: Mon-Fri 08:00-18:00; 24/7 emergency line',
        '',
        '## Key pages',
        f'- [Home]({base_url}/)',
        f'- [Guides and tips]({base_url}/guides)',
        f'- [Marketplace]({base_url}/marketplace)',
    ]
    if articles:
        lines += ['', '## Guides']
        lines += [f'- [{a.title}]({a.get_canonical_url()})' for a in articles]
    response = make_response('\n'.join(lines) + '\n')
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

@app.route('/sitemap.xml')
def sitemap():
    """SEO: XML sitemap for search engines (domain-aware)"""
    try:
        posts = Post.query.filter_by(published=True).all()
        base_url = SITE_URL or request.url_root.rstrip('/')

        # Home lastmod reflects the newest published content instead of today's
        # date, which avoids "lastmod changes on every request" trust issues.
        latest = max((p.updated_at or p.created_at) for p in posts) if posts else datetime.utcnow()
        lastmod = latest.strftime('%Y-%m-%d')

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for loc, priority in (('/', '1.0'), ('/marketplace', '0.8'), ('/guides', '0.8')):
            xml += '  <url>\n'
            xml += f'    <loc>{base_url}{loc}</loc>\n'
            xml += f'    <lastmod>{lastmod}</lastmod>\n'
            xml += f'    <priority>{priority}</priority>\n'
            xml += '  </url>\n'

        for post in posts:
            # SEO articles are discovery content - slightly higher priority
            priority = '0.8' if post.post_type == 'article' else '0.7'
            xml += '  <url>\n'
            xml += f'    <loc>{post.get_canonical_url()}</loc>\n'
            xml += f'    <lastmod>{post.updated_at.strftime("%Y-%m-%d")}</lastmod>\n'
            xml += f'    <priority>{priority}</priority>\n'
            xml += '  </url>\n'
        
        xml += '</urlset>\n'
        
        response = make_response(xml)
        response.headers['Content-Type'] = 'application/xml'
        return response
    except Exception as e:
        logger.error(f"Error generating sitemap: {e}")
        return '', 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        client_ip = get_client_ip()
        
        if is_login_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            flash('Too many failed login attempts. Please try again in 15 minutes.', 'error')
            return render_template('admin_login.html', 429)
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('admin_login.html', 400)

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password) and user.is_admin:
            clear_login_rate_limit(client_ip)
            # Ensure the session id is regenerated after privilege change (fixation protection)
            session.clear()
            login_user(user, remember=False, force=True)
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '' or not next_page.startswith('/'):
                next_page = url_for('admin_dashboard')
            return redirect(next_page)

        record_login_failure(client_ip)
        flash('Invalid username or password.', 'error')
        logger.info(f"Failed login attempt from IP: {client_ip}")

    return render_template('admin_login.html')

@app.route('/admin/logout', methods=['POST'])
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
@require_admin
def admin_dashboard():
    contact_count = ContactSubmission.query.count()
    feedback_count = FeedbackSubmission.query.count()
    posts_count = Post.query.count()

    status_rows = LeadStatus.query.all()
    status_by_contact = {row.contact_id: row.status for row in status_rows}
    pipeline_counts = {key: 0 for key in LEAD_STATUSES}
    for row in status_rows:
        if row.status in pipeline_counts:
            pipeline_counts[row.status] += 1
    # Contacts without an explicit status are "new".
    pipeline_counts['new'] += max(0, contact_count - len(status_rows))
    pipeline_value = sum(
        row.estimated_value or 0 for row in status_rows
        if row.status in ('contacted', 'quoted')
    )

    recent_contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).limit(6).all()
    recent_feedbacks = FeedbackSubmission.query.order_by(FeedbackSubmission.created_at.desc()).limit(5).all()
    recent_leads = [
        {'contact': c, 'status': status_by_contact.get(c.id, 'new')}
        for c in recent_contacts
    ]

    return render_template('admin_dashboard.html',
                         contact_count=contact_count,
                         feedback_count=feedback_count,
                         posts_count=posts_count,
                         pipeline_counts=pipeline_counts,
                         pipeline_value=pipeline_value,
                         statuses=LEAD_STATUSES,
                         recent_leads=recent_leads,
                         recent_contacts=recent_contacts,
                         recent_feedbacks=recent_feedbacks,
                         ai_configured=ai_service.is_configured(),
                         ai_generated=AiGeneration.query.filter_by(status='success').count(),
                         queued_topics=ContentTopic.query.filter_by(status='queued').count())


# ---------------------------------------------------------------------------
# CRM: leads pipeline
# ---------------------------------------------------------------------------
@app.route('/admin/leads')
@require_admin
def admin_leads():
    contacts = (ContactSubmission.query
                .order_by(ContactSubmission.created_at.desc()).limit(300).all())
    statuses = lead_status_map([c.id for c in contacts])
    note_counts = {}
    if contacts:
        note_counts = dict(
            db.session.query(LeadNote.contact_id, func.count(LeadNote.id))
            .filter(LeadNote.contact_id.in_([c.id for c in contacts]))
            .group_by(LeadNote.contact_id).all()
        )

    items = []
    for contact in contacts:
        row = statuses.get(contact.id)
        items.append({
            'contact': contact,
            'status': row.status if row and row.status in LEAD_STATUSES else 'new',
            'value': row.estimated_value if row else None,
            'notes': note_counts.get(contact.id, 0),
        })
    columns = {key: [i for i in items if i['status'] == key] for key in LEAD_STATUSES}

    return render_template('admin_leads.html', columns=columns, statuses=LEAD_STATUSES,
                           total=len(items), pipeline_value=sum(i['value'] or 0 for i in items
                                                              if i['status'] in ('contacted', 'quoted')))


@app.route('/admin/leads/<int:contact_id>')
@require_admin
def admin_lead_detail(contact_id):
    contact = ContactSubmission.query.get_or_404(contact_id)
    lead_status = LeadStatus.query.filter_by(contact_id=contact_id).first()
    notes = (LeadNote.query.filter_by(contact_id=contact_id)
             .order_by(LeadNote.created_at.desc()).all())
    return render_template('admin_lead_detail.html', contact=contact, lead_status=lead_status,
                           notes=notes, statuses=LEAD_STATUSES,
                           wa_number=re.sub(r'\D', '', contact.phone or ''))


@app.route('/admin/leads/<int:contact_id>/status', methods=['POST'])
@require_admin
def admin_lead_status(contact_id):
    ContactSubmission.query.get_or_404(contact_id)
    status = request.form.get('status', 'new')
    if status not in LEAD_STATUSES:
        flash('Choose a valid pipeline stage.', 'error')
        return redirect(url_for('admin_lead_detail', contact_id=contact_id))

    raw_value = (request.form.get('estimated_value') or '').strip()
    value = None
    if raw_value:
        try:
            value = float(raw_value)
            if value < 0:
                raise ValueError
        except (TypeError, ValueError):
            flash('Estimated value must be a positive number.', 'error')
            return redirect(url_for('admin_lead_detail', contact_id=contact_id))

    row = LeadStatus.query.filter_by(contact_id=contact_id).first()
    if row is None:
        row = LeadStatus(contact_id=contact_id)
        db.session.add(row)
    row.status = status
    row.estimated_value = value
    row.updated_at = datetime.utcnow()
    try:
        db.session.commit()
        flash('Lead updated.', 'success')
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Could not update lead {contact_id}: {exc}")
        flash('Could not update the lead. Please try again.', 'error')

    next_url = request.form.get('next', '')
    if not next_url.startswith('/admin'):
        next_url = url_for('admin_lead_detail', contact_id=contact_id)
    return redirect(next_url)


@app.route('/admin/leads/<int:contact_id>/notes', methods=['POST'])
@require_admin
def admin_lead_note(contact_id):
    ContactSubmission.query.get_or_404(contact_id)
    body = sanitize_input(request.form.get('body', ''), 2000)
    if not body:
        flash('Write a note before saving.', 'error')
    else:
        try:
            db.session.add(LeadNote(contact_id=contact_id, body=body))
            db.session.commit()
            flash('Note added.', 'success')
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Could not add lead note: {exc}")
            flash('Could not save the note. Please try again.', 'error')
    return redirect(url_for('admin_lead_detail', contact_id=contact_id))


# ---------------------------------------------------------------------------
# AI content studio
# ---------------------------------------------------------------------------
@app.route('/admin/ai')
@require_admin
def admin_ai():
    settings = ai_service.get_settings()
    generations = (AiGeneration.query.order_by(AiGeneration.created_at.desc())
                   .limit(10).all())
    topics = (ContentTopic.query.order_by(ContentTopic.created_at.desc()).limit(25).all())
    return render_template(
        'admin_ai.html',
        configured=ai_service.is_configured(),
        provider=settings['provider'],
        model=settings['model'],
        auto_publish=AI_AUTO_PUBLISH,
        generations=generations,
        topics=topics,
        queued=ContentTopic.query.filter_by(status='queued').count(),
        rate_limited=ai_is_rate_limited(current_user.id),
    )


@app.route('/admin/ai/generate', methods=['POST'])
@require_admin
def admin_ai_generate():
    topic = sanitize_input(request.form.get('topic', ''), 300)
    keyword = sanitize_input(request.form.get('keyword', ''), 200)
    category = sanitize_input(request.form.get('category', 'guides'), 100) or 'guides'
    tone = sanitize_input(request.form.get('tone', 'practical'), 50) or 'practical'
    try:
        target_words = int(request.form.get('target_words') or 1200)
        faq_count = int(request.form.get('faq_count') or 0)
    except (TypeError, ValueError):
        flash('Word count and FAQ count must be numbers.', 'error')
        return redirect(url_for('admin_ai'))
    target_words = max(600, min(2000, target_words))
    faq_count = max(0, min(6, faq_count))
    publish = request.form.get('publish') == 'on'

    if not topic:
        flash('Enter a topic first.', 'error')
        return redirect(url_for('admin_ai'))
    if not ai_service.is_configured():
        flash('AI is not configured. Set AI_API_KEY in the environment.', 'error')
        return redirect(url_for('admin_ai'))
    if ai_is_rate_limited(current_user.id):
        flash('Too many AI requests. Wait a few minutes before generating again.', 'error')
        return redirect(url_for('admin_ai'))

    record_ai_call(current_user.id)
    try:
        post = generate_ai_post(topic=topic, keyword=keyword, category=category, tone=tone,
                                target_words=target_words, faq_count=faq_count,
                                publish=publish, author_id=current_user.id)
    except ai_service.AiError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin_ai'))
    except Exception as exc:  # never leak provider internals to the UI
        logger.exception(f"Unexpected AI generation failure: {exc}")
        flash('Generation failed unexpectedly. Check the server logs.', 'error')
        return redirect(url_for('admin_ai'))

    state = 'published' if post.published else 'saved as a draft'
    flash(f'Article {state}: {post.title}', 'success')
    return redirect(url_for('admin_edit_post', post_id=post.id))


@app.route('/admin/ai/topics', methods=['POST'])
@require_admin
def admin_ai_topic_add():
    topic = sanitize_input(request.form.get('topic', ''), 300)
    if not topic:
        flash('Enter a topic to queue.', 'error')
        return redirect(url_for('admin_ai'))
    try:
        target_words = max(600, min(2000, int(request.form.get('target_words') or 1200)))
        faq_count = max(0, min(6, int(request.form.get('faq_count') or 4)))
    except (TypeError, ValueError):
        target_words, faq_count = 1200, 4

    db.session.add(ContentTopic(
        topic=topic,
        keyword=sanitize_input(request.form.get('keyword', ''), 200),
        category=sanitize_input(request.form.get('category', 'guides'), 100) or 'guides',
        tone=sanitize_input(request.form.get('tone', 'practical'), 50) or 'practical',
        target_words=target_words,
        faq_count=faq_count,
    ))
    db.session.commit()
    flash('Topic added to the queue.', 'success')
    return redirect(url_for('admin_ai'))


@app.route('/admin/ai/topics/<int:topic_id>/generate', methods=['POST'])
@require_admin
def admin_ai_topic_generate(topic_id):
    queued_topic = ContentTopic.query.get_or_404(topic_id)
    if not ai_service.is_configured():
        flash('AI is not configured. Set AI_API_KEY in the environment.', 'error')
        return redirect(url_for('admin_ai'))
    if ai_is_rate_limited(current_user.id):
        flash('Too many AI requests. Wait a few minutes before generating again.', 'error')
        return redirect(url_for('admin_ai'))

    record_ai_call(current_user.id)
    try:
        post = generate_ai_post(
            topic=queued_topic.topic, keyword=queued_topic.keyword or '',
            category=queued_topic.category, tone=queued_topic.tone,
            target_words=queued_topic.target_words or 1200,
            faq_count=queued_topic.faq_count or 0,
            publish=AI_AUTO_PUBLISH, author_id=current_user.id,
            source_topic=queued_topic,
        )
    except ai_service.AiError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin_ai'))
    except Exception as exc:
        logger.exception(f"Unexpected AI queue failure: {exc}")
        flash('Generation failed unexpectedly. Check the server logs.', 'error')
        return redirect(url_for('admin_ai'))

    flash(f"Draft created: {post.title}", 'success')
    return redirect(url_for('admin_edit_post', post_id=post.id))


@app.route('/admin/ai/topics/<int:topic_id>/delete', methods=['POST'])
@require_admin
def admin_ai_topic_delete(topic_id):
    queued_topic = ContentTopic.query.get_or_404(topic_id)
    db.session.delete(queued_topic)
    db.session.commit()
    flash('Topic removed.', 'success')
    return redirect(url_for('admin_ai'))


@app.route('/admin/ai/generate-queued', methods=['POST'])
@require_admin
def admin_ai_generate_queued():
    queued_topic = (ContentTopic.query.filter_by(status='queued')
                    .order_by(ContentTopic.created_at.asc()).first())
    if queued_topic is None:
        flash('The topic queue is empty.', 'info')
        return redirect(url_for('admin_ai'))
    return admin_ai_topic_generate(queued_topic.id)


@app.route('/admin/posts')
@require_admin
def admin_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin_posts.html', posts=posts)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
@require_admin
def admin_create_post():
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title', ''), 200)
        content = sanitize_input(request.form.get('content', ''), 20000)
        image_url = sanitize_input(request.form.get('image_url', ''), 500)
        image_alt = sanitize_input(request.form.get('image_alt', ''), 200)
        video_url = sanitize_input(request.form.get('video_url', ''), 500)
        category = sanitize_input(request.form.get('category', 'general'), 100)
        post_type = sanitize_input(request.form.get('post_type', 'portfolio'), 50)
        meta_description = sanitize_input(request.form.get('meta_description', ''), 160)
        price = request.form.get('price', '')
        currency = sanitize_input(request.form.get('currency', 'NGN'), 10)
        negotiable = request.form.get('negotiable') == 'on'
        item_link = sanitize_input(request.form.get('item_link', ''), 500)
        published = request.form.get('published') == 'on'

        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('admin_create_post'))

        uploaded_image_url = None
        uploaded_video_url = None

        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file and image_file.filename:
                uploaded_image_url = save_uploaded_file(image_file, 'images')

        if 'video_file' in request.files:
            video_file = request.files['video_file']
            if video_file and video_file.filename:
                uploaded_video_url = save_uploaded_file(video_file, 'videos')

        final_image_url = image_url or uploaded_image_url
        final_video_url = video_url or uploaded_video_url

        try:
            post = Post(
                title=title,
                slug=unique_slug(title),
                content=content,
                # [:160] guards the VARCHAR(160) column - PostgreSQL rejects
                # longer values with StringDataRightTruncation
                meta_description=(meta_description or content)[:160],
                image_url=final_image_url,
                image_alt=image_alt or title,
                video_url=final_video_url,
                category=category,
                post_type=post_type,
                price=float(price) if price else None,
                currency=currency,
                negotiable=negotiable,
                item_link=item_link if item_link else None,
                published=published,
                author_id=current_user.id
            )

            db.session.add(post)
            db.session.commit()

            flash('Post created successfully!', 'success')
            return redirect(url_for('admin_posts'))
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('admin_create_post'))

    return render_template('admin_post_form.html', post=None, post_faqs=[])

@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@require_admin
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        # Validate FAQs before mutating anything, so a malformed JSON blob
        # cannot be quietly dropped or saved half-applied.
        faq_pairs = []
        if request.form.get('faqs_present') == '1':
            try:
                faq_pairs = parse_faqs(request.form.get('faqs_json', ''))
            except ValueError as exc:
                flash(str(exc), 'error')
                return redirect(url_for('admin_edit_post', post_id=post.id))

        post.title = sanitize_input(request.form.get('title', ''), 200)
        post.content = sanitize_input(request.form.get('content', ''), 20000)
        post.meta_description = sanitize_input(request.form.get('meta_description', ''), 160)[:160]
        post.image_alt = sanitize_input(request.form.get('image_alt', ''), 200)

        uploaded_image_url = None
        uploaded_video_url = None

        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file and image_file.filename:
                uploaded_image_url = save_uploaded_file(image_file, 'images')

        if 'video_file' in request.files:
            video_file = request.files['video_file']
            if video_file and video_file.filename:
                uploaded_video_url = save_uploaded_file(video_file, 'videos')

        image_url = sanitize_input(request.form.get('image_url', ''), 500)
        video_url = sanitize_input(request.form.get('video_url', ''), 500)

        post.image_url = image_url or uploaded_image_url or post.image_url
        post.video_url = video_url or uploaded_video_url or post.video_url
        post.category = sanitize_input(request.form.get('category', 'general'), 100)
        post.post_type = sanitize_input(request.form.get('post_type', 'portfolio'), 50)
        
        try:
            post.price = float(request.form.get('price')) if request.form.get('price') else None
        except (ValueError, TypeError):
            post.price = None
        
        post.currency = sanitize_input(request.form.get('currency', 'NGN'), 10)
        post.negotiable = request.form.get('negotiable') == 'on'
        post.item_link = sanitize_input(request.form.get('item_link', ''), 500) if request.form.get('item_link') else None
        post.published = request.form.get('published') == 'on'
        post.updated_at = datetime.utcnow()

        if request.form.get('faqs_present') == '1':
            PostFaq.query.filter_by(post_id=post.id).delete()
            for position, (question, answer) in enumerate(faq_pairs):
                db.session.add(PostFaq(post_id=post.id, question=question,
                                       answer=answer, position=position))

        try:
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('admin_posts'))
        except Exception as e:
            logger.error(f"Error updating post: {e}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')

    post_faqs = (PostFaq.query.filter_by(post_id=post.id)
                 .order_by(PostFaq.position, PostFaq.id).all())
    return render_template('admin_post_form.html', post=post, post_faqs=post_faqs)

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@require_admin
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    try:
        # These tables have FKs to post.id and no cascade configured (they are
        # created via db.create_all, not migrations). Clear the references first
        # or PostgreSQL blocks the delete.
        PostFaq.query.filter_by(post_id=post.id).delete()
        AiGeneration.query.filter_by(post_id=post.id).update(
            {'post_id': None}, synchronize_session=False)
        ContentTopic.query.filter_by(post_id=post.id).update(
            {'post_id': None, 'status': 'queued'}, synchronize_session=False)
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('admin_posts'))

@app.route('/admin/contacts')
@require_admin
def admin_contacts():
    contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    return render_template('admin_contacts.html', contacts=contacts)

@app.route('/admin/feedbacks')
@require_admin
def admin_feedbacks():
    feedbacks = FeedbackSubmission.query.order_by(FeedbackSubmission.created_at.desc()).all()
    return render_template('admin_feedbacks.html', feedbacks=feedbacks)

@app.route('/admin/news')
@require_admin
def admin_news():
    news_articles = NewsArticle.query.order_by(NewsArticle.pub_date.desc()).all()
    return render_template('admin_news.html', news_articles=news_articles)

@app.route('/admin/news/new', methods=['GET', 'POST'])
@require_admin
def admin_create_news():
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title', ''), 300)
        description = sanitize_input(request.form.get('description', ''), 2000)
        link = sanitize_input(request.form.get('link', ''), 500)
        source_id = sanitize_input(request.form.get('source_id', ''), 100)
        image_url = sanitize_input(request.form.get('image_url', ''), 500)

        if not title or not link:
            flash('Title and link are required.', 'error')
            return redirect(url_for('admin_create_news'))

        pub_date_str = request.form.get('pub_date')
        if pub_date_str:
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('T', ' '))
            except:
                pub_date = datetime.utcnow()
        else:
            pub_date = datetime.utcnow()

        try:
            news_article = NewsArticle(
                title=title,
                description=description,
                link=link,
                pub_date=pub_date,
                source_id=source_id,
                image_url=image_url if image_url else None
            )

            db.session.add(news_article)
            db.session.commit()

            flash('News article added successfully!', 'success')
            return redirect(url_for('admin_news'))
        except Exception as e:
            logger.error(f"Error creating news article: {e}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')

    return render_template('admin_news_form.html', article=None)

@app.route('/admin/news/<int:article_id>/edit', methods=['GET', 'POST'])
@require_admin
def admin_edit_news(article_id):
    article = NewsArticle.query.get_or_404(article_id)

    if request.method == 'POST':
        article.title = sanitize_input(request.form.get('title', ''), 300)
        article.description = sanitize_input(request.form.get('description', ''), 2000)
        article.link = sanitize_input(request.form.get('link', ''), 500)
        article.source_id = sanitize_input(request.form.get('source_id', ''), 100)
        article.image_url = sanitize_input(request.form.get('image_url', ''), 500) if request.form.get('image_url') else None

        pub_date_str = request.form.get('pub_date')
        if pub_date_str:
            try:
                article.pub_date = datetime.fromisoformat(pub_date_str.replace('T', ' '))
            except:
                pass

        try:
            db.session.commit()
            flash('News article updated successfully!', 'success')
            return redirect(url_for('admin_news'))
        except Exception as e:
            logger.error(f"Error updating news article: {e}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')

    return render_template('admin_news_form.html', article=article)

@app.route('/admin/news/<int:article_id>/delete', methods=['POST'])
@require_admin
def admin_delete_news(article_id):
    article = NewsArticle.query.get_or_404(article_id)
    try:
        db.session.delete(article)
        db.session.commit()
        flash('News article deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting news article: {e}")
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('admin_news'))

# News API Configuration
NEWSDATA_API_KEY = os.getenv('NEWSDATA_API_KEY', '')
NEWSDATA_BASE_URL = 'https://newsdata.io/api/1/latest'
NEWS_FETCH_TIMEOUT = 30

# Only fetch news about the services Moscool actually offers. The query uses
# boolean OR so any one of these topics matches; the client-side filter below
# then drops articles where none of the topics appear in title/description
# (protects against loose API keyword matches).
NEWS_KEYWORDS = (
    'air conditioning', 'air conditioner', 'refrigerator', 'refrigeration',
    'hvac', 'solar panel', 'solar installation', 'inverter', 'electrical wiring',
)
NEWS_QUERY = ' OR '.join(f'"{keyword}"' for keyword in NEWS_KEYWORDS)

def _article_is_relevant(article_data):
    """Check that a fetched article is actually about one of our service topics."""
    text = ' '.join(filter(None, (
        str(article_data.get('title') or ''),
        str(article_data.get('description') or ''),
    ))).lower()
    return any(keyword in text for keyword in NEWS_KEYWORDS)

def _request_relevant_news(base_params, country=None):
    """Request news from the API and return only topic-relevant articles."""
    params = dict(base_params)
    if country:
        params['country'] = country
    try:
        response = requests.get(NEWSDATA_BASE_URL, params=params, timeout=NEWS_FETCH_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        if country:
            logger.warning(f"Network error fetching Nigerian news, will try global: {str(e)}")
        else:
            logger.warning(f"Network error fetching news from API: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error parsing news API response: {str(e)}")
        return []

    if data.get('status') != 'success':
        logger.warning(f"API returned non-success status: {data.get('status')}")
        return []

    results = data.get('results') or []
    return [a for a in results if isinstance(a, dict) and _article_is_relevant(a)]

def fetch_news_from_api():
    """Fetch AC/refrigeration/solar/inverter news from newsdata.io API.

    Prefers Nigerian news (local relevance) and falls back to global
    topic news when nothing relevant was published in Nigeria.
    """
    try:
        if not NEWSDATA_API_KEY:
            logger.info("NewsData.io API key not configured")
            return 0

        base_params = {
            'apikey': NEWSDATA_API_KEY,
            'q': NEWS_QUERY,
            'language': 'en',
            'size': 10,
            'removeduplicate': 1
        }

        relevant_results = _request_relevant_news(base_params, country='ng')
        if not relevant_results:
            relevant_results = _request_relevant_news(base_params)

        if not relevant_results:
            logger.info("No relevant news articles found in API response")
            return 0

        articles_added = 0

        for article_data in relevant_results:
            if not isinstance(article_data, dict):
                continue

            article_id = article_data.get('article_id') or article_data.get('link')
            title = article_data.get('title')

            if not title:
                continue

            existing = NewsArticle.query.filter(
                (NewsArticle.article_id == article_id) |
                (NewsArticle.title == title)
            ).first()

            if existing:
                continue

            pub_date = datetime.utcnow()
            if article_data.get('pubDate'):
                try:
                    pub_date = date_parser.parse(article_data['pubDate'])
                except Exception:
                    pass

            link = article_data.get('link', '')
            if not link:
                continue

            description = ''
            if 'description' in article_data and article_data['description'] is not None:
                description = str(article_data['description'])[:1000]

            try:
                article = NewsArticle(
                    title=title[:300],
                    description=description,
                    link=link,
                    pub_date=pub_date,
                    source_id=article_data.get('source_id', 'NewsData.io'),
                    image_url=article_data.get('image_url'),
                    api_source='newsdata',
                    article_id=article_id
                )
                db.session.add(article)
                articles_added += 1
            except Exception as e:
                logger.error(f"Error adding article: {e}")
                continue

        db.session.commit()
        logger.info(f"Added {articles_added} new articles from NewsData.io API")
        return articles_added

    except requests.exceptions.RequestException as e:
        logger.warning(f"Network error fetching news from API: {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"Error fetching news from API: {str(e)}")
        return 0

def cleanup_old_news():
    """Delete news articles older than 30 days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_articles = NewsArticle.query.filter(NewsArticle.created_at < cutoff_date).all()

        deleted_count = 0
        for article in old_articles:
            db.session.delete(article)
            deleted_count += 1

        db.session.commit()
        logger.info(f"Cleaned up {deleted_count} old news articles")
        return deleted_count

    except Exception as e:
        logger.error(f"Error cleaning up old news: {str(e)}")
        return 0

@app.route('/admin/fetch-news-api', methods=['POST'])
@require_admin
def admin_fetch_news_api():
    """Manually trigger news fetching from API"""
    try:
        if not NEWSDATA_API_KEY:
            flash('NewsData.io API key not configured. Please set NEWSDATA_API_KEY environment variable.', 'error')
            return redirect(url_for('admin_news'))

        articles_added = fetch_news_from_api()

        if articles_added > 0:
            flash(f'Successfully fetched {articles_added} new articles from NewsData.io!', 'success')
        elif articles_added == 0:
            flash('No new articles found or API limit reached.', 'info')

    except Exception as e:
        logger.error(f"Error in admin_fetch_news_api: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'error')

    return redirect(url_for('admin_news'))

@app.route('/admin/cleanup-news', methods=['POST'])
@require_admin
def admin_cleanup_news():
    """Manually trigger cleanup of old news"""
    deleted_count = cleanup_old_news()

    if deleted_count > 0:
        flash(f'Successfully deleted {deleted_count} old news articles.', 'success')
    else:
        flash('No old articles to clean up.', 'info')

    return redirect(url_for('admin_news'))

@app.route('/admin/generate-news', methods=['POST'])
@require_admin
def admin_generate_news():
    """Insert a small set of sample news articles (for demo/testing)."""
    sample_articles = [
        {
            'title': 'Top 5 HVAC Maintenance Tips for the Rainy Season',
            'description': 'Keep your air conditioning units running efficiently with these essential maintenance tips for humid climates.',
            'source_id': 'Moscool Tech',
            'category': 'hvac',
        },
        {
            'title': 'Why Regular Refrigerator Servicing Saves You Money',
            'description': 'Learn how routine refrigeration maintenance prevents costly breakdowns and extends equipment lifespan.',
            'source_id': 'Moscool Tech',
            'category': 'refrigeration',
        },
        {
            'title': 'Solar Power: A Smart Investment for Nigerian Homes',
            'description': 'With rising energy costs, solar and inverter systems are becoming the preferred backup solution for households.',
            'source_id': 'Moscool Tech',
            'category': 'solar',
        },
    ]

    added = 0
    try:
        for item in sample_articles:
            exists = NewsArticle.query.filter_by(title=item['title']).first()
            if exists:
                continue
            article = NewsArticle(
                title=item['title'],
                description=item['description'],
                link='https://moscooltech.com/',
                pub_date=datetime.utcnow(),
                source_id=item['source_id'],
                api_source='manual',
            )
            db.session.add(article)
            added += 1
        db.session.commit()
        if added:
            flash(f'Added {added} sample news article(s).', 'success')
        else:
            flash('Sample articles already exist.', 'info')
    except Exception as e:
        logger.error(f"Error generating sample news: {e}")
        db.session.rollback()
        flash('An error occurred while generating sample news.', 'error')

    return redirect(url_for('admin_news'))

# ---------------------------------------------------------------------------
# Database / admin bootstrap - must run when the module is loaded by any
# WSGI server (e.g. gunicorn on Render), not only under `python app.py`.
# ---------------------------------------------------------------------------
def init_database():
    """Create tables and ensure the default admin account exists."""
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin_password = os.getenv('ADMIN_PASSWORD')
            if not admin_password:
                if IS_PRODUCTION:
                    logger.error("ADMIN_PASSWORD environment variable not set on first boot - cannot create admin user.")
                else:
                    admin_password = secrets.token_urlsafe(12)
                    logger.warning(f"ADMIN_PASSWORD not set; generated temporary admin password: {admin_password}")

            if admin_password:
                admin = User(
                    username='admin',
                    email=os.getenv('ADMIN_EMAIL', 'admin@moscooltech.com'),
                    password_hash=generate_password_hash(admin_password),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("Default admin user created.")

        if SEED_SAMPLE_CONTENT:
            _seed_sample_content()


def _seed_sample_content():
    """Insert sample portfolio posts + SEO articles (idempotent by slug).

    Content lives in seed_data.py so the standalone scripts in scripts/ and
    this auto-seeder stay in sync. Existing slugs are skipped, so restarts
    and multi-worker boots never duplicate rows, and posts an admin has
    intentionally renamed are not resurrected.
    """
    import seed_data

    author = User.query.filter_by(username='admin').first()
    if not author:
        logger.warning("Sample content seeding skipped - no admin user.")
        return

    def _exists(slug):
        return Post.query.filter_by(slug=slug).first() is not None

    added = 0

    for spec in seed_data.PORTFOLIO_POSTS:
        title = spec['title']
        slug = re.sub(r'[^a-z0-9-]', '', title.lower().replace(' ', '-')[:250])
        if _exists(slug):
            continue
        db.session.add(Post(
            title=title,
            slug=slug,
            content=spec['content'],
            # Guard against VARCHAR(160) overflow (PostgreSQL enforces strictly;
            # an oversized value crashes the boot with StringDataRightTruncation)
            meta_description=spec['meta_description'][:160],
            image_url=spec['image'],
            image_alt=title,
            category=spec['category'],
            post_type='portfolio',
            published=True,
            author_id=author.id,
        ))
        added += 1

    for spec in seed_data.ARTICLES:
        slug = spec['slug']
        if _exists(slug):
            continue
        db.session.add(Post(
            title=spec['title'],
            slug=slug,
            content=spec['content'],
            meta_description=spec['meta_description'][:160],
            image_url=spec['image'],
            image_alt=spec['image_alt'],
            category='guides',
            post_type='article',
            published=True,
            author_id=author.id,
        ))
        added += 1

    if added:
        db.session.commit()
        logger.info(f"Seeded {added} sample portfolio/article posts (SEED_SAMPLE_CONTENT).")

# ---------------------------------------------------------------------------
# Background scheduler (news fetch + cleanup)
# ---------------------------------------------------------------------------
scheduler = None

def _fetch_news_job():
    """APScheduler wrapper that runs fetch inside an app context."""
    with app.app_context():
        try:
            fetch_news_from_api()
        except Exception as e:
            logger.error(f"Scheduled news fetch failed: {e}")

def _cleanup_news_job():
    """APScheduler wrapper that runs cleanup inside an app context."""
    with app.app_context():
        try:
            cleanup_old_news()
        except Exception as e:
            logger.error(f"Scheduled news cleanup failed: {e}")

def start_scheduler():
    """Start the background scheduler (single instance per process)."""
    global scheduler
    if scheduler is not None and scheduler.running:
        return scheduler
    if os.getenv('ENABLE_SCHEDULER', 'true').lower() in ('0', 'false', 'no'):
        logger.info("Scheduler disabled via ENABLE_SCHEDULER")
        return None

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=_fetch_news_job, trigger=IntervalTrigger(days=1), id='fetch_news', name='Fetch News from API')
    scheduler.add_job(func=_cleanup_news_job, trigger=IntervalTrigger(days=1), id='cleanup_news', name='Cleanup Old News')
    scheduler.start()
    logger.info("Background scheduler started")
    return scheduler

# Run DB bootstrap on import so tables exist under gunicorn too (idempotent).
# The scheduler starts when the app is actually run (see below), not on import,
# to avoid duplicate jobs across gunicorn workers.
init_database()

if __name__ == '__main__':
    start_scheduler()
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
    except (KeyboardInterrupt, SystemExit):
        if scheduler is not None:
            scheduler.shutdown()
            logger.info("Scheduler shut down")
