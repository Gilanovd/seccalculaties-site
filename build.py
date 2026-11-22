#!/usr/bin/env python3
"""Bouwt de statische website van SEC Calculaties naar de map ./public.

Geen extra pakketten nodig: alleen Python 3.8+.
  python build.py

Cloudflare Pages-instellingen:
  Build command:          python3 build.py
  Build output directory: public

Codes voor Google Tag Manager en Search Console staan in site.config.json.
"""
import datetime
import html
import json
import os
import re
import shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "public")

with open(os.path.join(ROOT, "site.config.json"), encoding="utf-8") as f:
    CONFIG = json.load(f)

BASE = CONFIG.get("base_url", "https://seccalculaties.nl").rstrip("/")
GTM = (CONFIG.get("google_tag_manager_id") or "").strip()
GSC = (CONFIG.get("google_search_console_verification") or "").strip()
# Op het GitHub Pages-testadres (gebruikersnaam.github.io/repo) staat de site in een submap.
# De workflow geeft die submap door; met een eigen domein is hij leeg.
PREFIX = os.environ.get("SITE_PATH_PREFIX", CONFIG.get("path_prefix", "")).rstrip("/")
# Testadres nooit laten indexeren: de workflow zet SITE_NOINDEX=true zolang er geen eigen domein is.
NOINDEX = bool(CONFIG.get("noindex")) or os.environ.get("SITE_NOINDEX", "").lower() == "true"
TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------- bedrijfsgegevens
BIZ = {
    "name": "SEC Calculaties",
    "phone_display": "06 24 19 62 13",
    "phone_e164": "+31624196213",
    "email": "info@seccalculaties.nl",
    "street": "Thomas Edisonweg 25",
    "postcode": "5151 DH",
    "city": "Drunen",
    "kvk": "78318440",
    "btw": "NL861344868B01",
    "btw_display": "NL8613.44.868.B01",
    "lat": 51.6938524,
    "lng": 5.1590914,
    "maps": "https://www.google.com/maps/place/SEC+Calculaties/@51.6938524,5.1590914,15z",
}
TEL = "tel:" + BIZ["phone_e164"]
MAIL = "mailto:" + BIZ["email"]
MAIL_REQUEST = MAIL + "?subject=" + quote("Calculatie-aanvraag") + "&body=" + quote(
    "Beste SEC Calculaties,\n\n"
    "Graag ontvangen wij een calculatie voor het volgende project:\n\n"
    "Projectnaam en plaats:\n"
    "Wat moet er gecalculeerd worden (wanden, plafonds, overig):\n"
    "Gewenste datum calculatie gereed:\n"
    "Bijlagen: bestek en tekeningen\n\n"
    "Met vriendelijke groet,\n\n"
    "Naam:\nBedrijf:\nTelefoon:\n"
)

# ---------------------------------------------------------------- iconen (inline SVG)
def svg(path, stroke=True):
    attrs = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"' if stroke else 'fill="currentColor"'
    return f'<svg viewBox="0 0 24 24" {attrs} aria-hidden="true" focusable="false">{path}</svg>'

I = {
    "phone": svg('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>'),
    "mail": svg('<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>'),
    "send": svg('<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>'),
    "check": svg('<path d="M20 6 9 17l-5-5"/>'),
    "ruler": svg('<path d="M21.3 15.3 8.7 2.7a1 1 0 0 0-1.4 0L2.7 7.3a1 1 0 0 0 0 1.4l12.6 12.6a1 1 0 0 0 1.4 0l4.6-4.6a1 1 0 0 0 0-1.4z"/><path d="m7.5 10.5 2-2M10.5 13.5l2-2M13.5 16.5l2-2"/>'),
    "layers": svg('<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>'),
    "shield": svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>'),
    "cart": svg('<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6"/>'),
    "calc": svg('<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01M8 19h8"/>'),
    "clock": svg('<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'),
    "map": svg('<path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>'),
    "menu": svg('<path d="M3 6h18M3 12h18M3 18h18"/>'),
}

# ---------------------------------------------------------------- navigatie
NAV = [
    ("/diensten/", "Diensten"),
    ("/metal-stud-calculatie/", "Metal stud calculatie"),
    ("/afbouwcalculatie-uitbesteden/", "Uitbesteden"),
    ("/over-ons/", "Over ons"),
    ("/contact/", "Contact"),
]

SERVICES = [
    {
        "url": "/metal-stud-calculatie/",
        "title": "Metal stud calculatie",
        "icon": "calc",
        "text": "Materiaal en uren voor metal stud wanden en plafonds, berekend op basis van bestek en tekeningen.",
    },
    {
        "url": "/hoeveelheden-uittrekken/",
        "title": "Hoeveelheden uittrekken",
        "icon": "ruler",
        "text": "Nauwkeurige hoeveelheden, zo aangeleverd dat u ze direct in uw eigen systeem verwerkt.",
    },
    {
        "url": "/advies-brand-geluid-stabiliteit/",
        "title": "Advies en alternatieven",
        "icon": "shield",
        "text": "Advies over brandwerendheid, geluid en stabiliteit, en slimme alternatieven die kosten besparen.",
    },
    {
        "url": "/offertes-en-inkoop/",
        "title": "Offertes en inkoop",
        "icon": "cart",
        "text": "Offertes op basis van uw inkoopgegevens. Desgewenst verzorgen wij ook de inkoop van materialen.",
    },
]


def esc(s):
    return html.escape(s, quote=True)


def org_schema():
    return {
        "@type": "ProfessionalService",
        "@id": BASE + "/#organisatie",
        "name": BIZ["name"],
        "url": BASE + "/",
        "logo": BASE + "/assets/img/logo.png",
        "image": BASE + "/assets/img/og-image.jpg",
        "description": "Calculatiebureau voor de droge afbouw: hoeveelheden en begrotingen voor metal stud wanden en plafonds.",
        "telephone": BIZ["phone_e164"],
        "email": BIZ["email"],
        "vatID": BIZ["btw"],
        "identifier": {"@type": "PropertyValue", "propertyID": "KvK", "value": BIZ["kvk"]},
        "foundingDate": "2020",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": BIZ["street"],
            "postalCode": BIZ["postcode"],
            "addressLocality": BIZ["city"],
            "addressRegion": "Noord-Brabant",
            "addressCountry": "NL",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": BIZ["lat"], "longitude": BIZ["lng"]},
        "areaServed": {"@type": "Country", "name": "Nederland"},
        "knowsAbout": [
            "afbouwcalculatie", "droge afbouw", "metal stud wanden", "metal stud plafonds",
            "hoeveelheden uittrekken", "begroting afbouw", "brandwerendheid", "akoestiek",
        ],
        "hasMap": BIZ["maps"],
    }


