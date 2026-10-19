"""Smoke tests for the Moscool Technical Services Flask app.

These mirror the deployment-critical flows: every public/admin page renders,
authentication gates admin routes, CSRF protects all state changes, bot
honeypots block spam, user content is HTML-escaped, and security/SEO headers
are present. Run with:  python -m pytest
"""
from datetime import datetime

from conftest import login  # noqa: F401  (re-exported helper)

import app as app_module
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


# ---------------------------------------------------------------------------
# Seed content fits PostgreSQL column limits
# ---------------------------------------------------------------------------
# SQLite (used by the test DB) does NOT enforce VARCHAR lengths, but
# PostgreSQL on Render does: an oversized value fails the boot with
# StringDataRightTruncation. These checks catch that before deploy.
def test_seed_data_fits_post_column_limits():
    import re as _re
    import seed_data

    limits = {'title': 200, 'slug': 250, 'meta_description': 160, 'image_alt': 200}

    def _check(source, **fields):
        for field, value in fields.items():
            assert value is not None and len(value) <= limits[field], (
                f'{source}: {field} is {len(value)} chars, limit {limits[field]}: {value!r}'
            )

    for spec in seed_data.PORTFOLIO_POSTS:
        slug = _re.sub(r'[^a-z0-9-]', '', spec['title'].lower().replace(' ', '-')[:250])
        _check(spec['title'][:40], title=spec['title'], slug=slug,
               meta_description=spec['meta_description'], image_alt=spec['title'])

    for spec in seed_data.ARTICLES:
        slug = spec.get('slug') or _re.sub(r'[^a-z0-9-]', '', spec['title'].lower().replace(' ', '-')[:250])
        _check(spec['title'][:40], title=spec['title'], slug=slug,
               meta_description=spec['meta_description'], image_alt=spec['image_alt'])


def test_seeder_truncates_oversized_meta_description(client):
    """Defense-in-depth: even if seed data drifts over the limit, the seeder
    must truncate instead of crashing the boot on PostgreSQL."""
    import seed_data
    from app import Post, db

    class _FakeOversized(list):
        pass

    # Temporarily inject an oversized meta_description into the first article
    original = seed_data.ARTICLES[0]['meta_description']
    seed_data.ARTICLES[0]['meta_description'] = 'X' * 200
    try:
        with client.application.app_context():
            # Point the fake spec at a slug guaranteed not to exist yet
            seed_data.ARTICLES[0]['slug'] = 'oversize-probe-article'
            app_module._seed_sample_content()
            post = Post.query.filter_by(slug='oversize-probe-article').first()
            assert post is not None
            assert len(post.meta_description) <= 160
    finally:
        seed_data.ARTICLES[0]['meta_description'] = original
        with client.application.app_context():
            post = Post.query.filter_by(slug='oversize-probe-article').first()
            if post:
                db.session.delete(post)
                db.session.commit()


# ---------------------------------------------------------------------------
# CRM: leads pipeline
# ---------------------------------------------------------------------------
def _make_contact(client, **overrides):
    with client.application.app_context():
        data = dict(name='Chinedu Okafor', email='chinedu@test.com', phone='08031234567',
                    service_needed='AC Repair', message='Unit not cooling')
        data.update(overrides)
        contact = ContactSubmission(**data)
        db.session.add(contact)
        db.session.commit()
        return contact.id


def test_crm_pages_render_after_login(client, csrf):
    login(client, csrf)
    contact_id = _make_contact(client)
    for path in ['/admin/leads', f'/admin/leads/{contact_id}', '/admin/ai']:
        r = client.get(path)
        assert r.status_code == 200, f'GET {path} -> {r.status_code}'
        assert 'name="csrf_token"' in r.get_data(as_text=True)


