# Moscool Technical Services - Flask Application

A modern, responsive website for a technical services company offering AC repair, refrigeration, solar panel installation, and electrical services. This is a complete Flask conversion of the original React application.

## 🚀 Technologies Used

- **Backend**: Python Flask 2.3.3
- **Database**: SQLite with SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5.3.0, Jinja2 templates
- **Icons**: Font Awesome 6.4.0

## 📁 Project Structure

```
moscool-tech-flask/
├── app.py                      # Main Flask application
├── sample_data.py              # Script to populate sample data
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
├── templates/                  # Jinja2 templates
│   ├── base.html              # Base template with header/footer
│   ├── home.html              # Home page with all sections
│   ├── post_detail.html       # Individual post/portfolio item page
│   ├── admin_login.html       # Admin login page
│   ├── admin_dashboard.html   # Admin dashboard
│   ├── admin_posts.html       # Post management
│   ├── admin_post_form.html   # Create/edit posts
│   ├── admin_news.html        # News article management
│   ├── admin_news_form.html   # Create/edit news articles
│   ├── admin_contacts.html    # Contact submissions management
│   └── admin_feedbacks.html   # Feedback submissions management
└── static/                    # Static files
    ├── css/
    │   └── style.css         # Custom styles
    ├── js/                   # JavaScript files (if needed)
    └── images/               # Image assets
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd moscool-tech-flask
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to: http://127.0.0.1:5000
   - Admin login: http://127.0.0.1:5000/admin/login
   - Default admin credentials: `admin` / `***REMOVED***`

## 🌐 Features

### Public Features
- ✅ Responsive homepage with all sections (Hero, Services, About, Portfolio, News, Feedback, Contact)
- ✅ Contact form with database storage
- ✅ Feedback form with database storage
- ✅ Portfolio/marketplace with posts for sale and portfolio items
- ✅ News articles display
- ✅ Individual post detail pages
- ✅ WhatsApp and phone integration
- ✅ Social media links

### Admin Features
- ✅ Secure admin authentication
- ✅ Dashboard with statistics
- ✅ Portfolio post management (CRUD operations)
- ✅ News article management (manual + API integration)
- ✅ Automatic news fetching from NewsData.io API
- ✅ Contact submissions management
- ✅ Feedback submissions management
- ✅ Automatic cleanup of old news articles (30+ days)
- ✅ Manual news generation for testing

## 💾 Database

The application uses SQLite with the following tables:

- **Users**: Admin authentication
- **Contact Submissions**: Customer contact form data
- **Feedback Submissions**: Customer feedback data
- **News Articles**: Industry news articles (automatically fetched from NewsData.io API)
- **Posts**: Portfolio items and marketplace listings

### News API Integration

The application automatically fetches news articles from [NewsData.io](https://newsdata.io/) API:

- **Automatic Fetching**: News articles are fetched daily at midnight
- **Cleanup**: Articles older than 30 days are automatically deleted
- **Deduplication**: Prevents duplicate articles using article IDs
- **Pagination**: News articles are paginated on the homepage (6 per page)

#### API Setup

1. Get a free API key from [NewsData.io](https://newsdata.io/)
2. Create a `.env` file in the project root:
   ```env
   NEWSDATA_API_KEY=***REMOVED***
   ```
3. The application will automatically start fetching news once the API key is configured

#### Manual News Management

You can also manually:
- Add news articles through the admin panel
- Fetch news immediately using the "Fetch from API" button
- Generate mock news for testing
- Clean up old articles manually

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=***REMOVED***

# NewsData.io API Configuration
# Get your free API key from: https://newsdata.io/
NEWSDATA_API_KEY=your-newsdata-api-key-here
```

### Admin User

Default admin user is created automatically:
- **Username**: admin
- **Password**: ***REMOVED***

**⚠️ Important**: Change the default password in production!

## 🚀 Deployment

### Production Deployment

1. Set `FLASK_ENV=production` in your environment
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 app:app
   ```

3. Use a reverse proxy like Nginx
4. Set up proper database (PostgreSQL recommended for production)
5. Configure environment variables securely

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 🤝 Usage

### Admin Panel

1. Navigate to `/admin/login`
2. Login with admin credentials
3. Access various management sections:
   - **Dashboard**: Overview and statistics
   - **Posts**: Manage portfolio and marketplace items
   - **News**: Manage news articles
   - **Contacts**: View contact form submissions
   - **Feedback**: View feedback submissions

### Content Management

- **Posts**: Create portfolio items or items for sale
- **News**: Add industry news articles manually, fetch from NewsData.io API, or generate mock data
- **Automatic Tasks**: News fetching runs daily, old articles are cleaned up automatically
- **Forms**: All form submissions are stored in the database and can be viewed in the admin panel

## 📞 Support

For technical support or feature requests:
- **Email**: contact@moscooltech.com
- **Phone**: +234(90)33150460
- **WhatsApp**: +2349033150460

## 📄 License

This project is licensed under the MIT License.

---

Built with ❤️ using Flask and Bootstrap