def breadcrumb_schema(trail):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": BASE + url}
            for i, (url, name) in enumerate(trail)
        ],
    }


def faq_schema(faqs):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }


def service_schema(name, desc, url):
    return {
        "@type": "Service",
        "name": name,
        "description": desc,
        "url": BASE + url,
        "serviceType": name,
        "provider": {"@id": BASE + "/#organisatie"},
        "areaServed": {"@type": "Country", "name": "Nederland"},
        "audience": {"@type": "BusinessAudience", "audienceType": "Afbouwbedrijven en aannemers"},
    }


# ---------------------------------------------------------------- bouwstenen
def faq_html(faqs, heading="Veelgestelde vragen"):
    items = "".join(
        f'<details><summary>{esc(q)}</summary><div class="answer"><p>{esc(a)}</p></div></details>'
        for q, a in faqs
    )
    return f'''<section class="section section--paper" aria-labelledby="faq-titel">
  <div class="wrap">
    <div class="section-head center"><span class="eyebrow">Vragen</span><h2 id="faq-titel">{esc(heading)}</h2></div>
    <div class="faq">{items}</div>
  </div>
</section>'''


def cta_html(title="Project op de planning?", text="Stuur uw bestek en tekeningen. Wij laten snel weten wat we voor u kunnen doen."):
    return f'''<section class="cta" aria-label="Neem contact op">
  <div class="wrap">
    <div><h2>{esc(title)}</h2><p>{esc(text)}</p></div>
    <div class="btn-row">
      <a class="btn btn--dark" href="{esc(MAIL_REQUEST)}">{I["send"]}Stuur uw tekeningen</a>
      <a class="btn btn--outline" href="{TEL}">{I["phone"]}Bel {BIZ["phone_display"]}</a>
    </div>
  </div>
</section>'''


def aside_html(title="Calculatie nodig?"):
    return f'''<aside class="aside" aria-label="Direct contact">
  <p class="aside-title">{esc(title)}</p>
  <p>Mail uw bestek en tekeningen of bel ons direct. Wij denken graag mee over de aanpak van uw project.</p>
  <a class="btn btn--gold" href="{esc(MAIL_REQUEST)}">{I["send"]}Stuur uw tekeningen</a>
  <a class="btn btn--ghost" href="{TEL}">{I["phone"]}{BIZ["phone_display"]}</a>
  <a class="btn btn--ghost" href="{MAIL}">{I["mail"]}{BIZ["email"]}</a>
</aside>'''


def page_hero(trail, eyebrow, h1, lead):
    crumbs = "".join(
        (f'<li><a href="{u}">{esc(n)}</a></li>' if i < len(trail) - 1 else f'<li aria-current="page">{esc(n)}</li>')
        for i, (u, n) in enumerate(trail)
    )
    return f'''<section class="page-hero">
  <div class="wrap">
    <nav class="breadcrumb" aria-label="Kruimelpad"><ol>{crumbs}</ol></nav>
    <span class="eyebrow">{esc(eyebrow)}</span>
    <h1>{esc(h1)}</h1>
    <p class="lead">{esc(lead)}</p>
  </div>
</section>'''


def service_cards(exclude=None):
    cards = "".join(
        f'''<a class="card" href="{s["url"]}"><span class="icon">{I[s["icon"]]}</span><h3>{esc(s["title"])}</h3><p>{esc(s["text"])}</p><span class="more">Lees meer<span class="sr-only"> over {esc(s["title"].lower())}</span></span></a>'''
        for s in SERVICES if s["url"] != exclude
    )
    cols = "grid-4" if exclude is None else "grid-3"
    return f'<div class="grid {cols}">{cards}</div>'


