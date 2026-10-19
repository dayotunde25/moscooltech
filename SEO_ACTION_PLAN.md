# SEO Action Plan — Moscool Technical Services

Based on the SEO review of `https://moscooltech.onrender.com` (score 50–52/100) and the
changes made to this codebase. Work top to bottom: the first two sections are what
actually moves rankings for a local service business.

---

## 1. Fixed in this pass (code)

| Audit finding | What changed |
| --- | --- |
| Title tag too long (69 chars) | Home title is now 56 chars: `AC Repair, Solar & Refrigeration in Lagos \| Moscool Tech`. Marketplace and post titles are trimmed to ≤60 rendered characters. |
| Heading structure — first heading H5, 5 skipped levels | Offcanvas menu title is no longer a heading. Homepage sections now run H1 → H2 → H3, card titles are H3, footer uses H2/H3. Verified on `/`, `/guides`, `/marketplace`, `/post/<id>`. |
| Thin content | Added a ~450-word service-areas/expertise section and a 4-question FAQ to the homepage (homepage text is now ~1,300 words). Added an indexable `/guides` hub page. |
| Missing favicon | Added `static/img/favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` and the correct `<link>` tags. |
| Missing explicit image dimensions | All `<img>` tags now have `width`/`height` (plus `loading="lazy"` below the fold and `fetchpriority="high"` on the hero). |
| Render-blocking resources | Font Awesome CSS now loads non-blocking (`media="print"` swapped by `main.js`), CDNs are preconnected, and the hero image is preloaded. Bootstrap stays blocking (removing it causes an unstyled flash). |
| Too many inline styles | Repeated image/line-height styles moved to `.card-img-cover*`, `.post-media`, `.post-body-text` in `style.css`. One inline style remains (the hidden marketplace tab, toggled by JS). |
| No analytics | GA4 is wired up and only renders when `GA_MEASUREMENT_ID` is set. CSP updated to allow Google Tag Manager/Analytics. |
| No llms.txt | `/llms.txt` now serves a structured summary (services, service areas, contact, guides) for AI search engines. |
| Sitemap/robots | `/guides` added to both. Sitemap `lastmod` now reflects real content dates instead of "today" on every request. |
| Schema | LocalBusiness now includes phone/email from config, logo, image, service catalog, and conditional street address. Article pages add `author`, `publisher`, `image` and a `BreadcrumbList`. `twitter:title`/`twitter:description` now match the page. |
| Address & phone not detected | Phone is now written in standard international format (`+234 903 315 0460`) and is a clickable `tel:` link in the header, footer and contact cards. The street address is now configurable — see section 2. |
| No internal linking hub | Nav + footer link to `/guides`; homepage content and guides link back to each other. |

Run the tests after any change: `python -m pytest -q` (18 passing).

### Environment variables to set (Render → Environment)

```
SITE_URL=https://moscooltech.com      # canonical + sitemap host — IMPORTANT
BUSINESS_ADDRESS=12 Example Street, Ikeja, Lagos
BUSINESS_PHONE=+2349033150460
BUSINESS_EMAIL=dayotunde25@gmail.com
GA_MEASUREMENT_ID=G-XXXXXXXXXX        # from analytics.google.com
GOOGLE_REVIEW_URL=https://g.page/r/XXXX/review
```

`SITE_URL` matters more than it looks: without it, canonicals, Open Graph URLs and the
sitemap all use whatever host the request came in on. If Google discovers
`moscooltech.onrender.com`, you can end up with two competing copies of the site.

---

## 2. Local SEO — the biggest quick win

The audit could not identify a business address, and only one referring domain exists.
For "AC repair in Lagos"-style searches, Google leans heavily on the local pack, which is
driven by Google Business Profile, not by the website alone.

1. **Complete the Google Business Profile** — follow `GOOGLE_BUSINESS_PROFILE_CHECKLIST.md`.
   Primary category: *Air conditioning repair service*. Add refrigeration, solar, electrician.
   Add the same street address that is now published on the site:
   **16, Oredegbe Street, Off Ogundele Street, Agbado Station, Ifo, Ogun State**.
