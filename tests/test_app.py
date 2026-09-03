"""Smoke tests for the Moscool Technical Services Flask app.

These mirror the deployment-critical flows: every public/admin page renders,
authentication gates admin routes, CSRF protects all state changes, bot
honeypots block spam, user content is HTML-escaped, and security/SEO headers
are present. Run with:  python -m pytest
"""
from datetime import datetime

from conftest import login  # noqa: F401  (re-exported helper)

from app import db, FeedbackSubmission, ContactSubmission, NewsArticle, Post, User


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
def test_public_pages_render(client):
    for path in ['/', '/marketplace', '/robots.txt', '/sitemap.xml', '/admin/login']:
        r = client.get(path)
        assert r.status_code == 200, f'GET {path} -> {r.status_code}'


def test_custom_404_page(client):
    r = client.get('/nonexistent-page-xyz')
    assert r.status_code == 404
    assert 'Page Not Found' in r.get_data(as_text=True)


def test_admin_requires_login(client):
    r = client.get('/admin')
    assert r.status_code == 302
    assert '/admin/login' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
def test_security_headers(client):
    r = client.get('/')
    h = r.headers
    csp = h.get('Content-Security-Policy', '')
    assert 'Content-Security-Policy' in h and 'nonce-' in csp
    # strict CSP: inline scripts must not be allowed via 'unsafe-inline'
    script_part = csp.split('script-src')[1].split(';')[0]
    assert "'unsafe-inline'" not in script_part
    assert 'Strict-Transport-Security' in h  # HSTS (production mode)
    assert h.get('X-Content-Type-Options') == 'nosniff'
    assert h.get('X-Frame-Options') == 'SAMEORIGIN'
    assert 'Referrer-Policy' in h


def test_csrf_required_for_state_changes(client):
    r = client.post('/contact', data={'name': 'x', 'email': 'x@x.com', 'message': 'hi'})
    assert r.status_code == 400  # CSRF token missing


# ---------------------------------------------------------------------------
# SEO / social
# ---------------------------------------------------------------------------
def test_home_seo_markup(client):
    body = client.get('/').get_data(as_text=True)
    assert '/static/img/og-image.png' in body          # default social share image
    assert 'application/ld+json' in body and 'nonce=' in body  # LocalBusiness schema
    # both public forms must carry CSRF inputs
    assert body.count('name="csrf_token"') >= 2


def test_robots_and_sitemap(client):
    robots = client.get('/robots.txt').get_data(as_text=True)
    assert 'User-agent: *' in robots and '/sitemap.xml' in robots
    sitemap = client.get('/sitemap.xml').get_data(as_text=True)
    assert 'urlset' in sitemap and '<loc>' in sitemap