# ---------------------------------------------------------------- layout
def layout(page):
    url = page["url"]
    canonical = BASE + url
    title = page["title"]
    desc = page["description"]
    robots = "noindex, nofollow" if (NOINDEX or page.get("noindex")) else "index, follow, max-image-preview:large"
    graph = [org_schema(), {
        "@type": "WebSite", "@id": BASE + "/#website", "url": BASE + "/", "name": BIZ["name"],
        "inLanguage": "nl-NL", "publisher": {"@id": BASE + "/#organisatie"},
    }, {
        "@type": "WebPage", "@id": canonical + "#webpagina", "url": canonical, "name": title,
        "description": desc, "inLanguage": "nl-NL", "isPartOf": {"@id": BASE + "/#website"},
        "about": {"@id": BASE + "/#organisatie"},
    }]
    graph += page.get("schema", [])
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))

    gtm_head = gtm_body = ""
    if GTM:
        gtm_head = ("<!-- Google Tag Manager -->\n<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
                    "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),"
                    "dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;"
                    f"f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{esc(GTM)}');</script>\n<!-- End Google Tag Manager -->\n")
        gtm_body = (f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={esc(GTM)}" height="0" width="0" '
                    'style="display:none;visibility:hidden"></iframe></noscript>\n')
    gsc = f'<meta name="google-site-verification" content="{esc(GSC)}">\n' if (GSC and url == "/") else ""

    current = ' aria-current="page"'
    nav_links = "".join(
        f'<a href="{u}"{current if (u == url or (u != "/" and url.startswith(u))) else ""}>{esc(n)}</a>'
        for u, n in NAV
    )
    footer_services = "".join(f'<li><a href="{s["url"]}">{esc(s["title"])}</a></li>' for s in SERVICES)

    return f'''<!doctype html>
<html lang="nl">
<head>
{gtm_head}<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
{gsc}<meta property="og:type" content="website">
<meta property="og:locale" content="nl_NL">
<meta property="og:site_name" content="{BIZ["name"]}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/assets/img/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#232427">
<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/raleway-800.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/lato-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
{gtm_body}<a class="skip" href="#inhoud">Direct naar de inhoud</a>
<div class="topbar"><div class="wrap">
  <a href="{TEL}">{I["phone"]}{BIZ["phone_display"]}</a>
  <a href="{MAIL}">{I["mail"]}{BIZ["email"]}</a>
</div></div>
<header class="header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="SEC Calculaties – naar de homepage"><img src="/assets/img/logo.png" alt="SEC Calculaties" width="110" height="62"></a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Menu openen">{I["menu"]}</button>
    <nav class="nav" id="site-nav" aria-label="Hoofdmenu">
      {nav_links}
      <a class="btn btn--gold" href="{esc(MAIL_REQUEST)}">Calculatie aanvragen</a>
    </nav>
  </div>
</header>
<main id="inhoud">
{page["body"]}
</main>
<footer class="footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <img class="logo" src="/assets/img/logo.png" alt="SEC Calculaties" width="107" height="60" loading="lazy">
        <p>Calculatiebureau voor de droge afbouw. Wij berekenen materiaal en uren voor metal stud wanden en plafonds, voor afbouwbedrijven in heel Nederland.</p>
      </div>
      <div>
        <p class="footer-title">Diensten</p>
        <ul>{footer_services}<li><a href="/afbouwcalculatie-uitbesteden/">Calculatie uitbesteden</a></li></ul>
      </div>
      <div>
        <p class="footer-title">Contact</p>
        <address>
          {BIZ["name"]}<br>{BIZ["street"]}<br>{BIZ["postcode"]} {BIZ["city"]}<br>
          <a href="{TEL}">{BIZ["phone_display"]}</a><br>
          <a href="{MAIL}">{BIZ["email"]}</a>
        </address>
      </div>
      <div>
        <p class="footer-title">Bedrijf</p>
        <ul>
          <li><a href="/over-ons/">Over ons</a></li>
          <li><a href="/contact/">Contact en route</a></li>
          <li><a href="/assets/downloads/algemene-voorwaarden-sec-calculaties.pdf">Algemene voorwaarden (pdf)</a></li>
          <li>KvK {BIZ["kvk"]}</li>
          <li>Btw {BIZ["btw_display"]}</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year">{datetime.date.today().year}</span> {BIZ["name"]}</span>
      <span>Calculaties voor de droge afbouw in heel Nederland</span>
    </div>
  </div>
</footer>
<nav class="actionbar" aria-label="Snel contact">
  <a class="call" href="{TEL}">{I["phone"]}Bellen</a>
  <a class="mail" href="{esc(MAIL_REQUEST)}">{I["mail"]}Mailen</a>
</nav>
<script src="/assets/js/site.js" defer></script>
</body>
</html>
'''


# ---------------------------------------------------------------- pagina's
PAGES = []

