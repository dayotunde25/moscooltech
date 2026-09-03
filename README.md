# Moscool Technical Services - Flask Application

A modern, responsive website for a technical services company offering AC repair, refrigeration, solar panel installation, and electrical services. This is a complete Flask conversion of the original React application.

## 🚀 Technologies Used

- **Backend**: Python Flask 3.1 + Gunicorn
- **Database**: SQLAlchemy (SQLite for development, PostgreSQL on Render)
- **Authentication**: Flask-Login
- **Security**: Flask-WTF CSRF protection, Werkzeug password hashing, strict CSP & security headers
- **Frontend**: Bootstrap 5.3.0, Jinja2 templates
- **Icons**: Font Awesome 6.4.0

## 📁 Project Structure

```
moscooltech/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Procfile                    # Render start command (gunicorn app:app)
├── render.yaml                 # Render Blueprint (web service + PostgreSQL)
├── .env.example                # Environment variable template (never commit .env)
├── .gitignore                  # Git ignore rules
├── templates/                  # Jinja2 templates
│   ├── base.html              # Base template with header/footer + SEO/social meta
│   ├── home.html              # Home page with all sections + LocalBusiness schema
│   ├── post_detail.html       # Individual post/portfolio item page
│   ├── marketplace.html       # Items-for-sale listing
│   ├── error.html             # Custom 400/403/404/500 pages
│   ├── admin_login.html       # Admin login page
│   ├── admin_dashboard.html   # Admin dashboard
│   ├── admin_posts.html       # Post management
│   ├── admin_post_form.html   # Create/edit posts
│   ├── admin_news.html        # News article management
│   ├── admin_news_form.html   # Create/edit news articles
│   ├── admin_contacts.html    # Contact submissions management
│   └── admin_feedbacks.html   # Feedback submissions management
└── static/                    # Static files
    ├── css/style.css          # Custom styles
    ├── js/main.js             # Public-site JavaScript (external, CSP-safe)
    ├── js/admin.js            # Admin JavaScript (external, CSP-safe)
    └── img/og-image.png       # Default social-share (Open Graph) image
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

4. **Create your local `.env`** (copy `.env.example`) and set:
   ```env
   FLASK_ENV=development
   SECRET_KEY=anything-local   # required only in production
   ADMIN_PASSWORD=something-strong
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to: http://127.0.0.1:5000
   - Admin login: http://127.0.0.1:5000/admin/login
   - Username: `admin` — password: the value of `ADMIN_PASSWORD` (set on first boot)

   > ⚠️ There is **no default password**. The `admin` account is created once,
   > with the password taken from the `ADMIN_PASSWORD` environment variable.
   > If it isn't set in development, a random one is printed to the console.

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

Copy `.env.example` to `.env` and fill in the values. The most important keys:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Session signing key — **required** in production (32+ random bytes) |
| `ADMIN_PASSWORD` | Password for the auto-created `admin` account (first boot only) |
| `FLASK_ENV` | `development` locally; `production` on Render |
| `DATABASE_URL` | PostgreSQL URL on Render; `sqlite:///...` locally (`postgres://` is auto-normalized) |
| `SITE_URL` | Optional fixed domain used by `robots.txt`/`sitemap.xml`/social tags |
| `NEWSDATA_API_KEY` | Optional NewsData.io key for automatic news fetching |

See `.env.example` for the full list with comments.

### Admin User

The `admin` user is created automatically the first time the app boots against an
empty database. Its password is **not** hardcoded — it comes from the
`ADMIN_PASSWORD` environment variable (a random password is generated and logged
if it is unset in development). In production the app refuses to start without a
`SECRET_KEY`, and no admin account is created without `ADMIN_PASSWORD`.

## 🚀 Deployment

### Production Deployment (Render)

The repository ships with a `Procfile` (`gunicorn app:app`) and a `render.yaml`
Render Blueprint. The easiest path:

1. Push this repository to GitHub
2. On Render: **New → Blueprint** and select the repository
3. Render provisions the web service **and** a PostgreSQL database automatically
4. Set `FLASK_ENV=production`, a strong `SECRET_KEY` and `ADMIN_PASSWORD` (Blueprint generates `SECRET_KEY`/`ADMIN_PASSWORD` for you — reveal them in the dashboard **Environment** tab after creation)

Manual alternative: create a Web Service, set the env vars above, and let
Render use the `Procfile` start command.

> ℹ️ The daily news scheduler only runs when started with `python app.py` (one
> process). Under gunicorn it stays off to avoid duplicate jobs across workers —
> fetch news on demand from the admin panel, or set `ENABLE_SCHEDULER=false`
> and run the app with a single worker if you need scheduled fetches.

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "app:app"]
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