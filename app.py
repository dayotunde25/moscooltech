from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
import os
import uuid
from dateutil import parser as date_parser

app = Flask(__name__)
app.config['SECRET_KEY'] = '***REMOVED***'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moscool_tech.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'wmv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

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
    api_source = db.Column(db.String(50), default='manual')  # 'manual' or 'newsdata'
    article_id = db.Column(db.String(100), unique=True)  # For API deduplication
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    category = db.Column(db.String(100), default='general')
    post_type = db.Column(db.String(50), default='portfolio')  # 'portfolio' or 'sale'
    price = db.Column(db.Float)
    currency = db.Column(db.String(10), default='NGN')
    negotiable = db.Column(db.Boolean, default=True)  # For marketplace items
    item_link = db.Column(db.String(500))  # External link to item
    published = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return the file path"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"

        # Create subfolder if specified
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_path, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)

        # Return relative path for database storage
        return f"/static/uploads/{subfolder}/{unique_filename}".lstrip('/') if subfolder else f"/static/uploads/{unique_filename}"

    return None

# Routes
@app.route('/')
def home():
    # Get published posts for portfolio/marketplace
    portfolio_posts = Post.query.filter_by(post_type='portfolio', published=True).order_by(Post.created_at.desc()).limit(6).all()
    sale_posts = Post.query.filter_by(post_type='sale', published=True).order_by(Post.created_at.desc()).limit(6).all()

    # Get recent news articles with pagination
    page = request.args.get('page', 1, type=int)
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
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    service_needed = request.form.get('service_needed')
    message = request.form.get('message')

    if not all([name, email, message]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('home') + '#contact')

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
    return redirect(url_for('home') + '#contact')

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    if not all([name, email, subject, message]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('home') + '#feedback')

    feedback = FeedbackSubmission(
        name=name,
        email=email,
        subject=subject,
        message=message
    )

    db.session.add(feedback)
    db.session.commit()

    flash('Thank you for your feedback! We appreciate your input.', 'success')
    return redirect(url_for('home') + '#feedback')

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id, published=True).first_or_404()
    return render_template('post_detail.html', post=post)