# ---- Home
HOME_FAQ = [
    ("Wat doet een calculatiebureau voor de afbouw?",
     "Een calculatiebureau rekent voor afbouwbedrijven uit hoeveel materiaal en hoeveel uren een project kost. SEC Calculaties is gespecialiseerd in de droge afbouw: wij trekken de hoeveelheden van metal stud wanden en plafonds uit het bestek en de tekeningen en maken daar een begroting van."),
    ("Welke gegevens hebben jullie nodig voor een afbouwcalculatie?",
     "Het bestek en de tekeningen van het project, bijvoorbeeld als pdf. Wilt u een complete offerte, stuur dan ook uw inkoopgegevens mee. Ontbreekt er iets, dan nemen wij contact met u op."),
    ("Kan ik de hoeveelheden in mijn eigen calculatieprogramma gebruiken?",
     "Ja. Wij leveren de hoeveelheden zo aan dat u ze eenvoudig in uw eigen systeem verwerkt."),
    ("Werken jullie in heel Nederland?",
     "Ja. Omdat wij digitaal werken, is ons werkgebied heel Nederland. Voor een kennismaking komen wij graag bij u langs."),
    ("Kunnen jullie ook advies geven en de inkoop verzorgen?",
     "Ja. Wij geven advies over brandwerendheid, geluid en stabiliteit, in overleg met fabrikanten zoals Gyproc en Knauf. Ook maken wij offertes op basis van uw inkoopgegevens en kunnen wij de inkoop van de materialen verzorgen."),
]
USPS = [
    ("Meer dan 30 jaar ervaring", "Wij komen uit de afbouwwereld en kennen het vak van calculatie tot oplevering."),
    ("Materiaalkennis", "Door onze kennis van materialen en systemen zijn wij in de droge afbouw in alle markten thuis."),
    ("Strakke planning", "Wij werken met een realistische planning, zodat u uw project op tijd kunt indienen."),
    ("Heldere communicatie", "Wij luisteren, stellen de juiste vragen en houden korte lijnen met u."),
    ("Goede prijs-kwaliteitverhouding", "U krijgt kwaliteit voor een passende prijs."),
    ("Heel Nederland", "Wij werken digitaal en zijn daardoor in het hele land inzetbaar."),
]
usp_html = "".join(
    f'<li><img src="/assets/img/mark.png" alt="" width="48" height="48" loading="lazy"><div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>'
    for t, d in USPS
)
PAGES.append({
    "url": "/",
    "file": "index.html",
    "title": "Afbouwcalculatie voor de droge afbouw | SEC Calculaties",
    "description": "Calculatiebureau voor afbouwbedrijven: hoeveelheden en begrotingen voor metal stud wanden en plafonds, uit bestek en tekening. 30+ jaar ervaring.",
    "schema": [faq_schema(HOME_FAQ)],
    "body": f'''<section class="hero">
  <div class="wrap">
    <span class="eyebrow">Calculatiebureau droge afbouw</span>
    <h1>Afbouwcalculatie voor <span>metal stud wanden en plafonds</span></h1>
    <p class="lead">SEC Calculaties berekent voor afbouwbedrijven de benodigde materialen en uren, op basis van uw bestek en tekeningen. Zo dient u uw project op tijd en scherp in.</p>
    <div class="btn-row">
      <a class="btn btn--gold" href="{esc(MAIL_REQUEST)}">{I["send"]}Stuur uw tekeningen</a>
      <a class="btn btn--ghost" href="{TEL}">{I["phone"]}Bel {BIZ["phone_display"]}</a>
    </div>
    <ul class="trust">
      <li>{I["check"]}Meer dan 30 jaar ervaring in de afbouw</li>
      <li>{I["check"]}Werkgebied heel Nederland</li>
      <li>{I["check"]}Aangeleverd voor uw eigen systeem</li>
    </ul>
  </div>
</section>

<section class="section" id="diensten" aria-labelledby="diensten-titel">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Diensten</span>
      <h2 id="diensten-titel">Calculaties voor de droge afbouw</h2>
      <p class="lead">Wij nemen het theoretische deel van uw werk over: van hoeveelheden uittrekken tot een complete offerte.</p>
    </div>
    {service_cards()}
  </div>
</section>

<section class="section section--dark" aria-labelledby="waarom-titel">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Waarom SEC Calculaties</span>
      <h2 id="waarom-titel">Uw afbouwcalculatie uitbesteden aan vakmensen</h2>
      <p class="lead">Wij hebben jarenlang zelf metal stud wanden en plafonds gebouwd. Die praktijkkennis zit in elke calculatie.</p>
    </div>
    <ul class="usps">{usp_html}</ul>
  </div>
</section>

<section class="section section--paper" id="werkwijze" aria-labelledby="werkwijze-titel">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Werkwijze</span>
      <h2 id="werkwijze-titel">Zo werkt een calculatie bij SEC Calculaties</h2>
    </div>
    <ol class="steps">
      <li><h3>U stuurt bestek en tekeningen</h3><p>Mail de projectstukken en laat weten wat er berekend moet worden en wanneer.</p></li>
      <li><h3>Wij trekken de hoeveelheden uit</h3><p>Wij bepalen per wand- en plafondtype de hoeveelheden materiaal en uren.</p></li>
      <li><h3>U ontvangt de calculatie</h3><p>Overzichtelijk en klaar om in uw eigen systeem te verwerken.</p></li>
      <li><h3>Advies, offerte of inkoop</h3><p>Desgewenst met alternatieven, advies en een offerte op basis van uw inkoopgegevens.</p></li>
    </ol>
  </div>
</section>

<section class="section" aria-labelledby="over-titel">
  <div class="wrap split">
    <div class="prose">
      <span class="eyebrow">Over ons</span>
      <h2 id="over-titel">Van afbouwbedrijf naar calculatiebureau</h2>
      <p>Vijftien jaar lang bouwden wij met ons afbouwbedrijf Comperto BV metal stud wanden en plafonds in heel Nederland. Wij deden alles zelf: het project opnemen, calculeren, offreren, inkopen, plannen en begeleiden tot de oplevering.</p>
      <p>Eind 2020 kozen wij voor onze grootste kracht: het uittrekken van hoeveelheden en het begroten van metal stud wanden en plafonds. Zo ontstond SEC Calculaties. Met die ervaring ondersteunen wij nu afbouwbedrijven bij hun calculaties en offertes.</p>
      <p><a class="btn btn--outline" href="/over-ons/">Lees meer over ons</a></p>
    </div>
    {aside_html("Direct contact")}
  </div>
</section>

{faq_html(HOME_FAQ, "Veelgestelde vragen over afbouwcalculatie")}
{cta_html()}''',
})

# ---- Diensten (overzicht)
PAGES.append({
    "url": "/diensten/",
    "file": "diensten/index.html",
    "title": "Diensten calculatiebureau droge afbouw | SEC Calculaties",
    "description": "Metal stud calculatie, hoeveelheden uittrekken, advies over brand en geluid, offertes en inkoop. Alle diensten van SEC Calculaties voor afbouwbedrijven.",
    "schema": [breadcrumb_schema([("/", "Home"), ("/diensten/", "Diensten")])],
    "body": f'''{page_hero([("/", "Home"), ("/diensten/", "Diensten")], "Diensten", "Diensten voor afbouwbedrijven", "Wij ondersteunen droge afbouwbedrijven met het theoretische deel van het werk, zodat u zich op de uitvoering kunt richten.")}
<section class="section">
  <div class="wrap">
    {service_cards()}
  </div>
</section>
<section class="section section--paper">
  <div class="wrap split">
    <div class="prose">
      <h2>Calculatie uitbesteden als het druk is</h2>
      <p>Heeft u tijdelijk te weinig calculatiecapaciteit, of wilt u een tweede blik op een groot project? Wij springen bij voor één project of werken structureel voor u.</p>
      <p><a class="btn btn--outline" href="/afbouwcalculatie-uitbesteden/">Afbouwcalculatie uitbesteden</a></p>
    </div>
    {aside_html()}
  </div>
</section>
{cta_html()}''',
})