# ---------------------------------------------------------------------------
# Authentication & authorization
# ---------------------------------------------------------------------------
def test_login_rejects_wrong_password(client, csrf):
    token = csrf(client, '/admin/login')
    r = client.post('/admin/login', data={'username': 'admin', 'password': 'nope', 'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    assert 'Invalid username or password' in r.get_data(as_text=True)


def test_login_success_and_dashboard(client, csrf):
    r = login(client, csrf)
    assert r.status_code == 302
    assert r.headers.get('Location') == '/admin'
    r = client.get('/admin')
    assert r.status_code == 200
    assert 'Dashboard' in r.get_data(as_text=True)


def test_logout_is_post_only(client, csrf):
    login(client, csrf)
    # GET logout must not work (state change must be a POST)
    assert client.get('/admin/logout').status_code == 405
    token = csrf(client, '/admin')
    r = client.post('/admin/logout', data={'csrf_token': token})
    assert r.status_code == 302 and r.headers.get('Location') == '/'
    r = client.get('/admin')
    assert r.status_code == 302 and '/admin/login' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Public forms: submission + honeypot
# ---------------------------------------------------------------------------
def test_contact_form_valid(client, csrf):
    token = csrf(client, '/')
    r = client.post('/contact', data={'name': 'Ada Lovelace', 'email': 'ada@test.com',
                                      'phone': '08000000000', 'service_needed': 'AC Repair',
                                      'message': 'Please fix my unit',
                                      'csrf_token': token, 'company_website': ''},
                    follow_redirects=True)
    assert r.status_code == 200
    with client.application.app_context():
        assert ContactSubmission.query.count() == 1


def test_contact_honeypot_blocks_bot(client, csrf):
    token = csrf(client, '/')
    client.post('/contact', data={'name': 'Spam Bot', 'email': 'spam@bot.com',
                                  'message': 'buy stuff', 'csrf_token': token,
                                  'company_website': 'http://spam.example'},
                follow_redirects=True)
    with client.application.app_context():
        assert ContactSubmission.query.count() == 0  # nothing saved


def test_feedback_form_valid(client, csrf):
    token = csrf(client, '/')
    r = client.post('/feedback', data={'name': 'Rev', 'email': 'rev@test.com',
                                       'subject': 'Great work', 'message': 'Loved it',
                                       'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200
    with client.application.app_context():
        assert FeedbackSubmission.query.count() == 1


# ---------------------------------------------------------------------------
# Admin: news CRUD (all via CSRF-protected POST forms)
# ---------------------------------------------------------------------------
def test_admin_news_crud(client, csrf):
    login(client, csrf)
    token = csrf(client, '/admin/news')
    r = client.post('/admin/news/new', data={'title': 'Smoke News Item',
                                             'link': 'https://example.com/story',
                                             'description': 'desc', 'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    assert 'Smoke News Item' in r.get_data(as_text=True)
    with client.application.app_context():
        article = NewsArticle.query.filter_by(title='Smoke News Item').first()
        assert article is not None
        article_id = article.id

    token = csrf(client, '/admin/news')
    r = client.post('/admin/generate-news', data={'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200

    token = csrf(client, '/admin/news')
    r = client.post('/admin/cleanup-news', data={'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200

    token = csrf(client, '/admin/news')
    r = client.post(f'/admin/news/{article_id}/delete', data={'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    with client.application.app_context():
        assert db.session.get(NewsArticle, article_id) is None


def test_all_admin_pages_render_with_csrf(client, csrf):
    login(client, csrf)
    with client.application.app_context():
        user = User.query.filter_by(username='admin').first()
        post = Post(title='Sweep Post', slug='sweep-post', content='body', post_type='sale',
                    price=100, currency='NGN', published=True, author_id=user.id)
        db.session.add(post)
        db.session.commit()
        post_id = post.id

    pages = ['/admin', '/admin/posts', f'/admin/posts/{post_id}/edit', '/admin/posts/new',
             '/admin/news', '/admin/news/new', '/admin/contacts', '/admin/feedbacks']
    for path in pages:
        r = client.get(path)
        assert r.status_code == 200, f'GET {path} -> {r.status_code}'
        assert 'name="csrf_token"' in r.get_data(as_text=True), f'no CSRF input on {path}'


# ---------------------------------------------------------------------------
# Content safety: XSS escaping on post pages
# ---------------------------------------------------------------------------
def test_post_content_is_escaped_and_marked_up(client, csrf):
    login(client, csrf)
    evil = '<script>alert(1)</script>\nSecond line <b>bold</b>'
    with client.application.app_context():
        user = User.query.filter_by(username='admin').first()
        post = Post(title='XSS <script>probe</script>', slug='xss-probe-1', content=evil,
                    meta_description='desc', image_url='/static/uploads/images/fake.png',
                    image_alt='Refrigeration unit', post_type='portfolio', published=True,
                    author_id=user.id, created_at=datetime.utcnow())
        db.session.add(post)
        db.session.commit()
        post_id = post.id

    body = client.get(f'/post/{post_id}').get_data(as_text=True)
    # raw script tags must never reach the page; escaped + newline-><br> versions appear
    assert '<script>alert(1)</script>' not in body
    assert '&lt;script&gt;' in body
    assert '<br>' in body and '&lt;br&gt;' not in body
    # SEO/accessibility markup
    assert 'alt="Refrigeration unit"' in body
    assert 'breadcrumb' in body and 'Home' in body
    assert 'rel="canonical"' in body and f'/post/{post_id}' in body
    assert 'application/ld+json' in body and 'nonce=' in body

    sitemap = client.get('/sitemap.xml').get_data(as_text=True)
    assert f'/post/{post_id}' in sitemap