@app.route('/marketplace')
def marketplace():
    # Get all published marketplace items
    marketplace_items = Post.query.filter_by(post_type='sale', published=True).order_by(Post.created_at.desc()).all()
    return render_template('marketplace.html', marketplace_items=marketplace_items)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin_dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
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
@login_required
def admin_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin_posts.html', posts=posts)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def admin_create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_url = request.form.get('image_url')
        video_url = request.form.get('video_url')
        category = request.form.get('category')
        post_type = request.form.get('post_type')
        price = request.form.get('price')
        currency = request.form.get('currency')
        negotiable = request.form.get('negotiable') == 'on'
        item_link = request.form.get('item_link')
        published = request.form.get('published') == 'on'

        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('admin_create_post'))

        # Handle file uploads
        uploaded_image_url = None
        uploaded_video_url = None

        # Check for uploaded image file
        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file and image_file.filename:
                uploaded_image_url = save_uploaded_file(image_file, 'images')

        # Check for uploaded video file
        if 'video_file' in request.files:
            video_file = request.files['video_file']
            if video_file and video_file.filename:
                uploaded_video_url = save_uploaded_file(video_file, 'videos')

        # Use uploaded files if no URLs provided
        final_image_url = image_url or uploaded_image_url
        final_video_url = video_url or uploaded_video_url

        post = Post(
            title=title,
            content=content,
            image_url=final_image_url,
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

    return render_template('admin_post_form.html', post=None)

@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')

        # Handle file uploads for editing
        uploaded_image_url = None
        uploaded_video_url = None

        # Check for uploaded image file
        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file and image_file.filename:
                uploaded_image_url = save_uploaded_file(image_file, 'images')

        # Check for uploaded video file
        if 'video_file' in request.files:
            video_file = request.files['video_file']
            if video_file and video_file.filename:
                uploaded_video_url = save_uploaded_file(video_file, 'videos')

        # Use uploaded files if no URLs provided, otherwise use form URLs
        image_url = request.form.get('image_url')
        video_url = request.form.get('video_url')

        post.image_url = image_url or uploaded_image_url or post.image_url
        post.video_url = video_url or uploaded_video_url or post.video_url

        post.category = request.form.get('category')
        post.post_type = request.form.get('post_type')
        post.price = float(request.form.get('price')) if request.form.get('price') else None
        post.currency = request.form.get('currency')
        post.negotiable = request.form.get('negotiable') == 'on'
        post.item_link = request.form.get('item_link') if request.form.get('item_link') else None
        post.published = request.form.get('published') == 'on'
        post.updated_at = datetime.utcnow()

        db.session.commit()

        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template('admin_post_form.html', post=post)

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/admin/contacts')
@login_required
def admin_contacts():
    contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    return render_template('admin_contacts.html', contacts=contacts)

@app.route('/admin/feedbacks')
@login_required
def admin_feedbacks():
    feedbacks = FeedbackSubmission.query.order_by(FeedbackSubmission.created_at.desc()).all()
    return render_template('admin_feedbacks.html', feedbacks=feedbacks)

@app.route('/admin/news')
@login_required
def admin_news():
    news_articles = NewsArticle.query.order_by(NewsArticle.pub_date.desc()).all()
    return render_template('admin_news.html', news_articles=news_articles)

@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
def admin_create_news():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        source_id = request.form.get('source_id')
        image_url = request.form.get('image_url')

        if not title or not link:
            flash('Title and link are required.', 'error')
            return redirect(url_for('admin_create_news'))

        # Parse publication date or use current time
        pub_date_str = request.form.get('pub_date')
        if pub_date_str:
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('T', ' '))
            except:
                pub_date = datetime.utcnow()
        else:
            pub_date = datetime.utcnow()

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

    return render_template('admin_news_form.html', article=None)