# ---- Metal stud calculatie
MS_FAQ = [
    ("Wat zit er in een metal stud calculatie?",
     "Een overzicht van de benodigde materialen en uren per wand- en plafondtype: profielen, beplating, isolatie, bevestigingsmaterialen en de arbeidstijd. Daarmee maakt u een onderbouwde begroting of offerte."),
    ("Berekenen jullie ook systeemwanden en verlaagde plafonds?",
     "Wij zijn gespecialiseerd in metal stud wanden en plafonds. Heeft u een project met andere systemen, neem dan contact op. Dan bespreken we wat mogelijk is."),
    ("Houden jullie rekening met eisen voor brand en geluid?",
     "Ja. Wij kijken naar de eisen uit het bestek en adviseren, in overleg met fabrikanten zoals Gyproc en Knauf, over geschikte systemen en alternatieven."),
]
PAGES.append({
    "url": "/metal-stud-calculatie/",
    "file": "metal-stud-calculatie/index.html",
    "title": "Calculatie metal stud wanden en plafonds | SEC Calculaties",
    "description": "Metal stud calculatie uitbesteden? Wij berekenen materiaal en uren voor metal stud wanden en plafonds op basis van bestek en tekeningen.",
    "schema": [
        breadcrumb_schema([("/", "Home"), ("/diensten/", "Diensten"), ("/metal-stud-calculatie/", "Metal stud calculatie")]),
        service_schema("Metal stud calculatie", "Berekening van materiaal en uren voor metal stud wanden en plafonds op basis van bestek en tekeningen.", "/metal-stud-calculatie/"),
        faq_schema(MS_FAQ),
    ],
    "body": f'''{page_hero([("/", "Home"), ("/diensten/", "Diensten"), ("/metal-stud-calculatie/", "Metal stud calculatie")], "Metal stud calculatie", "Calculatie van metal stud wanden en plafonds", "Wij berekenen de benodigde materialen en uren voor metal stud wanden en plafonds, zodat u met een scherpe en onderbouwde prijs inschrijft.")}
<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>Een complete calculatie voor de droge afbouw</h2>
      <p>Een goede metal stud calculatie begint bij het bestek en de tekeningen. Wij lopen het project per ruimte door en bepalen per wand- en plafondtype wat er nodig is. U krijgt een helder overzicht dat u direct kunt gebruiken voor uw begroting.</p>
      <h3>Wat wij voor u berekenen</h3>
      <ul class="checks">
        <li>Hoeveelheden per wand- en plafondtype, op basis van bestek en tekeningen</li>
        <li>Benodigde materialen: profielen, beplating, isolatie en bevestiging</li>
        <li>Benodigde uren voor de uitvoering</li>
        <li>Aandachtspunten uit het bestek, zoals eisen voor brand en geluid</li>
        <li>Mogelijke alternatieven die tijd of geld besparen</li>
      </ul>
      <h2>Waarom een externe calculator?</h2>
      <p>Calculeren kost tijd, juist als er meerdere aanvragen tegelijk binnenkomen. Door de calculatie uit te besteden, schrijft u in op meer projecten zonder extra mensen in dienst te nemen. En omdat wij zelf jarenlang metal stud wanden en plafonds hebben gebouwd, rekenen wij met de praktijk in ons achterhoofd.</p>
      <h2>Klaar voor uw eigen systeem</h2>
      <p>Wij leveren de hoeveelheden zo aan dat u ze eenvoudig in uw eigen calculatie- of offertesysteem verwerkt. Geen dubbel werk, geen overtypen.</p>
    </div>
    {aside_html()}
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><h2>Andere diensten</h2></div>
    {service_cards(exclude="/metal-stud-calculatie/")}
  </div>
</section>
{faq_html(MS_FAQ, "Vragen over metal stud calculatie")}
{cta_html()}''',
})

# ---- Hoeveelheden uittrekken
HV_FAQ = [
    ("Wat betekent hoeveelheden uittrekken?",
     "Bij hoeveelheden uittrekken bepaalt de calculator uit de tekeningen en het bestek hoeveel meter wand, hoeveel vierkante meter plafond en hoeveel materiaal er nodig is. Dat is de basis van iedere begroting."),
    ("In welke vorm ontvang ik de hoeveelheden?",
     "Wij stemmen de aanlevering af op uw werkwijze, zodat u de hoeveelheden eenvoudig in uw eigen systeem verwerkt."),
]
PAGES.append({
    "url": "/hoeveelheden-uittrekken/",
    "file": "hoeveelheden-uittrekken/index.html",
    "title": "Hoeveelheden uittrekken droge afbouw | SEC Calculaties",
    "description": "Wij trekken de hoeveelheden van metal stud wanden en plafonds uit bestek en tekeningen, aangeleverd zodat u ze direct in uw eigen systeem verwerkt.",
    "schema": [
        breadcrumb_schema([("/", "Home"), ("/diensten/", "Diensten"), ("/hoeveelheden-uittrekken/", "Hoeveelheden uittrekken")]),
        service_schema("Hoeveelheden uittrekken", "Hoeveelheden van metal stud wanden en plafonds uittrekken uit bestek en tekeningen.", "/hoeveelheden-uittrekken/"),
        faq_schema(HV_FAQ),
    ],
    "body": f'''{page_hero([("/", "Home"), ("/diensten/", "Diensten"), ("/hoeveelheden-uittrekken/", "Hoeveelheden uittrekken")], "Hoeveelheden uittrekken", "Hoeveelheden uittrekken uit bestek en tekeningen", "Nauwkeurige hoeveelheden zijn de basis van elke goede afbouwcalculatie. Wij bepalen ze voor u, per wand- en plafondtype.")}
<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>De basis van uw begroting</h2>
      <p>Een fout in de hoeveelheden werkt door in de hele begroting. Daarom nemen wij de tijd om bestek en tekeningen zorgvuldig door te lopen. Wij bepalen de hoeveelheden van metal stud wanden en plafonds en leveren die overzichtelijk aan.</p>
      <h3>Zo pakken wij het aan</h3>
      <ul class="checks">
        <li>Bestek en tekeningen naast elkaar: wat wordt er gevraagd en waar?</li>
        <li>Hoeveelheden per wand- en plafondtype, per ruimte of bouwdeel</li>
        <li>Onduidelijkheden in de stukken signaleren wij en bespreken wij met u</li>
        <li>Aanlevering die aansluit op uw eigen systeem</li>
      </ul>
      <h2>Alleen hoeveelheden, of een complete calculatie</h2>
      <p>Heeft u eigen prijzen en normen, dan kunt u volstaan met de hoeveelheden. Wilt u meer uit handen geven, dan maken wij er een complete <a href="/metal-stud-calculatie/">metal stud calculatie</a> of een <a href="/offertes-en-inkoop/">offerte</a> van.</p>
    </div>
    {aside_html()}
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><h2>Andere diensten</h2></div>
    {service_cards(exclude="/hoeveelheden-uittrekken/")}
  </div>
</section>
{faq_html(HV_FAQ, "Vragen over hoeveelheden uittrekken")}
{cta_html()}''',
})