2. **Keep NAP identical everywhere** — the site now shows the Agbado Station address in the
   footer, contact section and LocalBusiness schema (with a Get Directions link). Google
   compares name + address + phone character-for-character across the site, GBP and directories.
3. **Add a real domain and redirect the Render subdomain.** See section 2b. In Cloudflare,
   add a rule: `moscooltech.onrender.com/*` → `https://yourdomain/$1` (301). The site's
   canonical tags already point at `SITE_URL`, but a 301 removes the duplicate host entirely.
   Multiple redirects were flagged at 0.63 s — this also fixes that.
4. **Reviews:** ask every completed job for a review via the GBP review link. Ten recent
   reviews with the service named ("fixed my freezer in Ikeja") outperform most on-page work.
5. **Local citations** — identical NAP on: Bing Places, Apple Business Connect, Facebook Page,
   Instagram, LinkedIn company page, VConnect, BusinessList.com.ng, Finelib, NgEX.
   These are also your first legitimate backlinks.

---

## 2b. Domain name: free vs paid

There is no reliable **free second-level domain** in 2026. Freenom (`.tk`, `.ml`, `.ga`,
`.cf`, `.gq`) lost its ICANN accreditation after 2024 and its domains stopped resolving,
which is why no credible registrar advertises free TLDs any more.

Free options that still exist, and what they are actually good for:

| Option | Cost | Verdict for a business |
| --- | --- | --- |
| `moscooltech.onrender.com` | Free | Works today, but weak trust signal and tied to a hosting brand. Keep it as a staging/preview URL. |
| `yourname.is-a.dev` | Free (GitHub PR) | Free subdomain, Render has an official guide. Fine as a placeholder, not for the GBP/website of record. (`moscooltech.is-a.dev` already resolves to another owner.) |
| `yourname.eu.org` | Free (EU.org, approval can take days/weeks) | Same trade-off, slower setup. |
| `duckdns.org` / FreeDNS | Free | Dynamic-DNS tools, not business addresses. |

Recommended paid options (a domain is the cheapest SEO asset you will ever buy):

- **`.com.ng` for a Nigerian business** — around ₦2,000–8,000/year from NiRA-accredited
  registrars (WhoGoHost, Qservers, DomainKing, Modewebhost). Often on promo around ₦3,000.
  Signals local relevance and is cheap enough to hold for years.
- **`.com`** — roughly $10–12 first year, renewing around $15–20 (Namecheap, Porkbun,
  Cloudflare Registrar). Choose this if you want to look national/international.

Checked on 19 Oct 2026: **`moscooltech.com` and `moscooltechservices.com` are unregistered**
(Verisign RDAP returns 404). `moscooltech.com.ng` and `moscool.ng` had no DNS records —
confirm availability at a NiRA registrar. Prefer a name you can also use for email
(`hello@moscooltech.com`) so email, GBP and the website all match.

After registering: add the domain in Render → Settings → Custom Domains, point DNS at
Render, set `SITE_URL` to the chosen domain, then add the 301 from the onrender host.

---

## 3. Email authentication (SPF + DMARC)

These are DNS records, not code, and the report is right that they are missing. They
affect deliverability and spoofing, and they are quick to fix — but they only make sense
for a domain you actually send mail from. The site currently publishes a Gmail address.

Recommended: move to a domain mailbox (`hello@moscooltech.com`) via Google Workspace or
Zoho Mail, then add:

```
# SPF (TXT on @)
v=spf1 include:_spf.google.com ~all

# DMARC (TXT on _dmarc)
v=DMARC1; p=none; rua=mailto:dmarc@moscooltech.com; adkim=r; aspf=r
```

Start at `p=none`, watch the reports for 2–4 weeks, then move to `p=quarantine` and
`p=reject`. If you keep using Gmail for business, the records still help stop spoofing of
the domain, but they do not make Gmail look like a branded sender.

---

## 4. Link building (the audit's only HIGH priority)

You have 1 backlink from 1 domain (`indexyour.link`, a directory). This is the main reason
a well-optimised page still will not outrank established competitors. Links must be earned
from real sites — bought link packages are a fast way to get penalised.