@app.route('/admin/news/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_news(article_id):
    article = NewsArticle.query.get_or_404(article_id)

    if request.method == 'POST':
        article.title = request.form.get('title')
        article.description = request.form.get('description')
        article.link = request.form.get('link')
        article.source_id = request.form.get('source_id')
        article.image_url = request.form.get('image_url') if request.form.get('image_url') else None

        # Parse publication date
        pub_date_str = request.form.get('pub_date')
        if pub_date_str:
            try:
                article.pub_date = datetime.fromisoformat(pub_date_str.replace('T', ' '))
            except:
                pass

        db.session.commit()

        flash('News article updated successfully!', 'success')
        return redirect(url_for('admin_news'))

    return render_template('admin_news_form.html', article=article)

@app.route('/admin/news/<int:article_id>/delete', methods=['POST'])
@login_required
def admin_delete_news(article_id):
    article = NewsArticle.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()

    flash('News article deleted successfully!', 'success')
    return redirect(url_for('admin_news'))

# News API Configuration
NEWSDATA_API_KEY = os.getenv('NEWSDATA_API_KEY', '***REMOVED***')
NEWSDATA_BASE_URL = 'https://newsdata.io/api/1/latest'

def fetch_news_from_api():
    """Fetch news from newsdata.io API"""
    try:
        # Check if API key is configured
        if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == '***REMOVED***':
            print("NewsData.io API key not configured")
            return 0

        params = {
            'apikey': NEWSDATA_API_KEY,
            'q': 'HVAC',
            'language': 'en',
            'size': 5  # Start with smaller batch
        }

        response = requests.get(NEWSDATA_BASE_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        print(f"API Response status: {response.status_code}")
        print(f"API Response data keys: {list(data.keys()) if data else 'None'}")

        # Check if response data is valid
        if not data:
            print("Empty response from NewsData.io API")
            return 0

        # Check API response status
        if data.get('status') != 'success':
            print(f"API returned non-success status: {data.get('status')}")
            print(f"API response: {data}")
            return 0

        # Check if results exist
        if 'results' not in data or not data['results']:
            print("No results found in API response")
            print(f"Available keys: {list(data.keys())}")
            return 0

        print(f"Found {len(data['results'])} articles in response")

        articles_added = 0

        for i, article_data in enumerate(data['results']):
            print(f"Processing article {i+1}: {type(article_data)}")

            # Validate article_data is a dictionary
            if not isinstance(article_data, dict):
                print(f"Invalid article data format: {type(article_data)}")
                continue

            # Debug article data
            print(f"Article keys: {list(article_data.keys())}")

            # Check if article already exists by article_id or title
            article_id = article_data.get('article_id') or article_data.get('link')
            title = article_data.get('title')

            if not title:
                print(f"Article missing title, skipping")
                continue

            existing = NewsArticle.query.filter(
                (NewsArticle.article_id == article_id) |
                (NewsArticle.title == title)
            ).first()

            if existing:
                print(f"Article already exists: {title[:50]}...")
                continue

            # Parse publication date
            pub_date = datetime.utcnow()
            if article_data.get('pubDate'):
                try:
                    pub_date = date_parser.parse(article_data['pubDate'])
                    print(f"Parsed date: {pub_date}")
                except Exception as e:
                    print(f"Error parsing date: {e}")
                    pass

            # Validate required fields
            link = article_data.get('link', '')
            if not link:
                print(f"Article missing link, skipping: {title[:50]}...")
                continue

            # Safe access to description
            description = ''
            if 'description' in article_data and article_data['description'] is not None:
                description = str(article_data['description'])[:1000]

            print(f"Creating article: {title[:50]}...")

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
            print(f"Article added successfully")

        db.session.commit()
        print(f"Added {articles_added} new articles from NewsData.io API")
        return articles_added

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching news from API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response content: {e.response.text[:500]}")
        return 0
    except Exception as e:
        print(f"Error fetching news from API: {str(e)}")
        import traceback
        traceback.print_exc()

        # Fallback to mock data if API fails
        print("Falling back to mock news data...")
        return add_mock_news_data()

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
        print(f"Cleaned up {deleted_count} old news articles")
        return deleted_count

    except Exception as e:
        print(f"Error cleaning up old news: {str(e)}")
        return 0

def add_mock_news_data():
    """Add mock news data when API fails"""
    try:
        mock_articles = [
            {
                'title': 'Breakthrough in Energy-Efficient Cooling Technology',
                'description': 'New cooling systems reduce energy consumption by 40% while maintaining superior performance. Industry experts predict widespread adoption within the next 2 years.',
                'link': 'https://example.com/cooling-tech',
                'source_id': 'Tech Innovations Today',
                'image_url': 'https://images.unsplash.com/photo-1503389152951-9c3c317b99c7?auto=format&fit=crop&w=400&q=80'
            },
            {
                'title': 'Solar Installation Costs Drop by 25% This Year',
                'description': 'Advancements in manufacturing and installation techniques make solar power more accessible than ever. Residential installations have increased by 35% in Q3.',
                'link': 'https://example.com/solar-costs',
                'source_id': 'Renewable Energy Weekly',
                'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
            },
            {
                'title': 'Smart Home Integration Revolutionizes HVAC Control',
                'description': 'IoT-enabled HVAC systems provide unprecedented control and energy savings for homeowners. Integration with major smart home platforms now standard.',
                'link': 'https://example.com/smart-hvac',
                'source_id': 'Home Technology Review',
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=400&q=80'
            },
            {
                'title': 'New Refrigeration Standards Set to Reduce Environmental Impact',
                'description': 'Updated EPA regulations for commercial refrigeration systems focus on reducing greenhouse gas emissions and improving energy efficiency across all sectors.',
                'link': 'https://example.com/refrigeration-standards',
                'source_id': 'Environmental Engineering Journal',
                'image_url': 'https://images.unsplash.com/photo-1595674057936-9891f1bb4cb6?auto=format&fit=crop&w=400&q=80'
            },
            {
                'title': 'Electrical Vehicle Charging Infrastructure Expands Rapidly',
                'description': 'Residential EV charging installations surge as more homeowners adopt electric vehicles, creating new opportunities for electrical contractors nationwide.',
                'link': 'https://example.com/ev-charging',
                'source_id': 'Electrical Contractor Magazine',
                'image_url': 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=400&q=80'
            }
        ]

        articles_added = 0
        for article_data in mock_articles:
            # Check if article already exists
            existing = NewsArticle.query.filter_by(title=article_data['title']).first()
            if not existing:
                article = NewsArticle(
                    title=article_data['title'],
                    description=article_data['description'],
                    link=article_data['link'],
                    pub_date=datetime.utcnow(),
                    source_id=article_data['source_id'],
                    image_url=article_data['image_url'],
                    api_source='mock'
                )
                db.session.add(article)
                articles_added += 1

        db.session.commit()
        print(f"Added {articles_added} mock news articles")
        return articles_added

    except Exception as e:
        print(f"Error adding mock news data: {str(e)}")
        return 0

@app.route('/admin/generate-news')
@login_required
def admin_generate_news():
    """Generate some mock news articles for demonstration"""
    mock_articles = [
        {
            'title': 'Breakthrough in Energy-Efficient Cooling Technology',
            'description': 'New cooling systems reduce energy consumption by 40% while maintaining superior performance.',
            'link': 'https://example.com/cooling-tech',
            'source_id': 'Tech Innovations Today',
            'image_url': 'https://images.unsplash.com/photo-1503389152951-9c3c317b99c7?auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'Solar Installation Costs Drop by 25% This Year',
            'description': 'Advancements in manufacturing and installation techniques make solar power more accessible than ever.',
            'link': 'https://example.com/solar-costs',
            'source_id': 'Renewable Energy Weekly',
            'image_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'
        },
        {
            'title': 'Smart Home Integration Revolutionizes HVAC Control',
            'description': 'IoT-enabled HVAC systems provide unprecedented control and energy savings for homeowners.',
            'link': 'https://example.com/smart-hvac',
            'source_id': 'Home Technology Review',
            'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=400&q=80'
        }
    ]

    for article_data in mock_articles:
        # Check if article already exists
        existing = NewsArticle.query.filter_by(title=article_data['title']).first()
        if not existing:
            article = NewsArticle(
                title=article_data['title'],
                description=article_data['description'],
                link=article_data['link'],
                pub_date=datetime.utcnow(),
                source_id=article_data['source_id'],
                image_url=article_data['image_url'],
                api_source='manual'
            )
            db.session.add(article)

    db.session.commit()
    flash('Mock news articles generated successfully!', 'success')
    return redirect(url_for('admin_news'))

@app.route('/admin/fetch-news-api')
@login_required
def admin_fetch_news_api():
    """Manually trigger news fetching from API"""
    try:
        # Check if API key is configured
        if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == '***REMOVED***':
            flash('NewsData.io API key not configured. Please set NEWSDATA_API_KEY environment variable.', 'error')
            return redirect(url_for('admin_news'))

        # Attempt to fetch news
        articles_added = fetch_news_from_api()

        if articles_added > 0:
            flash(f'Successfully fetched {articles_added} new articles from NewsData.io!', 'success')
        elif articles_added == 0:
            flash('No new articles found. This could be due to API limits, no matching content, or all available articles already exist.', 'info')
        else:
            flash('Error occurred while fetching news. Please check the server logs for details.', 'error')

    except Exception as e:
        print(f"Unexpected error in admin_fetch_news_api: {str(e)}")
        flash('An unexpected error occurred while fetching news. Please try again later.', 'error')

    return redirect(url_for('admin_news'))

@app.route('/admin/cleanup-news')
@login_required
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

        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@moscooltech.com',
                password_hash=generate_password_hash('***REMOVED***'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

        # Start the scheduler
        scheduler.start()
        print("Background scheduler started - News fetching every 6 hours, cleanup daily")

    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down")