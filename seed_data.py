"""Sample content for Moscool Technical Services, seeded automatically on app
startup (see SEED_SAMPLE_CONTENT in app.py / render.yaml) and reusable by the
standalone scripts (scripts/seed_portfolio.py / scripts/seed_articles.py).

Article content uses a small line-prefix markup rendered safely by the
`article_html` filter in app.py:
    '## '  -> <h2>,  '### ' -> <h3>,  '- ' -> <li>,  '**bold**' -> <strong>

Each article also carries FAQs. These are rendered two ways:
  1. JSON-LD FAQPage schema on the article page (rich-snippet eligibility)
  2. A visible "Frequently Asked Questions" section at the end of the article

Images are generic stock placeholders - replace with real project photos via
the admin panel when available.
"""

IMG = 'https://images.unsplash.com/{}?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'

# ---------------------------------------------------------------------------
# Portfolio case studies (fixes the empty "Portfolio (0)" credibility problem)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# SEO articles (content roadmap). week == 1 are the Week-1 priority posts,
# week == 2 are the Month-1 batch.
# ---------------------------------------------------------------------------
ARTICLES = [
    # ------------------------- WEEK 1 -------------------------
    {
        'title': 'AC Repair in Lagos: What to Expect, How Much It Costs, and Who to Call',
        'slug': 'ac-repair-in-lagos-what-to-expect-costs-and-who-to-call',
        'image': IMG.format('photo-1621905251918-48416bd8575a'),
        'image_alt': 'Technician servicing a split air conditioner in Lagos',
        'meta_description': 'AC repair in Lagos explained: common faults, typical repair costs in Naira, how to choose a trustworthy technician, and 24/7 emergency service in Lagos Mainland & Ogun State.',
        'faqs': [
            {'q': 'How much does AC repair cost in Lagos?',
             'a': 'Most common AC repairs in Lagos cost between ₦10,000 and ₦60,000: servicing runs ₦10,000–₦25,000 per unit, refrigerant recharge ₦25,000–₦60,000, and capacitor replacement ₦10,000–₦25,000. A compressor replacement is the big one at ₦120,000–₦350,000 depending on unit size. Insist on a written quote before any work begins.'},
            {'q': 'Why is my AC running but not cooling?',
             'a': 'The most common causes are low refrigerant from a leak, a failed run capacitor, or a dirty condenser coil. A technician should test pressures and capacitor readings before quoting - never accept a "gas top-up" without a leak check, because a sealed system does not consume gas.'},
            {'q': 'How often should an AC be serviced in Nigeria?',
             'a': 'Every 4-6 months for typical home use, and quarterly for units running daily in dusty or coastal areas like Lagos. Harmattan dust clogs condenser coils quickly, so units that skip service are far more likely to suffer compressor failure.'},
            {'q': 'Do you offer emergency AC repair in Lagos Mainland and Ogun State?',
             'a': 'Yes. Moscool Technical Services provides same-day AC repair across Lagos Mainland (Ikeja, Yaba, Surulere, Maryland, Gbagada, Ogba) and Ogun State (Magboro, Mowe, Ibafo), with a 24/7 emergency line on +2349033150460.'},
        ],
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
        'faqs': [
            {'q': 'How much does solar panel installation cost in Nigeria in 2026?',
             'a': 'A 1.5kVA essentials package costs ₦1.2m–₦1.8m installed with lithium storage, a 3.5kVA family system ₦2.5m–₦4m, and a 5kVA whole-home system ₦4m–₦6.5m. Battery quality is where quotes differ most - undersized or fake batteries are the most common way buyers get cheated.'},
            {'q': 'What size solar system do I need for a Nigerian home?',
             'a': 'Size from a load audit, not guesswork: list every appliance with its watts and daily hours, sum the watt-hours to size the battery, and find the peak simultaneous load to size the inverter. A typical Lagos family flat using lights, fans, a fridge and a TV needs roughly 6-7kWh/day - covered by a 5kVA inverter, 10kWh lithium battery and six 450W panels.'},
            {'q': 'How long do solar batteries last in Nigeria?',
             'a': 'Quality lithium batteries last 8-15 years in Nigerian conditions. Lead-acid batteries are cheaper upfront but need replacement every 2-4 years, which usually makes them more expensive over the system\'s life. Always buy batteries with verifiable serial numbers and a written warranty.'},
            {'q': 'How long does installation take?',
             'a': 'One day for a small 1.5kVA system; two to three days for a 3.5-5kVA hybrid system including panel mounting, wiring, protection devices, commissioning and a full load test. A proper installer follows a site survey → load audit → written design → install → commission process.'},
        ],
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
        'faqs': [
            {'q': 'Is an inverter cheaper than a generator in Nigeria?',
             'a': 'Over 10 years, yes for most homes. A small petrol generator running 5 hours daily burns roughly ₦450,000–₦700,000 per year in fuel, oil and repairs. A 1.5–3.5kVA inverter system costs ₦1.2m–₦4m installed once, then runs nearly free - typically paying for itself in 3-5 years.'},
            {'q': 'Can an inverter carry an air conditioner?',
             'a': 'A 3.5kVA inverter can run one 1.5HP AC, but a 1,100-1,500W AC drains battery storage quickly. For all-night AC use you need a 5kVA+ hybrid solar system with substantial lithium storage - or keep the generator for that load. Inverters comfortably carry lights, fans, TVs, routers, laptops and a fridge.'},
            {'q': 'Which lasts longer: inverter batteries or a generator?',
             'a': 'A quality lithium battery bank lasts 8-15 years; a small petrol generator in daily Nigerian use lasts 3-5 years before needing replacement. Lead-acid inverter batteries are the exception at 2-4 years - factor replacement into any price comparison.'},
            {'q': 'Can I keep my generator and add an inverter?',
             'a': 'Yes - that hybrid setup is what we recommend for most homes. The inverter silently carries daily loads (lights, fans, TV, fridge) while the generator handles heavy surge loads like borehole pumps. With a proper changeover switch both work together safely.'},
        ],
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
    # ------------------------- MONTH 1 -------------------------
    {
        'title': 'Book a Refrigerator Repair Technician in Lagos: Same-Day Service Guide',
        'slug': 'book-a-refrigerator-repair-technician-in-lagos-same-day-service',
        'image': IMG.format('photo-1581094794329-c8112a89af12'),
        'image_alt': 'Refrigerator repair technician at work in Lagos',
        'meta_description': 'Need a refrigerator repair technician in Lagos? Signs your fridge needs urgent repair, typical costs, what same-day service covers, and how to protect your food and stock.',
        'faqs': [
            {'q': 'How much does refrigerator repair cost in Lagos?',
             'a': 'Minor repairs (thermostat, door seal, fan motor) run ₦10,000–₦35,000. Refrigerant recharge with leak sealing costs ₦25,000–₦70,000, and compressor replacement ₦90,000–₦250,000 depending on fridge size. Commercial freezers cost more due to larger components.'},
            {'q': 'Is it worth repairing a fridge, or should I buy a new one?',
             'a': 'Use the age-times-cost rule: multiply the fridge\'s age in years by the repair cost. If that approaches the price of a new unit, replace. Repairs under ₦60,000 usually make sense for fridges under 8 years old; a failed compressor on a 10-year-old unit often does not.'},
            {'q': 'How fast can a technician come for an emergency fridge repair?',
             'a': 'Moscool Technical Services offers same-day and 24/7 emergency response across Lagos Mainland and Ogun State - typically attending within 2-4 hours for commercial freezers with stock at risk. Call or WhatsApp +2349033150460.'},
            {'q': 'Why does my fridge run constantly but never get cold?',
             'a': 'Common causes: a failed door gasket letting warm air in, dusty condenser coils, a faulty thermostat, or low refrigerant. Start by cleaning the coils behind the unit and checking the door seal with a paper test - if the paper slides out easily, the gasket needs replacing. Persistent issues need a technician with gauges.'},
        ],
        'content': '''A failed refrigerator is not just an inconvenience - it is spoiled food, lost stock, and in a business, lost customers. Whether it is a family fridge in Surulere or a glass-door showcase freezer in a Yaba supermarket, the first hour of a correct response decides whether this is a small repair or a disaster. Here is how to spot real problems early, what repairs should cost in Lagos, and how to get same-day help.

## Warning Signs Your Fridge or Freezer Needs a Technician

Catch these early and most repairs stay small:

- **Not cooling or cooling weakly** - the classic; often refrigerant, compressor or thermostat related
- **Running nonstop without cycling off** - usually dirty coils, a bad gasket, or low gas; it also doubles your electricity bill
- **Clicking then silence** - the compressor try-to-start cycle: typically a failed relay/overload or a dying compressor
- **Water pooling under or inside the fridge** - blocked defrost drain or a cracked drain pan
- **Ice building up in the fridge compartment** - defrost system failure or door seal leaks
- **Food freezing in the fridge section** - thermostat or air-damper fault
- **Loud humming, rattling or buzzing** - compressor mounts, fan motors, or the beginning of compressor failure

### The 30-second checks before you call

- Listen: is the compressor actually running, or clicking on and off?
- Feel the sides: a fridge working hard is warm to the touch; one that is stone cold and silent is not running at all
- Check the door seal with a sheet of paper - if it slides out easily, cold air is leaking out
- Vacuum the condenser coils behind or beneath the unit; dust is the #1 fridge killer in Lagos

## What Refrigerator Repair Costs in Lagos (2026)

- **Diagnostic / call-out:** ₦5,000 - ₦15,000
- **Thermostat replacement:** ₦10,000 - ₦30,000
- **Door gasket replacement:** ₦10,000 - ₦25,000
- **Fan motor:** ₦15,000 - ₦35,000
- **Refrigerant recharge + leak repair:** ₦25,000 - ₦70,000
- **Compressor replacement (domestic):** ₦90,000 - ₦250,000
- **Commercial showcase freezer compressor:** ₦150,000 - ₦400,000

### Repair or replace: the honest rule

Multiply the fridge's age in years by the quoted repair cost. If the result approaches the price of a new unit of similar size, replacement usually wins. A 4-year-old fridge needing a ₦40,000 thermostat? Repair. A 10-year-old fridge needing a ₦200,000 compressor? Start shopping - and consider a new inverter fridge that sips power.

## What Same-Day Commercial Refrigeration Service Covers

For shops, restaurants and pharmacies, downtime is measured in naira per hour. A proper commercial response includes:

- Priority dispatch - our commercial calls jump the queue, typically on-site within 2-4 hours
- Full electrical diagnostics before any parts are replaced
- Compressor replacement with correctly matched units, not "closest fit" shortcuts
- Temperature verification with a pull-down log before handover - the freezer must hold -18°C, not "feel cold"
- Preventive maintenance scheduling for the rest of your units so the next failure never surprises you

## Why "Gas Filling" Without Leak Testing Is a Scam

The most common fridge scam in Lagos: a technician "tops the gas" every few months and charges you each time. A refrigeration circuit is a sealed system - refrigerant does not get consumed. If a system is low on gas, it has a leak, and topping up without finding and sealing the leak guarantees a repeat visit and another invoice. Insist on leak detection, repair, vacuum, and then a weighed-in charge.

## How to Protect Food During a Fridge Breakdown

- Keep the doors closed - a closed fridge holds a safe temperature for about 4 hours, a full freezer about 48
- Move high-value items (meat, fish, medicines) to a neighbour's unit or a backup freezer early, not at hour 40
- For businesses: note the time temperature left the safe zone; discard perishables held above 5°C for more than 4 hours
- Do not restock a repaired fridge until it has held temperature through one full cycle

## Same-Day Refrigerator Repair in Lagos Mainland and Ogun State

Moscool Technical Services repairs fridges, freezers, chillers, display cases and cold rooms across Lagos Mainland - Ikeja, Yaba, Surulere, Maryland, Gbagada, Ogba - and Ogun State including Magboro, Mowe and Ibafo. Domestic or commercial, our emergency line runs 24/7, we quote in writing before work starts, and we give 90 days warranty on parts and labour.

Call or WhatsApp **+2349033150460** now - for commercial freezers with stock at risk, say so on the call and you jump the queue.''',
    },
    {
        'title': 'How to Know When Your Home Inverter Battery Needs Replacing',
        'slug': 'how-to-know-when-your-home-inverter-battery-needs-replacing',
        'image': IMG.format('photo-1558618666-fcd25c85cd64'),
        'image_alt': 'Inverter battery bank installed in a Nigerian home',
        'meta_description': 'Signs your inverter battery is failing: shorter backup times, swelling, slow charging. Test methods, lithium vs lead-acid replacement costs in Nigeria, and safe disposal.',
        'faqs': [
            {'q': 'How long do inverter batteries last in Nigeria?',
             'a': 'Lithium batteries last 8-15 years; tubular lead-acid batteries 3-5 years with good maintenance; cheap flat-plate lead-acid often just 12-24 months. Nigeria\'s heat shortens all battery life - a battery in a 35°C room ages much faster than one in a cool, ventilated space.'},
            {'q': 'What are the signs a battery needs replacing?',
             'a': 'Backup time dropping well below what it used to be is the clearest sign - if your load runs 2 hours instead of 6, the battery capacity has collapsed. Also watch for the battery swelling, taking far longer to charge than before, needing frequent water top-ups (flooded types), or the inverter showing low-battery alarms almost immediately after a full charge.'},
            {'q': 'Can I replace just one battery in a bank of two or four?',
             'a': 'It is possible but usually a false economy: a new battery paired with old ones means the old batteries drag the new one down and the bank fails unevenly. Replace the whole bank, or test each battery individually and replace only if the others still test at 80%+ of rated capacity.'},
            {'q': 'Should I upgrade to lithium when replacing?',
             'a': 'Usually yes if budget allows: lithium lasts 2-3 times longer than tubular lead-acid, needs zero water maintenance, charges faster, and delivers more usable capacity from the same rated size. The upfront cost is higher (₦600k-₦2m+ depending on capacity), but the cost per year of service is typically lower.'},
        ],
        'content': '''An inverter battery never fails suddenly - it fades, and most owners only notice when the lights go out an hour earlier than usual. Learning to read the warning signs saves you from being stranded mid-outage and from the domino damage a dying battery can do to a whole bank. Here is how to test, when to replace, and what the smart options cost in Nigeria.

## The Clear Signs Your Battery Is Failing

- **Backup time has collapsed** - your usual load now runs 2 hours instead of 6. Capacity loss is the defining symptom of battery ageing
- **It takes much longer to charge** - worn plates accept charge slowly; a battery that used to fill in 6 hours now needs 10+
- **Low-battery alarm almost immediately** after showing full - surface charge masks a battery that cannot deliver under load
- **Visible swelling or a bulging case** - internal plate damage; stop using it, this one is a safety issue
- **Constant water loss** (flooded lead-acid) - gassing hard after every charge cycle
- **Corroded, heat-discoloured terminals** - resistance rises, everything downstream suffers
- **A rotten-egg smell** near the bank - over-gassing or internal fault; ventilate and get it checked

### The one test that settles it

Run your normal evening load on battery only and time it. Compare against what the same load delivered when the system was new (or against the installer's design estimate). If you are getting less than half the expected runtime, the bank's usable capacity is gone - no additive, "battery optimizer" or magic trick brings plate material back.

For a precise answer, ask a technician to load-test each battery: any unit delivering under 80% of its rated capacity is due for retirement.

## Why Batteries Die Faster in Nigeria

- **Heat:** every 8-10°C above 25°C roughly halves battery life - and Nigerian battery rooms routinely hit 35°C+
- **Deep daily cycling:** outages mean most Nigerian batteries work hard every single day, not occasionally
- **Chronic undercharging:** if grid supply is short, the bank starts each night partially charged, which sulphates lead-acid plates permanently
- **Cheap batteries sold as premium:** the market is flooded with rebranded flat-plate batteries; buy on verifiable serial numbers, not box art
- **Water neglect:** flooded batteries that go dry get permanently damaged within a few cycles

## Lithium vs Tubular Lead-Acid: The Replacement Decision

- **Lithium (LiFePO4):** 8-15 year life, zero maintenance, 90%+ usable capacity, fast charging, built-in management system. Costs more upfront: roughly ₦600k - ₦2m+ for home sizes (5-10kWh)
- **Tubular lead-acid:** 3-5 year life with care, only ~50% of rated capacity is usable, needs monthly water checks. Cheaper to buy: ₦250k - ₦600k per battery
- **The maths:** two or three tubular replacements over a decade usually cost more than one lithium bank that spans the whole decade - and lithium delivers more usable energy per rated kWh

When replacing, also check the inverter's charge profile: lithium batteries need a compatible charger or an inverter with a selectable lithium mode. We check this during every replacement survey.

## Safe Disposal: Never Throw Old Batteries in the Trash

Lead-acid batteries are hazardous waste - the lead and acid are toxic, and dumping them poisons soil and water. They do, however, have real scrap value (₦15,000 - ₦40,000+ per battery, weight dependent), which is why battery traders will collect from your door. Hand old batteries to your installer for trade-in credit, or sell to a licensed recycler. Lithium batteries should be returned through the supplier or manufacturer recycling channel.

## Getting the Most from Your New Bank

- Give the bank breathing room: ventilated, shaded, off the floor - heat is the #1 killer
- Right-size charging: the bank must fully recharge between outages; chronically short grid supply means you need more charging hours or solar
- Monthly checks for flooded batteries: water level, terminal tightness, no corrosion
- Keep the load honest: adding a freezer or AC to a bank sized for lights ages it overnight - re-audit loads when your usage changes

## Free Battery Health Check in Lagos Mainland and Ogun State

Not sure whether you need one battery or a whole new bank - or whether to go lithium? Moscool Technical Services offers a free battery health check: we load-test each unit, check your inverter's charging profile, and give you a written recommendation with honest options. We replace and upgrade banks across Lagos Mainland and Ogun State.

Call or WhatsApp **+2349033150460** to book your free check, or read our inverter vs generator guide for the bigger picture on backup power.''',
    },
    {
        'title': 'HVAC Maintenance Contracts for Businesses in Nigeria: What\'s Included and Why You Need One',
        'slug': 'hvac-maintenance-contracts-for-businesses-in-nigeria-whats-included',
        'image': IMG.format('photo-1620714223084-8fcacc6dfd8d'),
        'image_alt': 'HVAC technician maintaining commercial air conditioning units',
        'meta_description': 'HVAC maintenance contracts for Nigerian businesses: what a good contract includes, realistic pricing, quarterly vs monthly plans, and how preventive maintenance beats emergency repairs.',
        'faqs': [
            {'q': 'What does an HVAC maintenance contract include?',
             'a': 'A good contract covers scheduled service visits (filter and coil cleaning, drain flushing, refrigerant and electrical checks), priority emergency response with reduced or waived call-out fees, written reports after every visit, and discount pricing on parts and repairs. Exact scope varies - insist on a written checklist of what each visit includes.'},
            {'q': 'How much does a maintenance contract cost in Nigeria?',
             'a': 'For a typical small business with 5-10 AC units, quarterly plans run roughly ₦150,000-₦400,000 per year and monthly plans ₦400,000-₦1m+. Cost scales with unit count, unit types (splits vs cassettes vs VRF), and response-time guarantees. Compare contracts on what is included, not just price.'},
            {'q': 'How often should commercial AC units be serviced in Nigeria?',
             'a': 'Quarterly at minimum for standard split units; monthly for high-usage sites like restaurants, hotels and clinics, and for units exposed to dust or kitchen grease. Lagos harmattan dust and coastal humidity clog coils fast - skipped servicing is the leading cause of compressor failure we see.'},
            {'q': 'Is a maintenance contract cheaper than pay-as-you-go repairs?',
             'a': 'For any business with more than a handful of units, yes. Preventive maintenance keeps units efficient (lower electricity bills), catches faults before they become compressor replacements, and contracts typically price visits below one-off call-out rates. One avoided compressor replacement can pay for most of a year\'s contract.'},
        ],
        'content': '''If your business runs air conditioning - a restaurant, clinic, office, supermarket or hotel - you already know the pattern: everything works until the hottest day of the year, then three units fail in the same week, and you pay emergency rates to keep customers and staff comfortable. An HVAC maintenance contract exists to break that pattern. Here is what a good one includes, what it should cost in Nigeria, and how to tell a real maintenance plan from a marketing gimmick.

## What a Proper HVAC Maintenance Contract Includes

### Scheduled preventive visits (the core)

Each scheduled visit should follow a written checklist, not "look around and leave". Per unit, expect:

- Filter cleaning or replacement
- Evaporator and condenser coil cleaning
- Condensate drain flush (the #1 cause of water drips and ceiling stains)
- Refrigerant pressure check against specification
- Electrical checks: current draw, capacitor readings, contactor condition
- Fan motor and blower inspection
- Thermostat and control checks
- Written report per visit, per unit

### Beyond the visits

- **Priority emergency response:** contract customers jump the queue - hours matter when a freezer is warming up
- **Reduced or waived call-out fees** on emergency call-outs
- **Discounted repairs and parts:** typically 10-20% off list prices
- **Asset register:** a log of every unit - model, serial, service history - so faults are diagnosed faster and warranty claims are documented
- **Seasonal readiness:** pre-harmattan and peak-heat inspections timed before the stress seasons

### What should NOT be in the contract

- "Any repair needed is free" - repairs on failed parts are normally quoted separately, at discounted rates; contracts covering unlimited free repairs are either very expensive or will not be honoured
- Vague scope like "general servicing" with no checklist
- No reporting - if you do not get written records, you cannot verify the work happened

## How Much Should a Contract Cost in Nigeria?

Realistic 2026 ranges for Lagos and Ogun State, assuming standard split units:

- **Quarterly plan (4 visits/year):** roughly ₦15,000 - ₦40,000 per unit per year - a 10-unit office pays about ₦150,000 - ₦400,000 annually
- **Monthly plan (12 visits/year):** roughly ₦40,000 - ₦100,000 per unit per year - justified for restaurants, clinics, server rooms and high-traffic sites
- **Cassette, ducted and VRF systems:** price per unit is higher due to complexity and access equipment

Get itemised quotes from at least two providers and compare the checklist each includes - a cheap contract that skips electrical checks is paying for half a service.

## Quarterly vs Monthly: Which Does Your Business Need?

- **Quarterly** suits offices, shops and clinics with standard splits in reasonable environments
- **Monthly** suits sites where cooling failure costs money by the hour: restaurants (kitchen heat + customer comfort), pharmacies (stock), server rooms, hotels, and any unit exposed to grease or heavy dust
- **Commercial refrigeration** (freezers, chillers, cold rooms) should be on monthly checks regardless - the cost of one failed compressor and lost stock exceeds years of maintenance

## The Economics: Why Contracts Beat Emergency Repairs

- **Efficiency savings:** a dirty coil can raise AC power consumption 20-30%. On a site spending ₦500k monthly on cooling electricity, a contract that keeps coils clean can save more than the contract costs
- **Avoided capital failures:** compressors rarely die suddenly - they die from years of overheating on clogged coils and low gas. Preventive maintenance is how units reach 10-12 years instead of 5-6
- **Predictable budgeting:** a fixed annual figure replaces surprise ₦200,000 compressor invoices and emergency weekend rates
- **One accountable partner:** with a contract, one company is responsible for uptime - no more calling three different technicians who each blame the last one's work

### The rule of thumb

If your site has more than about five AC units, or any commercial refrigeration, a contract is almost always cheaper than reactive repairs over a 12-month window.

## How to Choose a Maintenance Partner

- Ask for the **written visit checklist** and a sample report
- Confirm **response-time guarantees**: e.g. emergency attendance within 4-6 working hours
- Check they service your equipment types (splits, cassettes, ducted, VRF, cold rooms)
- Verify technicians are trained on your brands and carry proper gauges and electrical test equipment - not just a ladder and a brush
- Look for **reviews and references** from businesses like yours
- Insist on a contract document stating scope, visit frequency, response times, parts pricing discounts, and termination terms

## Our Maintenance Plans

Moscool Technical Services offers quarterly and monthly HVAC maintenance plans for businesses across Lagos Mainland and Ogun State - offices, restaurants, clinics, shops and cold-room operators. Every plan includes written per-unit reports, priority 24/7 emergency response, and discounted repairs. We start with a free site survey: we count and assess your units, then quote a plan sized to your actual equipment.

Call or WhatsApp **+2349033150460** to book a free site survey, or read our guide on what AC repair should cost in Lagos to see what reactive maintenance is really costing you.''',
    },
]
