#!/usr/bin/env python3
"""Generate guide drafts from the AI topic queue.

Designed for a Render Cron Job (or any scheduler), so it does not depend on the
web process running a background scheduler:

    python scripts/generate_ai_drafts.py --limit 1

Publishing is off unless `--publish` is passed or AI_AUTO_PUBLISH=true is set.
Exit code is 1 only if every attempted generation failed (useful for alerting).
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import app as appmod  # noqa: E402  (needs the path insert above)


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate AI drafts from the queued topics.')
    parser.add_argument('--limit', type=int, default=1, help='how many queued topics to process (default 1)')
    parser.add_argument('--publish', action='store_true', help='publish immediately instead of saving drafts')
    args = parser.parse_args()

    limit = max(1, min(5, args.limit))

    with appmod.app.app_context():
        if not appmod.ai_service.is_configured():
            print('AI is not configured: set AI_API_KEY (and AI_MODEL) first.')
            return 1

        author = (appmod.User.query.filter_by(username='admin').first()
                  or appmod.User.query.filter_by(is_admin=True).first())
        if author is None:
            print('No admin user found - cannot assign the generated posts.')
            return 1

        topics = (appmod.ContentTopic.query.filter_by(status='queued')
                  .order_by(appmod.ContentTopic.created_at.asc())
                  .limit(limit).all())
        if not topics:
            print('Topic queue is empty; nothing to do.')
            return 0

        publish = args.publish or appmod.AI_AUTO_PUBLISH
        failures = 0
        for topic in topics:
            try:
                post = appmod.generate_ai_post(
                    topic=topic.topic,
                    keyword=topic.keyword or '',
                    category=topic.category or 'guides',
                    tone=topic.tone or 'practical',
                    target_words=topic.target_words or 1200,
                    faq_count=topic.faq_count or 0,
                    publish=publish,
                    author_id=author.id,
                    source_topic=topic,
                )
            except appmod.ai_service.AiError as exc:
                failures += 1
                print(f'FAILED  {topic.topic}: {exc}')
                continue
            except Exception as exc:  # noqa: BLE001 - cron should report, not crash silently
                failures += 1
                print(f'FAILED  {topic.topic}: unexpected error: {exc}')
                continue
            state = 'published' if post.published else 'draft'
            print(f'OK      {state} post #{post.id}: {post.title}')

        if failures and failures == len(topics):
            print(f'All {failures} generation(s) failed.')
            return 1
        print(f'Processed {len(topics) - failures}/{len(topics)} topic(s).')
        return 0


if __name__ == '__main__':
    sys.exit(main())