# ---- Advies
AD_FAQ = [
    ("Met welke fabrikanten werken jullie?",
     "Wij adviseren in overleg met fabrikanten zoals Gyproc en Knauf, zodat het advies past bij de systemen die u gaat toepassen."),
    ("Wanneer is een alternatief interessant?",
     "Bijvoorbeeld als een ander systeem aan dezelfde eisen voldoet, maar sneller te monteren of goedkoper is. Wij geven zulke mogelijkheden aan op basis van de aangeleverde gegevens."),
]
PAGES.append({
    "url": "/advies-brand-geluid-stabiliteit/",
    "file": "advies-brand-geluid-stabiliteit/index.html",
    "title": "Advies brand, geluid en stabiliteit | SEC Calculaties",
    "description": "Advies over brandwerendheid, geluidsisolatie en stabiliteit van metal stud wanden en plafonds, in overleg met fabrikanten zoals Gyproc en Knauf.",
    "schema": [
        breadcrumb_schema([("/", "Home"), ("/diensten/", "Diensten"), ("/advies-brand-geluid-stabiliteit/", "Advies en alternatieven")]),
        service_schema("Advies brand, geluid en stabiliteit", "Advies over brandwerendheid, geluid en stabiliteit van metal stud wanden en plafonds.", "/advies-brand-geluid-stabiliteit/"),
        faq_schema(AD_FAQ),
    ],
    "body": f'''{page_hero([("/", "Home"), ("/diensten/", "Diensten"), ("/advies-brand-geluid-stabiliteit/", "Advies en alternatieven")], "Advies en alternatieven", "Advies over brand, geluid en stabiliteit", "Welk systeem voldoet aan de eisen uit het bestek, en kan het slimmer? Wij denken met u mee.")}
<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>De juiste wand en het juiste plafond</h2>
      <p>Eisen voor brandwerendheid, geluidsisolatie en stabiliteit bepalen welk systeem u moet toepassen. Wij vertalen die eisen naar passende metal stud oplossingen, in overleg met fabrikanten zoals Gyproc en Knauf.</p>
      <h3>Waar wij u mee helpen</h3>
      <ul class="checks">
        <li>Brandwerende wanden en plafonds die aan het bestek voldoen</li>
        <li>Geluidsisolatie tussen ruimtes</li>
        <li>Stabiliteit bij hoge wanden of zware belasting</li>
        <li>Alternatieven die aan dezelfde eisen voldoen, maar voordeliger zijn</li>
      </ul>
      <h2>Alternatieven die geld besparen</h2>
      <p>Op basis van de aangeleverde gegevens geven wij mogelijke alternatieven aan. Zo kiest u met uw opdrachtgever voor kwalitatief goede materialen en de voordeligste manier van bouwen.</p>
    </div>
    {aside_html("Advies nodig?")}
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><h2>Andere diensten</h2></div>
    {service_cards(exclude="/advies-brand-geluid-stabiliteit/")}
  </div>
</section>
{faq_html(AD_FAQ, "Vragen over advies en alternatieven")}
{cta_html()}''',
})

# ---- Offertes en inkoop
OI_FAQ = [
    ("Maken jullie ook de offerte voor mijn opdrachtgever?",
     "Ja. Op basis van uw inkoopgegevens maken wij een offerte die u aan uw opdrachtgever kunt sturen."),
    ("Kunnen jullie de materialen inkopen?",
     "Ja. Desgewenst verzorgen wij ook de inkoop van de materialen voor uw project."),
]
PAGES.append({
    "url": "/offertes-en-inkoop/",
    "file": "offertes-en-inkoop/index.html",
    "title": "Offertes en inkoop voor de droge afbouw | SEC Calculaties",
    "description": "Wij maken offertes op basis van uw eigen inkoopgegevens en verzorgen desgewenst de inkoop van materialen voor metal stud wanden en plafonds.",
    "schema": [
        breadcrumb_schema([("/", "Home"), ("/diensten/", "Diensten"), ("/offertes-en-inkoop/", "Offertes en inkoop")]),
        service_schema("Offertes en inkoop droge afbouw", "Offertes op basis van inkoopgegevens en inkoop van materialen voor de droge afbouw.", "/offertes-en-inkoop/"),
        faq_schema(OI_FAQ),
    ],
    "body": f'''{page_hero([("/", "Home"), ("/diensten/", "Diensten"), ("/offertes-en-inkoop/", "Offertes en inkoop")], "Offertes en inkoop", "Offertes en inkoop voor de droge afbouw", "Van calculatie naar offerte, en als u wilt ook de inkoop van de materialen. Wij ontzorgen u.")}
<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>Een offerte op basis van uw eigen prijzen</h2>
      <p>U kent uw inkoopprijzen en marges het best. Wij gebruiken uw inkoopgegevens om van de calculatie een complete offerte te maken. Zo blijft de prijs van u, en hoeft u het rekenwerk niet zelf te doen.</p>
      <h3>Wat u van ons krijgt</h3>
      <ul class="checks">
        <li>Een offerte op basis van de calculatie en uw inkoopgegevens</li>
        <li>Inzicht in de opbouw van materiaal en uren</li>
        <li>Desgewenst: inkoop van de materialen voor het project</li>
      </ul>
      <h2>Ervaring met in- en verkoop</h2>
      <p>Wij hebben jarenlang zelf calculaties, offertes, inkoop en planning gedaan voor ons eigen afbouwbedrijf. Die ervaring zetten wij nu in voor uw projecten.</p>
    </div>
    {aside_html()}
  </div>
</section>
<section class="section section--paper">
  <div class="wrap">
    <div class="section-head"><h2>Andere diensten</h2></div>
    {service_cards(exclude="/offertes-en-inkoop/")}
  </div>
</section>
{faq_html(OI_FAQ, "Vragen over offertes en inkoop")}
{cta_html()}''',
})

