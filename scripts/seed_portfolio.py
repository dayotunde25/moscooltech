"""Seed the database with sample portfolio posts.

Fixes the SEO audit finding of an empty "Portfolio (0)" section on the
homepage by adding three realistic, location-specific job write-ups
(Lagos Mainland & Ogun State). Idempotent: existing slugs are skipped,
so it is safe to run more than once.

Usage (from the moscooltech directory):
    FLASK_ENV=production SECRET_KEY=... DATABASE_URL=... python3 scripts/seed_portfolio.py
Environment variables may also live in a .env file next to app.py.

NOTE: The images below are generic stock placeholders. Replace them with
real before/after job photos via the admin panel as soon as possible —
real photos are what build customer trust (and the SEO scan flagged this).
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
from app import db, Post, User  # noqa: E402

IMG = 'https://images.unsplash.com/{}?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'

PORTFOLIO_POSTS = [
    {
        'title': 'AC Repair in Ikeja: Split Unit Gas Recharge & Compressor Fix',
        'image': IMG.format('photo-1621905251918-48416bd8575a'),
        'category': 'air-conditioning',
        'meta_description': 'Case study: split AC repaired in Ikeja, Lagos — refrigerant recharge, capacitor replacement and cooling restored same day by Moscool technicians.',
        'content': (
            'A homeowner in Ikeja, Lagos Mainland contacted us when their 1.5HP split air conditioner '
            'stopped cooling during one of the hottest weeks of the year. The unit ran continuously but '
            'only blew warm air, and electricity bills were climbing because it never cycled off.\n\n'
            'Our technician arrived the same day and carried out a full diagnostic. Gauges showed the '
            'refrigerant pressure had dropped well below specification, pointing to a slow leak on the '
            'flare nut connection. The indoor unit also drew excessive current, and the run capacitor '
            'tested outside its rated microfarad range.\n\n'
            'Work completed:\n'
            '- Located and sealed the refrigerant leak at the indoor unit flare connection\n'
            '- Replaced the failed run capacitor with a manufacturer-approved part\n'
            '- Vacuumed the line set to remove moisture before recharging\n'
            '- Recharged the system with the correct R410A charge by weight\n'
            '- Cleaned both evaporator and condenser coils and flushed the drain line\n\n'
            'The unit restored full cooling within the hour and cycled off normally. Follow-up testing a '
            'week later confirmed stable pressures and normal current draw, so the homeowner also saved '
            'on energy costs.\n\n'
            'If your AC is blowing warm air, tripping the breaker, or running without cooling anywhere '
            'in Lagos Mainland or Ogun State, call Moscool Technical Services on +2349033150460. We '
            'repair split units, cassettes and window units, and our emergency line is open 24/7.'
        ),
    },
    {
        'title': '5kVA Solar + Inverter Installation in Magboro, Ogun State',
        'image': IMG.format('photo-1509391366360-2e959784a276'),
        'category': 'solar',
        'meta_description': 'Hybrid 5kVA inverter, 6 x 450W solar panels and lithium storage installed in Magboro, Ogun State — near-silent power through every outage.',
        'content': (
            'A family in Magboro, Ogun State was spending heavily on petrol for their generator, running '
            'it several hours daily for lights, fans, a fridge and a TV. They asked us to design a solar '
            'and inverter system that would remove most of that generator dependency.\n\n'
            'We started with a load audit: measuring the running and surge wattage of every essential '
            'appliance to size both the inverter and battery bank correctly. Based on the audit we '
            'recommended a 5kVA hybrid inverter with lithium storage, which handles the peak load with '
            'headroom for future additions.\n\n'
            'Installation details:\n'
            '- 6 x 450W monocrystalline panels mounted on a custom aluminium rail on the roof\n'
            '- Panels oriented south with zero shading between 9am and 4pm for maximum yield\n'
            '- 5kVA hybrid inverter installed in a ventilated space with surge protection\n'
            '- 10kWh lithium battery bank with a 15-year design life\n'
            '- Dedicated changeover so the generator only starts for heavy loads like pumping\n\n'
            'The system now powers the home through the night on solar stored during the day, and the '
            'generator has been almost completely retired. The family reports the system is quieter, '
            'cheaper and needs none of the maintenance the generator demanded.\n\n'
            'Planning a solar or inverter installation in Lagos Mainland, Magboro, Mowe, Ibafo or '
            'anywhere in Ogun State? Moscool Technical Services offers free load audits and honest '
            'system sizing. Call +2349033150460 or send us a WhatsApp message to get started.'
        ),
    },
    {
        'title': 'Commercial Freezer Compressor Replacement in Yaba, Lagos',
        'image': IMG.format('photo-1581092918056-0c4c3acd3789'),
        'category': 'refrigeration',
        'meta_description': 'Commercial showcase freezer in Yaba, Lagos repaired — compressor replaced and temperature restored to food-safe levels in one visit.',
        'content': (
            'A supermarket in Yaba, Lagos Mainland called us at 7pm when one of their glass-door showcase '
            'freezers began climbing above food-safe temperature. With stock worth several hundred '
            'thousand naira inside, every hour of downtime risked a serious loss, and the compressor was '
            'cycling loudly before cutting out completely.\n\n'
            'Our refrigeration engineer attended within the hour. The compressor windings tested open on '
            'one phase and the overload protector had been tripping repeatedly — classic terminal failure '
            'on an ageing sealed unit. The condenser was also heavily caked with dust, which had been '
            'forcing the compressor to run hot for months.\n\n'
            'Work completed:\n'
            '- Confirmed compressor failure with electrical and pressure diagnostics\n'
            '- Replaced the sealed unit with a correctly matched compressor for the cabinet\n'
            '- Replaced the drier filter to protect the new compressor from moisture\n'
            '- Deep-cleaned the condenser coil and verified airflow across it\n'
            '- Evacuated, leak-tested and recharged the refrigerant circuit\n'
            '- Verified the cabinet held -18°C over a full 24-hour pull-down log\n\n'
            'The freezer was back at food-safe temperature the same evening, protecting the shop\'s stock '
            'and their health inspection record. We also scheduled quarterly preventive maintenance so '
            'the remaining units are cleaned and checked before they fail.\n\n'
            'Commercial refrigeration failing in Lagos Mainland or Ogun State? Moscool Technical '
            'Services repairs freezers, chillers, display cases and cold rooms, with 24/7 emergency '
            'response. Call +2349033150460 before stock is lost.'
        ),
    },
]


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
        for spec in PORTFOLIO_POSTS:
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
