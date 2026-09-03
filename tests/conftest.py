"""Pytest configuration for the Moscool app smoke tests.

Environment is configured BEFORE the app module is imported so the app picks up
production-like settings (secret key, admin password, isolated SQLite DB).
"""
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Production-like environment (exercises HSTS, secure cookies, strict modes)
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = 'test-secret-key-not-for-production-0123456789abcdef'
os.environ['ADMIN_PASSWORD'] = 'TestPass!2026'
os.environ['ADMIN_EMAIL'] = 'admin@test.local'
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(tempfile.mkdtemp(prefix='moscool-tests-'), 'test.db')
os.environ['ENABLE_SCHEDULER'] = 'false'
os.environ.pop('NEWSDATA_API_KEY', None)

import pytest  # noqa: E402

import app as appmod  # noqa: E402


@pytest.fixture()
def client():
    """Test client backed by a freshly recreated database and admin account."""
    appmod.login_attempts.clear()
    with appmod.app.app_context():
        appmod.db.drop_all()
        appmod.db.create_all()
        admin = appmod.User(
            username='admin',
            email=os.environ['ADMIN_EMAIL'],
            password_hash=appmod.generate_password_hash(os.environ['ADMIN_PASSWORD']),
            is_admin=True,
        )
        appmod.db.session.add(admin)
        appmod.db.session.commit()
    with appmod.app.test_client() as c:
        yield c


def _csrf_from(client, path):
    """Fetch a page and return the CSRF token from its first hidden input."""
    html = client.get(path).get_data(as_text=True)
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None


@pytest.fixture()
def csrf():
    """Fixture returning a helper that extracts a CSRF token for a page."""
    return _csrf_from


def login(client, csrf, username='admin', password='TestPass!2026'):
    """Log in as admin via the real login form; returns the response."""
    token = csrf(client, '/admin/login')
    assert token, 'login page did not render a CSRF token'
    return client.post(
        '/admin/login',
        data={'username': username, 'password': password, 'csrf_token': token},
        follow_redirects=False,
    )