def test_lead_stage_and_notes(client, csrf):
    login(client, csrf)
    contact_id = _make_contact(client)
    token = csrf(client, f'/admin/leads/{contact_id}')

    r = client.post(f'/admin/leads/{contact_id}/status',
                    data={'status': 'quoted', 'estimated_value': '45000',
                          'csrf_token': token}, follow_redirects=True)
    assert r.status_code == 200
    with client.application.app_context():
        row = app_module.LeadStatus.query.filter_by(contact_id=contact_id).first()
        assert row is not None and row.status == 'quoted'
        assert row.estimated_value == 45000

    token = csrf(client, f'/admin/leads/{contact_id}')
    r = client.post(f'/admin/leads/{contact_id}/notes',
                    data={'body': 'Quoted N45,000; awaiting approval.', 'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'Quoted N45,000' in body
    with client.application.app_context():
        assert app_module.LeadNote.query.filter_by(contact_id=contact_id).count() == 1


def test_lead_status_rejects_invalid_stage(client, csrf):
    login(client, csrf)
    contact_id = _make_contact(client)
    token = csrf(client, f'/admin/leads/{contact_id}')
    client.post(f'/admin/leads/{contact_id}/status',
                data={'status': 'hacked', 'csrf_token': token}, follow_redirects=True)
    with client.application.app_context():
        assert app_module.LeadStatus.query.filter_by(contact_id=contact_id).first() is None


# ---------------------------------------------------------------------------
# AI studio (provider mocked - no network)
# ---------------------------------------------------------------------------
def _fake_article():
    return {
        'title': 'AC Installation Cost in Lagos: 2026 Price Guide',
        'meta_description': 'What a split AC installation costs in Lagos in 2026, by unit size, '
                            'plus what a fair quote includes and how to avoid common upcharges.',
        'content': '## What installation costs\n\n' + ('Concrete pricing detail. ' * 60),
        'faqs': [{'q': 'How much is installation?', 'a': 'About N40,000 to N90,000.'},
                 {'q': 'How long does it take?', 'a': 'Usually one day.'}],
        'suggested_image_alt': 'Technician installing a split AC in Lagos',
    }


def test_ai_generate_creates_draft_with_faqs(client, csrf, monkeypatch):
    login(client, csrf)
    app_module.ai_request_log.clear()
    monkeypatch.setattr(app_module.ai_service, 'is_configured', lambda: True)
    monkeypatch.setattr(app_module.ai_service, 'generate_article',
                        lambda **kwargs: _fake_article())

    token = csrf(client, '/admin/ai')
    r = client.post('/admin/ai/generate',
                    data={'topic': 'AC installation cost in Lagos', 'keyword': 'AC installation cost Lagos',
                          'category': 'air-conditioning', 'tone': 'practical',
                          'target_words': '1200', 'faq_count': '2', 'csrf_token': token},
                    follow_redirects=False)
    assert r.status_code == 302 and '/admin/posts/' in r.headers['Location']

    with client.application.app_context():
        post = Post.query.filter_by(post_type='article').order_by(Post.id.desc()).first()
        assert post is not None
        assert post.published is False  # drafts by default
        assert post.slug and post.meta_description and len(post.meta_description) <= 160
        assert app_module.PostFaq.query.filter_by(post_id=post.id).count() == 2
        assert app_module.AiGeneration.query.filter_by(status='success').count() == 1

    # Drafts are not public yet: the FAQs must be visible in the admin editor.
    body = client.get(f'/admin/posts/{post.id}/edit').get_data(as_text=True)
    assert 'How much is installation?' in body


def test_ai_generate_publishes_when_requested(client, csrf, monkeypatch):
    login(client, csrf)
    app_module.ai_request_log.clear()
    monkeypatch.setattr(app_module.ai_service, 'is_configured', lambda: True)
    monkeypatch.setattr(app_module.ai_service, 'generate_article',
                        lambda **kwargs: _fake_article())
    token = csrf(client, '/admin/ai')
    client.post('/admin/ai/generate',
                data={'topic': 'Publish test', 'publish': 'on', 'csrf_token': token})
    with client.application.app_context():
        post = Post.query.filter_by(post_type='article').order_by(Post.id.desc()).first()
        assert post is not None and post.published is True


def test_ai_generate_blocked_when_not_configured(client, csrf, monkeypatch):
    login(client, csrf)
    monkeypatch.setattr(app_module.ai_service, 'is_configured', lambda: False)
    token = csrf(client, '/admin/ai')
    r = client.post('/admin/ai/generate',
                    data={'topic': 'Should not be created', 'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    assert 'not configured' in r.get_data(as_text=True).lower()
    with client.application.app_context():
        assert Post.query.filter_by(post_type='article').count() == 0


def test_ai_queue_topic_generates_and_links_post(client, csrf, monkeypatch):
    login(client, csrf)
    app_module.ai_request_log.clear()
    monkeypatch.setattr(app_module.ai_service, 'is_configured', lambda: True)
    monkeypatch.setattr(app_module.ai_service, 'generate_article',
                        lambda **kwargs: _fake_article())
    with client.application.app_context():
        topic = app_module.ContentTopic(topic='Cold room cost', keyword='cold room cost Nigeria')
        db.session.add(topic)
        db.session.commit()
        topic_id = topic.id

    token = csrf(client, '/admin/ai')
    r = client.post(f'/admin/ai/topics/{topic_id}/generate',
                    data={'csrf_token': token}, follow_redirects=False)
    assert r.status_code == 302
    with client.application.app_context():
        topic = db.session.get(app_module.ContentTopic, topic_id)
        assert topic.status == 'generated' and topic.post_id is not None
        assert Post.query.filter_by(post_type='article').count() == 1


def test_ai_failure_is_logged_and_no_post_created(client, csrf, monkeypatch):
    login(client, csrf)
    app_module.ai_request_log.clear()
    monkeypatch.setattr(app_module.ai_service, 'is_configured', lambda: True)

    def boom(**kwargs):
        raise app_module.ai_service.AiError('Provider exploded safely.')

    monkeypatch.setattr(app_module.ai_service, 'generate_article', boom)
    token = csrf(client, '/admin/ai')
    r = client.post('/admin/ai/generate',
                    data={'topic': 'Failure case', 'csrf_token': token},
                    follow_redirects=True)
    assert 'Provider exploded safely.' in r.get_data(as_text=True)
    with client.application.app_context():
        assert Post.query.filter_by(post_type='article').count() == 0
        assert app_module.AiGeneration.query.filter_by(status='error').count() == 1


# ---------------------------------------------------------------------------
# Manual FAQ editing on an existing guide
# ---------------------------------------------------------------------------
def test_admin_can_replace_faqs_on_a_post(client, csrf):
    login(client, csrf)
    with client.application.app_context():
        user = User.query.filter_by(username='admin').first()
        post = Post(title='FAQ Edit Probe', slug='faq-edit-probe', content='## Body\n\nText',
                    meta_description='desc', post_type='article', published=True,
                    author_id=user.id)
        db.session.add(post)
        db.session.commit()
        post_id = post.id

    token = csrf(client, f'/admin/posts/{post_id}/edit')
    faqs_json = '[{"q": "New question?", "a": "New answer."}]'
    r = client.post(f'/admin/posts/{post_id}/edit',
                    data={'title': 'FAQ Edit Probe', 'content': '## Body\n\nText',
                          'meta_description': 'desc', 'category': 'guides',
                          'post_type': 'article', 'faqs_present': '1',
                          'faqs_json': faqs_json, 'published': 'on', 'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    with client.application.app_context():
        faqs = app_module.PostFaq.query.filter_by(post_id=post_id).all()
        assert len(faqs) == 1 and faqs[0].question == 'New question?'

    # Published guide renders the FAQ and the FAQPage structured data.
    body = client.get(f'/post/{post_id}').get_data(as_text=True)
    assert 'New question?' in body
    assert '"FAQPage"' in body


def test_admin_invalid_faq_json_is_rejected(client, csrf):
    login(client, csrf)
    with client.application.app_context():
        user = User.query.filter_by(username='admin').first()
        post = Post(title='Bad FAQ Probe', slug='bad-faq-probe', content='Body',
                    post_type='article', published=True, author_id=user.id)
        db.session.add(post)
        db.session.commit()
        post_id = post.id

    token = csrf(client, f'/admin/posts/{post_id}/edit')
    r = client.post(f'/admin/posts/{post_id}/edit',
                    data={'title': 'Bad FAQ Probe', 'content': 'Body', 'category': 'guides',
                          'post_type': 'article', 'faqs_present': '1',
                          'faqs_json': 'not-json', 'csrf_token': token},
                    follow_redirects=True)
    assert 'FAQs must be valid JSON' in r.get_data(as_text=True)
    with client.application.app_context():
        assert app_module.PostFaq.query.filter_by(post_id=post_id).count() == 0


def test_ai_generate_queued_endpoint_processes_oldest_topic(client, csrf, monkeypatch):
    login(client, csrf)
    app_module.ai_request_log.clear()
    monkeypatch.setattr(app_module.ai_service, 'is_configured', lambda: True)
    monkeypatch.setattr(app_module.ai_service, 'generate_article',
                        lambda **kwargs: _fake_article())
    with client.application.app_context():
        topic = app_module.ContentTopic(topic='Oldest queued topic')
        db.session.add(topic)
        db.session.commit()
        topic_id = topic.id

    token = csrf(client, '/admin/ai')
    r = client.post('/admin/ai/generate-queued', data={'csrf_token': token},
                    follow_redirects=False)
    assert r.status_code == 302
    with client.application.app_context():
        topic = db.session.get(app_module.ContentTopic, topic_id)
        assert topic.status == 'generated'
        assert app_module.Post.query.filter_by(post_type='article').count() == 1


def test_deleting_an_ai_post_clears_dependents(client, csrf):
    login(client, csrf)
    with client.application.app_context():
        user = User.query.filter_by(username='admin').first()
        post = Post(title='Delete Me', slug='delete-me', content='Body',
                    post_type='article', published=True, author_id=user.id)
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        db.session.add(app_module.PostFaq(post_id=post_id, question='Q?', answer='A.'))
        db.session.add(app_module.AiGeneration(topic='Delete Me', status='success', post_id=post_id))
        db.session.add(app_module.ContentTopic(topic='Delete Me', status='generated', post_id=post_id))
        db.session.commit()

    token = csrf(client, '/admin/posts')
    r = client.post(f'/admin/posts/{post_id}/delete', data={'csrf_token': token},
                    follow_redirects=True)
    assert r.status_code == 200
    with client.application.app_context():
        assert db.session.get(Post, post_id) is None
        assert app_module.PostFaq.query.filter_by(post_id=post_id).count() == 0
        assert app_module.AiGeneration.query.filter_by(post_id=post_id).count() == 0
        topic = app_module.ContentTopic.query.filter_by(topic='Delete Me').first()
        assert topic is not None and topic.post_id is None and topic.status == 'queued'


def test_crm_and_ai_routes_require_login_and_csrf(client):
    # Anonymous GETs redirect to the login page.
    for path in ['/admin/leads', '/admin/ai']:
        r = client.get(path)
        assert r.status_code == 302 and '/admin/login' in r.headers.get('Location', '')

    # State changes without a CSRF token are rejected before the view runs.
    assert client.post('/admin/ai/generate', data={'topic': 'x'}).status_code == 400
    assert client.post('/admin/leads/1/status', data={'status': 'won'}).status_code == 400
    assert client.post('/admin/leads/1/notes', data={'body': 'x'}).status_code == 400