# ---- Uitbesteden
UB_FAQ = [
    ("Kan ik één project uitbesteden, of moet het structureel?",
     "Allebei kan. U kunt ons inschakelen voor één project, bij piekdrukte, of structureel als vaste calculator op afstand."),
    ("Hoe snel kunnen jullie starten?",
     "Dat hangt af van de omvang van het project en onze planning. Neem contact op met uw indiendatum, dan hoort u direct of het past."),
    ("Wat kost het om een afbouwcalculatie uit te besteden?",
     "De prijs hangt af van de omvang en de complexiteit van het project. Neem contact op, dan bespreken wij dit vooraf met u."),
]
PAGES.append({
    "url": "/afbouwcalculatie-uitbesteden/",
    "file": "afbouwcalculatie-uitbesteden/index.html",
    "title": "Afbouwcalculatie uitbesteden | SEC Calculaties",
    "description": "Te weinig tijd of calculatiecapaciteit? Besteed uw afbouwcalculatie uit aan SEC Calculaties: metal stud wanden en plafonds, voor één project of structureel.",
    "schema": [
        breadcrumb_schema([("/", "Home"), ("/afbouwcalculatie-uitbesteden/", "Afbouwcalculatie uitbesteden")]),
        service_schema("Afbouwcalculatie uitbesteden", "Externe calculatiecapaciteit voor droge afbouwbedrijven.", "/afbouwcalculatie-uitbesteden/"),
        faq_schema(UB_FAQ),
    ],
    "body": f'''{page_hero([("/", "Home"), ("/afbouwcalculatie-uitbesteden/", "Afbouwcalculatie uitbesteden")], "Calculatie uitbesteden", "Afbouwcalculatie uitbesteden", "Meer aanvragen dan u kunt doorrekenen? Wij werken als uw externe calculator voor de droge afbouw.")}
<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>Wanneer uitbesteden slim is</h2>
      <ul class="checks">
        <li>Er liggen meer aanvragen dan uw calculator kan doorrekenen</li>
        <li>Er staat een grote inschrijving op de planning met een krappe deadline</li>
        <li>U heeft geen eigen calculator, maar wilt wel scherp inschrijven</li>
        <li>U wilt een tweede blik op een calculatie voordat u indient</li>
      </ul>
      <h2>Wat u van ons kunt verwachten</h2>
      <p>Wij rekenen met de kennis van een afbouwbedrijf: wij hebben vijftien jaar zelf metal stud wanden en plafonds gebouwd. U krijgt een calculatie die klopt met de praktijk, aangeleverd zodat u er direct mee verder kunt.</p>
      <p>Wij werken met een strakke en realistische planning, zodat u uw project op tijd kunt indienen. Korte lijnen staan daarbij voorop: u heeft rechtstreeks contact met degene die uw project doorrekent.</p>
      <h2>Zo werkt het</h2>
      <ol>
        <li>U stuurt bestek, tekeningen en de gewenste datum.</li>
        <li>Wij laten weten of het in de planning past en bespreken de aanpak.</li>
        <li>Wij trekken de hoeveelheden uit en maken de calculatie.</li>
        <li>U ontvangt de calculatie, klaar voor verwerking in uw eigen systeem.</li>
      </ol>
    </div>
    {aside_html("Calculatie uitbesteden?")}
  </div>
</section>
{faq_html(UB_FAQ, "Vragen over calculatie uitbesteden")}
{cta_html()}''',
})

# ---- Over ons
PAGES.append({
    "url": "/over-ons/",
    "file": "over-ons/index.html",
    "title": "Over ons: 30 jaar ervaring in de afbouw | SEC Calculaties",
    "description": "SEC Calculaties ontstond uit afbouwbedrijf Comperto BV. Met meer dan 30 jaar ervaring calculeren wij metal stud wanden en plafonds voor afbouwbedrijven.",
    "schema": [breadcrumb_schema([("/", "Home"), ("/over-ons/", "Over ons")])],
    "body": f'''{page_hero([("/", "Home"), ("/over-ons/", "Over ons")], "Over ons", "Over SEC Calculaties", "Calculators met de kennis van een afbouwbedrijf. Wij hebben het werk dat wij berekenen jarenlang zelf uitgevoerd.")}
<section class="section">
  <div class="wrap split">
    <div class="prose">
      <h2>Ervaring uit de praktijk</h2>
      <p>Na jaren bij bouw- en grote afbouwbedrijven werkervaring te hebben opgedaan met calculeren, offertes maken en in- en verkoop, besloten wij het zelf te gaan doen. Zo ontstond Comperto BV: een totaal afbouwbedrijf met metal stud wanden en plafonds als basis.</p>
      <p>Met Comperto hebben wij in heel Nederland vele grote en kleine projecten gerealiseerd, samen met architecten, projectontwikkelaars en bouwbedrijven. Denk aan transformaties, nieuwbouw en verbouw.</p>
      <h2>Alles in eigen hand, korte lijnen</h2>
      <p>Behalve het bouwen deden wij alles zelf: het project opnemen, de calculatie, de offerte, de inkoop, het plannen van transport en het begeleiden van de bouw tot de oplevering. Dat betekende altijd korte lijnen en een fijne samenwerking met onze opdrachtgevers.</p>
      <h2>Sinds eind 2020: SEC Calculaties</h2>
      <p>Eind 2020 besloten wij ons te richten op onze grootste kracht: het uittrekken van de hoeveelheden en het begroten van metal stud wanden en plafonds. Zo is SEC Calculaties ontstaan. Wij ondersteunen droge afbouwbedrijven met het theoretische deel van hun werk.</p>
      <p>Binnen dat theoretische deel denken wij mee over een geschikte aanpak, met kwalitatief goede materialen en de voordeligste manier van bouwen. Wat er maar nodig is om u te ontzorgen bij het maken van offertes.</p>
    </div>
    {aside_html("Kennismaken?")}
  </div>
</section>
{cta_html("Zullen we kennismaken?", "Wij komen graag bij u langs, waar in Nederland u ook zit.")}''',
})

