"""Seed the database with sample portfolio posts from seed_data.py.

Fixes the SEO audit finding of an empty "Portfolio (0)" section on the
homepage by adding three realistic, location-specific job write-ups
(Lagos Mainland & Ogun State). Idempotent: existing slugs are skipped,
so it is safe to run more than once.

Usage (from the moscooltech directory):
    FLASK_ENV=production SECRET_KEY=... DATABASE_URL=... python3 scripts/seed_portfolio.py
Environment variables may also live in a .env file next to app.py.

NOTE: The images are generic stock placeholders. Replace them with real
before/after job photos via the admin panel as soon as possible - real
photos are what build customer trust (and the SEO scan flagged this).
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_dotenv():
    """Minimal .env loader (no external dependency)."""
    env_file = ROOT / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

import app as appmod  # noqa: E402
import seed_data  # noqa: E402  (shared content - single source of truth)
from app import Post, User, db  # noqa: E402


def make_slug(title):
    """Mirror the slug logic used by the admin post form in app.py."""
    slug = title.lower().replace(' ', '-')[:250]
    return re.sub(r'[^a-z0-9-]', '', slug)


def seed():
    with appmod.app.app_context():
        author = User.query.filter_by(username='admin').first()
        if not author:
            print('ERROR: admin user not found. Start the app once to create it, then re-run.')
            sys.exit(1)

        added = skipped = 0
        for spec in seed_data.PORTFOLIO_POSTS:
            slug = make_slug(spec['title'])
            if Post.query.filter_by(slug=slug).first():
                print(f'SKIP (exists): {slug}')
                skipped += 1
                continue

            post = Post(
                title=spec['title'],
                slug=slug,
                content=spec['content'],
                meta_description=spec['meta_description'],
                image_url=spec['image'],
                image_alt=spec['title'],
                category=spec['category'],
                post_type='portfolio',
                published=True,
                author_id=author.id,
            )
            db.session.add(post)
            print(f'ADDED: {slug}')
            added += 1

        db.session.commit()
        print(f'\nDone: {added} added, {skipped} skipped.')


if __name__ == '__main__':
    seed()
