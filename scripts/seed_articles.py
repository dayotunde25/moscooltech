"""Seed the database with the Week-1 SEO content roadmap articles.

Adds three long-form, keyword-targeted guides (from the LeadOS scan's content
roadmap) targeting high-volume Nigerian searches:
  1. AC Repair in Lagos ("ac repair Lagos", 2,400/mo)
  2. Solar Panel Installation in Nigeria ("solar panel installation Nigeria", 2,400/mo)
  3. Inverter vs Generator ("inverter installation cost Nigeria", 880/mo)

Content uses a small line-prefix markup rendered safely by the `article_html`
filter in app.py:
    '## '  -> <h2>,  '### ' -> <h3>,  '- ' -> <li>,  '**bold**' -> <strong>

Idempotent: existing slugs are skipped, safe to run repeatedly.

Usage (from the moscooltech directory):
    FLASK_ENV=production SECRET_KEY=... DATABASE_URL=... python3 scripts/seed_articles.py
Environment variables may also live in a .env file next to app.py.

NOTE: Images are generic stock placeholders - replace with real project photos
via the admin panel when available.
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

ARTICLES = [
    {
        'title': 'AC Repair in Lagos: What to Expect, How Much It Costs, and Who to Call',
        'slug': 'ac-repair-in-lagos-what-to-expect-costs-and-who-to-call',
        'image': IMG.format('photo-1621905251918-48416bd8575a'),
        'image_alt': 'Technician servicing a split air conditioner in Lagos',
        'meta_description': 'AC repair in Lagos explained: common faults, typical repair costs in Naira, how to choose a trustworthy technician, and 24/7 emergency service in Lagos Mainland & Ogun State.',
        'content': '''When your air conditioner fails in Lagos heat, you need it fixed fast - but a rushed decision often means paying twice: once for the technician who misdiagnosed the fault, and again for the one who actually fixed it. This guide explains what a proper AC repair in Lagos looks like, what it should realistically cost, and how to find a technician you can trust anywhere in Lagos Mainland or Ogun State.

## Common AC Problems in Lagos Homes and Offices

Lagos is hard on air conditioners. Harmattan dust, coastal humidity, salty air near the water, and unstable voltage all shorten the life of compressors, capacitors and coils. These are the faults we see most often:

- **Blowing warm air** - usually low refrigerant from a leak, a failed capacitor, or a seized compressor
- **Water leaking from the indoor unit** - a blocked condensate drain line, very common during humid months
- **Tripping the breaker** - a failing compressor or a short in the wiring; this one needs urgent attention
- **Weak airflow** - clogged filters, a dirty blower wheel, or a failing fan motor
- **Ice on the copper pipes** - low refrigerant or a dirty evaporator coil restricting airflow
- **Bad smell** - mould on the evaporator coil or a dead rodent in the ducting

### Why Lagos ACs break down faster

- Harmattan dust clogs condenser coils, forcing the compressor to run hot
- Voltage swings from the grid burn out capacitors and control boards
- Salt-laden coastal air corrodes outdoor units faster than inland areas
- Units that run 10+ hours daily simply wear out faster without preventive service

## How Much Does AC Repair Cost in Lagos?

Prices vary with the fault, the unit size (1HP to 5HP), and whether genuine or aftermarket parts are used. The figures below are realistic 2026 ranges for Lagos based on the work we do every week:

- **Diagnostic / call-out fee:** ₦5,000 - ₦15,000 (often waived if you proceed with the repair)
- **AC service (cleaning, gas top-up check):** ₦10,000 - ₦25,000 per unit
- **Refrigerant recharge (R410A / R22):** ₦25,000 - ₦60,000 depending on gas type and severity of the leak
- **Capacitor or relay replacement:** ₦10,000 - ₦25,000 including parts
- **Compressor replacement:** ₦120,000 - ₦350,000 depending on unit size
- **Full new split-unit installation:** ₦40,000 - ₦90,000 including materials

### Warning signs you are being overcharged

- Quoting a compressor replacement without first testing the capacitors and checking pressures
- "Gas topping" every few months without finding and fixing the leak - a properly sealed system does not consume gas
- No written invoice or warranty on the parts replaced
- Prices that change on arrival after a cheaper quote was given on the phone

A trustworthy technician diagnoses before quoting, explains what failed and why, and gives you a warranty on both parts and labour.

## What a Professional Repair Visit Should Look Like

When a Moscool technician arrives, the visit follows a fixed process so nothing is missed:

- **Step 1 - Interview:** when did it start, what changed, any sounds or smells
- **Step 2 - Electrical checks:** capacitor microfarad readings, current draw, contactor condition
- **Step 3 - Pressure checks:** gauge readings on both sides to confirm refrigerant charge and detect leaks
- **Step 4 - Coil and airflow inspection:** filters, evaporator and condenser condition
- **Step 5 - Written quote:** the fault, the fix, the cost, before any work starts
- **Step 6 - Repair and test:** the unit is run through a full cooling cycle before we leave
- **Step 7 - Advice:** what caused the failure and how to prevent a repeat

## DIY Checks Before You Call a Technician

Some issues you can safely rule out yourself in five minutes:

- Confirm the remote is set to cool, not fan, and the temperature is below room temperature
- Check that the breaker is on and has not tripped
- Clean or remove the indoor filters - clogged filters cause most "weak cooling" complaints
- Make sure the outdoor unit is not buried under debris, curtains or laundry
- Look at the error code display, if the unit has one, and note it down

If the problem persists after these checks, it is time for a professional - electrical faults and refrigerant work should never be DIY.

## Repair or Replace? The Honest Math

A useful rule of thumb used across the HVAC industry: multiply the age of the unit in years by the estimated repair cost. If that exceeds the price of a new unit of the same size, replacement usually wins. Two examples:

- A 3-year-old 1.5HP unit needing a ₦20,000 capacitor: 3 × 20,000 = 60,000, far below a new unit - repair it
- A 9-year-old unit needing a ₦250,000 compressor: 9 × 25,000 = 225,000... approaching the cost of a new, more efficient inverter unit - consider replacing

Also factor in efficiency: a new inverter AC can cut cooling-related electricity costs by 40-60% compared to a tired fixed-speed unit, which changes the math for frequently used rooms.

## How to Choose a Trustworthy AC Technician in Lagos

- Ask for **certifications and experience** with your brand (Samsung, LG, Hisense, Panasonic, Gree, Daikin etc.)
- Insist on a **written quote before work begins**
- Confirm there is a **warranty** - we give 90 days on parts and labour as standard
- Check **Google reviews** from real customers in your area
- Beware of anyone who "tops gas" without leak-testing - it guarantees a repeat visit

## Emergency AC Repair in Lagos Mainland and Ogun State

Moscool Technical Services provides same-day AC repair across Lagos Mainland - Ikeja, Yaba, Surulere, Maryland, Gbagada, Ogba and environs - and across Ogun State including Magboro, Mowe and Ibafo. Our emergency line is open 24/7 for cases like a clinic with medicines to keep cool, a server room, or a home with elderly residents.

Call or WhatsApp **+2349033150460** now for a same-day diagnosis, or send us a message through our contact form and we will respond within 2 hours.''',
    },
    {
        'title': 'Solar Panel Installation in Nigeria: Complete 2026 Cost and Process Guide',
        'slug': 'solar-panel-installation-in-nigeria-cost-and-process-guide',
        'image': IMG.format('photo-1509391366360-2e959784a276'),
        'image_alt': 'Solar panels installed on a residential rooftop in Nigeria',
        'meta_description': 'Solar panel installation in Nigeria: realistic 2026 costs for homes, how the process works step by step, sizing your system, and choosing an installer in Lagos & Ogun State.',
        'content': '''With grid power unreliable and petrol prices volatile, more Nigerian households are choosing solar than ever before. But between inflated quotes, undersized systems and outright fakes, many first-time buyers get burned. This guide gives you realistic 2026 prices, the exact process a proper installer follows, and the questions to ask before you pay anyone a deposit.

## What Does Solar Installation Cost in Nigeria in 2026?

A working solar system has four cost components: panels, inverter, batteries, and balance-of-system (mounting rails, cabling, breakers, protection devices, labour). Realistic installed ranges for Lagos and Ogun State:

- **Small essentials package (1.5kVA):** lights, fans, TV, phones, laptop - ₦1.2m - ₦1.8m with lithium storage
- **Medium family package (3.5kVA):** the above plus a fridge/freezer and small pump - ₦2.5m - ₦4m
- **Large family package (5kVA):** most of a home's daily loads, near-zero generator use - ₦4m - ₦6.5m
- **Panel-only budget systems (lead-acid batteries):** cheaper upfront (₦800k - ₦1.5m for 1.5kVA class) but batteries need replacing every 2-4 years

### Where the money goes

- **Lithium battery bank:** 30-40% of system cost - the heart of the system, never economise here
- **Hybrid inverter:** 15-20% - buy a proven brand with local warranty support
- **Panels:** 20-25% - monocrystalline gives more power per m² on small Lagos roofs
- **Mounting, cabling, protection, labour:** 15-25% - the part bad installers cut corners on

## Sizing: How to Know What You Actually Need

Good installers size systems from a load audit, not guesswork. The process:

- **List every appliance** that must run during outages: watts × hours per day each
- **Sum daily energy needs** in watt-hours (Wh) - this sizes the battery bank
- **Find the peak simultaneous load** in watts - this sizes the inverter
- **Add 25-30% headroom** for surges (fridge compressors, pumps) and future additions

### Sample audit for a typical Lagos family flat

- 8 LED lights × 10W × 5h = 400Wh
- 3 fans × 60W × 8h = 1,440Wh
- 1 fridge/freezer × 150W average × 24h = 3,600Wh
- TV + decoder × 120W × 5h = 600Wh
- Phones, laptop, router × 100W × 6h = 600Wh
- **Total ≈ 6,600Wh/day → a 5kVA inverter + 10kWh lithium bank + 6 × 450W panels covers this with headroom**

## The Installation Process, Step by Step

A professional installation is a project with clear stages - not two men arriving with panels on a bike:

- **1. Site survey:** roof orientation, shading from water tanks and trees, structural condition, DB position
- **2. Load audit and design:** the appliance-by-appliance sizing above, with a written system proposal
- **3. Equipment sourcing:** genuine panels and batteries with verifiable serial numbers and warranties
- **4. Mounting and racking:** aluminium rails fixed structurally, panels south-facing, 9am-4pm sun guaranteed
- **5. DC and AC wiring:** correctly rated solar cable, conduit-protected, labelled
- **6. Protection and changeover:** DC/AC breakers, surge protection, earthing, and a safe changeover switch
- **7. Commissioning and testing:** full load test, charge/discharge verification, app monitoring setup
- **8. Handover:** walkthrough for the household, documentation, warranty cards

Typical timeline: 1 day for a small system, 2-3 days for 3.5-5kVA including commissioning.

## Grid-Tied, Hybrid, or Off-Grid?

- **Hybrid (recommended for Nigeria):** solar first, battery storage, grid or generator as backup - the standard choice
- **Off-grid:** fully independent; makes sense for farms and sites with no grid at all
- **Grid-tied without batteries:** cheapest per watt but does nothing during outages - rarely worth it here without net metering, which Nigeria does not yet offer broadly

## How to Avoid Fake Panels and Bad Installers

Nigeria's market has its share of problems. Protect yourself:

- Buy panels and batteries **with serial numbers you can verify** with the manufacturer
- Be suspicious of quotes far below the ranges above - undersized batteries are the usual trick
- Demand a **written proposal** showing panel count, inverter size and battery capacity in kWh
- Ask which **protection devices** are included - a system without surge protection and earthing is a fire risk
- Check the installer's **reviews and previous installations** - ask to see or visit one
- Get a **warranty in writing**: panels 10-25 years, inverter 3-5 years, lithium 5-10 years, workmanship 1 year

## Maintenance: What Solar Systems Need

- Panels washed every 4-8 weeks (more in harmattan) with water and a soft cloth
- Terminal and connection inspection yearly
- For lead-acid systems: electrolyte checks and equalisation charging
- Monitoring app reviewed monthly to catch falling output early

A well-installed hybrid system is largely hands-off - that is one of its biggest advantages over a generator.

## Ready to Go Solar in Lagos or Ogun State?

Moscool Technical Services designs and installs hybrid solar and inverter systems across Lagos Mainland and Ogun State - from 1.5kVA essentials packages to full 5kVA+ home systems with lithium storage. We start with a **free load audit** and give you a written system design with honest sizing before you commit to anything.

Call or WhatsApp **+2349033150460** to book your free load audit today.''',
    },
    {
        'title': 'Inverter vs Generator: Which Power Backup Is Right for Nigerian Homes?',
        'slug': 'inverter-vs-generator-which-power-backup-is-right-for-nigerian-homes',
        'image': IMG.format('photo-1615873968403-89e068629265'),
        'image_alt': 'Home power inverter system installed in a Nigerian home',
        'meta_description': 'Inverter vs generator for Nigerian homes: true 2026 running costs compared, noise and maintenance, which loads each can carry, and how to choose the right backup power.',
        'content': '''Every Nigerian household eventually faces the same decision: keep paying for generator fuel and servicing, or invest in an inverter system. The right answer depends on your loads, your budget, and how long your typical outages last. This guide compares both honestly - including what generators do better - so you can choose with real numbers.

## The Real Cost of Running a Generator in 2026

Generators look affordable because the cost arrives in small increments: ₦5,000 here, ₦8,000 there. Annualised, the picture changes:

- **Fuel:** a small 2.5kVA petrol generator running 5 hours daily burns roughly ₦350,000 - ₦550,000 of fuel per year at 2026 prices
- **Oil, plugs and filters:** ₦30,000 - ₦60,000 yearly with required 3-weekly oil changes
- **Repairs:** carburettor cleaning, pull-start repairs, armature rewinds - budget ₦40,000 - ₦100,000 yearly for an ageing unit
- **Replacement:** small generators last 3-5 years of daily use before needing replacement

**Total for a small generator, 5 hours daily: roughly ₦450,000 - ₦700,000 every year, forever.**

## The Real Cost of an Inverter System

An inverter system's costs are concentrated upfront, then mostly disappear:

- **1.5kVA system with lithium storage:** ₦1.2m - ₦1.8m installed
- **3.5kVA system:** ₦2.5m - ₦4m installed
- **Running cost:** near zero - it recharges from the grid when available, and from solar panels if you add them
- **Battery replacement:** lithium batteries last 8-15 years; lead-acid need replacing every 2-4 years (factor this in if comparing on price)

**Compare that with generator fuel: a mid-size inverter system typically pays for itself in 3-5 years, then runs free for another 5-10.**

### The noise and fumes factor nobody budgets for

- Generators run 65-75 decibels - like a vacuum cleaner beside your window, all evening
- Inverter systems are **silent** - and produce no exhaust fumes in your compound
- Many Lagos estates and rented compounds now restrict generator hours; nobody restricts an inverter

## What Each One Can Actually Power

### A 2.5-3.5kVA inverter system comfortably runs

- All lights and fans
- TV, decoder, Wi-Fi router, phones and laptops
- Fridge or freezer
- Small water pump (check surge wattage)

### It will NOT run

- Air conditioners for long periods (a 1.5HP AC draws 1,100-1,500W - possible on a 3.5kVA system but it drains storage fast)
- Electric cookers, irons, water heaters (2,000W+ each)
- Heavy pumping machines for extended periods

### Where generators still win

- **Heavy surge loads:** borehole pumps, big freezers, welding equipment
- **Running ACs all night:** only a large (and costly) solar + battery system matches that comfortably
- **Extended cloudy/harmattan periods:** a generator does not care about weather - though hybrid systems with grid charging largely solve this

This is why many homes end up with a **hybrid setup**: inverter for daily loads and quiet nights, small generator (or grid) as backup for heavy loads like pumping.

## Head-to-Head Comparison

- **Cost over 10 years:** inverter wins clearly for light/medium loads; generator wins only if you run heavy AC loads nightly
- **Noise:** inverter (silent) by a wide margin
- **Fumes and safety:** inverter - no carbon monoxide risk indoors
- **Maintenance:** inverter needs almost none; generators demand oil changes and constant attention
- **Fuel availability:** inverters are immune to petrol scarcity and price spikes
- **Heavy loads:** generator still the simpler answer for pumps and all-night AC
- **Resale:** lithium-based inverter systems hold value; small generators are nearly worthless after 4 years

## What We Recommend for Typical Nigerian Homes

- **Flat or small home, mostly lights + fan + TV + fridge:** 1.5-2.5kVA inverter with lithium - silent, cheap to run, pays back in 3-4 years
- **Family home with freezer and pump:** 3.5kVA inverter system, keep the generator for pumping and emergencies only
- **Home running ACs nightly:** 5kVA+ hybrid solar system with lithium storage, or stay on a generator until budget allows - inverter-only without solar will disappoint here

## Common Mistakes to Avoid

- Buying an inverter sized to run everything "just in case" - size for essential loads, add solar later
- Cheap lead-acid batteries that die in 18 months instead of lithium with a real warranty
- No changeover switch - improper changeovers back-feed power and endanger technicians working on the street line
- Skipping surge protection - grid disturbances kill inverters just as they kill generators' AVRs

## Get a Free Load Audit Before You Decide

The honest answer for your home depends on your actual appliances - which is why Moscool Technical Services starts every project with a free load audit, not a sales pitch. We install inverters, hybrid solar systems and changeover setups across Lagos Mainland and Ogun State, and we will tell you frankly if a generator is still the right tool for your situation.

Call or WhatsApp **+2349033150460** to book your free load audit, or read our complete solar installation guide for system sizes and prices.''',
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
        for spec in ARTICLES:
            slug = spec.get('slug') or make_slug(spec['title'])
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
                image_alt=spec['image_alt'],
                category=spec.get('category', 'guides'),
                post_type='article',
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
