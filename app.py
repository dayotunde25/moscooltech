from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from functools import wraps
import requests
import os
import uuid
from dateutil import parser as date_parser
import re
import logging

# Security: Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: Load secret key from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    logger.critical("SECRET_KEY not configured. Set the SECRET_KEY environment variable.")
    raise ValueError("SECRET_KEY environment variable must be set")

# Security: Enforce HTTPS in production
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Security: Disable debug mode in production
app.config['DEBUG'] = os.getenv('FLASK_ENV') != 'production'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///moscool_tech.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# Security: Rate limiting for login attempts
login_attempts = {}

def get_client_ip():
    """Get client IP address safely"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def check_login_rate_limit(ip_address, max_attempts=5, window_seconds=900):
    """Check if IP has exceeded login attempts"""
    now = datetime.utcnow()
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    
    # Remove old attempts outside the window
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address]
        if (now - attempt_time).total_seconds() < window_seconds
    ]
    
    if len(login_attempts[ip_address]) >= max_attempts:
        return False
    
    login_attempts[ip_address].append(now)
    return True

def require_admin(f):
    """Decorator to require admin authorization"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
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
        """Get canonical URL for SEO"""
        return url_for('post_detail', post_id=self.id, _external=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_mime_type(file_stream):
    """Validate file MIME type"""
    try:
        file_stream.seek(0)
        magic_bytes = file_stream.read(12)
        file_stream.seek(0)
        
        if magic_bytes.startswith(b'\x89PNG'):
            return 'image/png'
        elif magic_bytes.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif magic_bytes.startswith(b'GIF8'):
            return 'image/gif'
        elif b'ftyp' in magic_bytes[:12]:
            return 'video/mp4'
        return None
    except:
        return None

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return the file path"""
    if not file or not allowed_file(file.filename):
        logger.warning(f"Invalid file upload attempt: {file.filename if file else 'No file'}")
        return None
    
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        return None
    
    mime_type = validate_mime_type(file)
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Invalid MIME type: {mime_type}")
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
    """Sanitize user input"""
    if not isinstance(text, str):
        return ''
    text = text.replace('\x00', '')
    if max_length:
        text = text[:max_length]
    return text

# Security: Add security headers to all responses
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    csp = (
        "default-src 'self'; "
        "script-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' cdn.jsdelivr.net cdnjs.cloudflare.com 'unsafe-inline'; "
        "img-src 'self' data: https: unsplash.com images.unsplash.com; "
        "font-src 'self' cdnjs.cloudflare.com; "
        "connect-src 'self'; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    if app.config['DEBUG'] == False:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
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

    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    per_page = 6
    news_pagination = NewsArticle.query.order_by(NewsArticle.pub_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    news_articles = news_pagination.items

    return render_template('home.html',
                         portfolio_posts=portfolio_posts,
                         sale_posts=sale_posts,
                         news_articles=news_articles,
                         news_pagination=news_pagination)

@app.route('/contact', methods=['POST'])
def submit_contact():
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
    return render_template('post_detail.html', post=post)

@app.route('/marketplace')
def marketplace():
    marketplace_items = Post.query.filter_by(post_type='sale', published=True).order_by(Post.created_at.desc()).all()
    return render_template('marketplace.html', marketplace_items=marketplace_items)

@app.route('/robots.txt')
def robots():
    """SEO: Robots.txt for search engine crawling"""
    response = make_response("""User-agent: *
Allow: /
Disallow: /admin
Disallow: /admin/*
Disallow: /static/uploads/
Allow: /static/
Allow: /post/
Allow: /marketplace/

Sitemap: https://moscooltech.onrender.com/sitemap.xml
""")
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/sitemap.xml')
def sitemap():
    """SEO: XML sitemap for search engines"""
    try:
        posts = Post.query.filter_by(published=True).all()
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        xml += '  <url>\n'
        xml += '    <loc>https://moscooltech.onrender.com/</loc>\n'
        xml += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
        xml += '    <priority>1.0</priority>\n'
        xml += '  </url>\n'
        
        xml += '  <url>\n'
        xml += '    <loc>https://moscooltech.onrender.com/marketplace</loc>\n'
        xml += f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>\n'
        xml += '    <priority>0.8</priority>\n'
        xml += '  </url>\n'
        
        for post in posts:
            xml += '  <url>\n'
            xml += f'    <loc>{post.get_canonical_url()}</loc>\n'
            xml += f'    <lastmod>{post.updated_at.strftime("%Y-%m-%d")}</lastmod>\n'
            xml += '    <priority>0.7</priority>\n'
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
        
        if not check_login_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            flash('Too many login attempts. Please try again later.', 'error')
            return render_template('admin_login.html')
        
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('admin_login.html')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password) and user.is_admin:
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('admin_dashboard')
            return redirect(next_page)

        flash('Invalid username or password.', 'error')
        logger.info(f"Failed login attempt from IP: {client_ip}")

    return render_template('admin_login.html')

@app.route('/admin/logout')
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

    recent_contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).limit(5).all()
    recent_feedbacks = FeedbackSubmission.query.order_by(FeedbackSubmission.created_at.desc()).limit(5).all()

    return render_template('admin_dashboard.html',
                         contact_count=contact_count,
                         feedback_count=feedback_count,
                         posts_count=posts_count,
                         recent_contacts=recent_contacts,
                         recent_feedbacks=recent_feedbacks)

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
        content = sanitize_input(request.form.get('content', ''), 10000)
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
            slug = title.lower().replace(' ', '-')[:250]
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            
            post = Post(
                title=title,
                slug=slug,
                content=content,
                meta_description=meta_description or content[:160],
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

    return render_template('admin_post_form.html', post=None)

@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@require_admin
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = sanitize_input(request.form.get('title', ''), 200)
        post.content = sanitize_input(request.form.get('content', ''), 10000)
        post.meta_description = sanitize_input(request.form.get('meta_description', ''), 160)
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

        try:
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('admin_posts'))
        except Exception as e:
            logger.error(f"Error updating post: {e}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')

    return render_template('admin_post_form.html', post=post)

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@require_admin
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    try:
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

def fetch_news_from_api():
    """Fetch news from newsdata.io API"""
    try:
        if not NEWSDATA_API_KEY:
            logger.info("NewsData.io API key not configured")
            return 0

        params = {
            'apikey': NEWSDATA_API_KEY,
            'q': 'HVAC',
            'language': 'en',
            'size': 5
        }

        response = requests.get(NEWSDATA_BASE_URL, params=params, timeout=NEWS_FETCH_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'success':
            logger.warning(f"API returned non-success status: {data.get('status')}")
            return 0

        if 'results' not in data or not data['results']:
            logger.info("No results found in API response")
            return 0

        articles_added = 0

        for article_data in data['results']:
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

@app.route('/admin/fetch-news-api')
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

@app.route('/admin/cleanup-news')
@require_admin
def admin_cleanup_news():
    """Manually trigger cleanup of old news"""
    deleted_count = cleanup_old_news()

    if deleted_count > 0:
        flash(f'Successfully deleted {deleted_count} old news articles.', 'success')
    else:
        flash('No old articles to clean up.', 'info')

    return redirect(url_for('admin_news'))

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_news_from_api, trigger=IntervalTrigger(days=1), id='fetch_news', name='Fetch News from API')
scheduler.add_job(func=cleanup_old_news, trigger=IntervalTrigger(days=1), id='cleanup_news', name='Cleanup Old News')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin_password = os.getenv('ADMIN_PASSWORD')
            if not admin_password:
                logger.error("ADMIN_PASSWORD environment variable not set. Generating temporary password.")
                admin_password = os.urandom(16).hex()
                logger.warning(f"WARNING: Temporary admin password generated: {admin_password}")
            
            admin = User(
                username='admin',
                email=os.getenv('ADMIN_EMAIL', 'admin@moscooltech.com'),
                password_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin user created.")

        scheduler.start()
        logger.info("Background scheduler started")

    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down")