Do these in order:

1. **Directories and citations** (10–20 links): Bing Places, Apple Maps, VConnect,
   BusinessList.com.ng, Finelib, NgEX, Yellow Pages Nigeria, plus any Ikeja/Ogun community
   business listings. Free, relevant, and they reinforce NAP.
2. **Supplier and brand pages.** LG, Samsung, Hisense, Gree and Daikin publish "find an
   installer" lists. Being listed is a strong, relevant link and sends customers.
3. **Property and facilities managers.** Estate associations, facility-management firms and
   serviced-apartment operators in Lekki/Ikeja often link to trusted vendors. Offer a free
   maintenance check for their building in exchange for a vendor listing.
4. **Local media and blogs.** Pitch a short expert piece to Lagos lifestyle/property blogs:
   "what AC servicing should cost in 2026", "solar vs generator for a Lagos flat". Link back
   to the matching guide.
5. **Be the source.** Publish one original data piece per quarter (e.g. "what 100 Lagos AC
   repairs actually cost"), then tell journalists and forum moderators about it.
6. **Answer where people ask.** Nairaland, Reddit r/Nigeria, Facebook groups — answer the
   question fully, link only when it genuinely helps. No drive-by link drops.

Track referring domains monthly in Search Console (Links report) or Ahrefs' free checker.

---

## 5. Content plan

The six seeded articles are a good foundation (AC repair, solar, inverter vs generator,
fridge repair, inverter batteries, HVAC contracts). Build topic clusters around them, and
link every article to at least two others plus the relevant service section on the homepage.

**Cluster A — AC (highest commercial intent)**
- Cost of installing a split AC in Lagos (by HP)
- Why your AC trips the breaker (and when to stop resetting it)
- Inverter AC vs fixed-speed: real electricity savings in Nigeria
- AC servicing schedule for offices and short-lets

**Cluster B — Refrigeration (commercial money)**
- Cold room setup cost for a small food business
- Why a freezer runs but does not freeze
- Display chiller maintenance for supermarkets

**Cluster C — Solar/inverter**
- How many panels for a 1.5kVA / 3.5kVA / 5kVA system
- Lithium vs tubular batteries: 10-year cost
- What to check before accepting a solar quote

**Rules that matter more than volume**
- One article every 2 weeks beats six in one week and then silence.
- Every article: a specific title with the city, a 150–160 char meta description (already
  enforced in the admin form), real Naira figures, and an FAQ block (the template emits
  `FAQPage` schema automatically for seeded guides).
- Refresh the pricing articles every 6 months and update `dateModified` — Google rewards
  maintained pages.
- Keep the news section as freshness signal only; it links off-site and does not build
  topical authority on its own.

---

## 6. Remaining technical items (low priority, worth knowing)

- **Mobile PageSpeed** (FCP 3.5 s from a US test server): biggest remaining cost is
  Bootstrap CSS. Self-hosting Bootstrap + a small critical-CSS inline block would cut
  ~200 KB and one CDN round-trip; do it only if you can test the layout after.
- **Hreflang** — ignore. You serve one language in one country; hreflang adds nothing.
- **Facebook Pixel** — add only if you actually run Meta ads.
- **YouTube** — create a channel with short repair clips and link it in the footer. Video
  results take SERP space and give you another profile to rank.
- **Plain-text email** — the audit flags scraping risk. Obfuscating it hurts real customers
  and screen readers; the contact form is the mitigation. Keep the email visible.
- **Core Web Vitals** — "insufficient real-world data" just means low traffic. It resolves
  as traffic grows; no action needed.

---

## 7. Measurement

1. Set `GA_MEASUREMENT_ID`, then link GA4 to **Google Search Console**.
2. Verify both `https://moscooltech.com` and the Render host in Search Console; submit
   `https://moscooltech.com/sitemap.xml`.
3. Watch four numbers monthly: impressions, average position for "AC repair Lagos" and
   "solar installation Lagos", GBP calls/direction requests, and referring domains.
4. Add UTM tags to GBP and social links so leads can be attributed.