# ---- Contact
PAGES.append({
    "url": "/contact/",
    "file": "contact/index.html",
    "title": "Contact: calculatie aanvragen | SEC Calculaties",
    "description": f"Calculatie aanvragen of kennismaken? Bel {BIZ['phone_display']} of mail {BIZ['email']}. SEC Calculaties, {BIZ['street']}, {BIZ['city']}.",
    "schema": [breadcrumb_schema([("/", "Home"), ("/contact/", "Contact")])],
    "body": f'''{page_hero([("/", "Home"), ("/contact/", "Contact")], "Contact", "Contact en calculatie aanvragen", "Stuur uw bestek en tekeningen, of bel ons direct. Wij reageren zo snel mogelijk.")}
<section class="section">
  <div class="wrap">
    <div class="contact-cards">
      <a class="contact-card" href="{TEL}"><span class="icon">{I["phone"]}</span><span class="label">Bellen</span><span class="value">{BIZ["phone_display"]}</span></a>
      <a class="contact-card" href="{MAIL}"><span class="icon">{I["mail"]}</span><span class="label">Mailen</span><span class="value">{BIZ["email"]}</span></a>
      <a class="contact-card" href="{esc(MAIL_REQUEST)}"><span class="icon">{I["send"]}</span><span class="label">Calculatie aanvragen</span><span class="value">Stuur uw tekeningen</span></a>
    </div>
  </div>
</section>
<section class="section section--paper">
  <div class="wrap grid grid-2">
    <div class="card">
      <h2>Adres</h2>
      <address style="font-style:normal">{BIZ["name"]}<br>{BIZ["street"]}<br>{BIZ["postcode"]} {BIZ["city"]}</address>
      <p style="margin-top:1rem">Wij werken digitaal in heel Nederland. Voor een kennismaking komen wij graag bij u langs.</p>
      <p><a class="btn btn--outline" href="{BIZ["maps"]}" rel="noopener">{I["map"]}Route in Google Maps</a></p>
    </div>
    <div class="card">
      <h2>Bedrijfsgegevens</h2>
      <dl class="dl">
        <dt>KvK</dt><dd>{BIZ["kvk"]}</dd>
        <dt>Btw</dt><dd>{BIZ["btw_display"]}</dd>
        <dt>E-mail</dt><dd><a href="{MAIL}">{BIZ["email"]}</a></dd>
        <dt>Telefoon</dt><dd><a href="{TEL}">{BIZ["phone_display"]}</a></dd>
      </dl>
      <p style="margin-top:1rem"><a href="/assets/downloads/algemene-voorwaarden-sec-calculaties.pdf">Algemene voorwaarden (pdf)</a></p>
    </div>
  </div>
</section>''',
})

# ---- 404
PAGES.append({
    "url": "/404.html",
    "file": "404.html",
    "title": "Pagina niet gevonden | SEC Calculaties",
    "description": "Deze pagina bestaat niet (meer). Ga naar de homepage of neem contact op met SEC Calculaties.",
    "noindex": True,
    "body": f'''{page_hero([("/", "Home"), ("/404.html", "Niet gevonden")], "Foutmelding 404", "Deze pagina bestaat niet (meer)", "Misschien is de pagina verplaatst. Kies hieronder waar u naartoe wilt, of neem direct contact op.")}
<section class="section"><div class="wrap">{service_cards()}<p style="margin-top:2rem"><a class="btn btn--outline" href="/">Naar de homepage</a></p></div></section>''',
})


# ---------------------------------------------------------------- schrijven
def check(page):
    warnings = []
    t, d = page["title"], page["description"]
    if not 30 <= len(t) <= 60:
        warnings.append(f"title {len(t)} tekens")
    if not 110 <= len(d) <= 160:
        warnings.append(f"description {len(d)} tekens")
    return warnings


def with_prefix(markup):
    """Zet interne links (href="/..." en src="/...") om naar de submap van het testadres."""
    if not PREFIX:
        return markup
    return re.sub(r'(href|src)="/(?!/)', lambda m: f'{m.group(1)}="{PREFIX}/', markup)


# Oude WordPress-adressen: GitHub Pages kent geen serverredirects, dus een doorverwijspagina.
OLD_URLS = {
    "over-sec-calculaties/index.html": "/over-ons/",
    "home/index.html": "/",
}


def redirect_page(target):
    url = BASE + target
    local = PREFIX + target
    return (f'<!doctype html><html lang="nl"><head><meta charset="utf-8"><title>Doorverwijzing</title>'
            f'<link rel="canonical" href="{url}"><meta name="robots" content="noindex">'
            f'<meta http-equiv="refresh" content="0; url={local}"></head>'
            f'<body><p>Deze pagina is verplaatst naar <a href="{local}">{url}</a>.</p></body></html>\n')


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(OUT, "assets"))
    for name in ("_headers", "_redirects"):
        p = os.path.join(SRC, name)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OUT, name))
    # Oude pdf-link van de WordPress-site blijft werken.
    old_pdf = os.path.join(OUT, "wp-content", "uploads", "2021", "06", "Algemene-voorwaarden.pdf")
    os.makedirs(os.path.dirname(old_pdf), exist_ok=True)
    shutil.copy(os.path.join(SRC, "assets", "downloads", "algemene-voorwaarden-sec-calculaties.pdf"), old_pdf)
    for rel, target in OLD_URLS.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(redirect_page(target))

    seen_titles, seen_desc = set(), set()
    for page in PAGES:
        path = os.path.join(OUT, page["file"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(with_prefix(layout(page)))
        w = check(page)
        if page["title"] in seen_titles:
            w.append("dubbele title")
        if page["description"] in seen_desc:
            w.append("dubbele description")
        seen_titles.add(page["title"])
        seen_desc.add(page["description"])
        print(f"  {page['url']:<36} title {len(page['title']):>2} | desc {len(page['description']):>3}" + (f"  ! {', '.join(w)}" if w else ""))

    urls = [p for p in PAGES if not p.get("noindex")]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in urls:
        sitemap.append(f"  <url><loc>{BASE}{p['url']}</loc><lastmod>{TODAY}</lastmod></url>")
    sitemap.append("</urlset>")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sitemap) + "\n")
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(("User-agent: *\nDisallow: /\n" if NOINDEX else "User-agent: *\nAllow: /\n") + f"\nSitemap: {BASE}/sitemap.xml\n")
    print(f"Klaar: {len(PAGES)} pagina's in {OUT}")


if __name__ == "__main__":
    main()
