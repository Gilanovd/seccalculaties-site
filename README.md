# seccalculaties.nl – nieuwe website

Statische, snelle website voor SEC Calculaties. Gebouwd met één Python-script, zonder WordPress.

## Structuur

```
build.py            bouwt alle pagina's (teksten, titels, meta, schema) naar ./public
site.config.json    codes voor Google Tag Manager en Search Console
src/assets/         css, js, fonts, afbeeldingen, algemene voorwaarden
src/_headers        beveiligings- en cache-headers, en noindex op *.pages.dev
src/_redirects      301-redirects van oude WordPress-adressen
ANALYSE.md          branche-, concurrentie- en SEO-analyse
public/             gegenereerde site (niet zelf bewerken)
```

Lokaal bouwen: `python build.py`. Bekijken: `python -m http.server 8765 --directory public`.

## Hosting: Cloudflare Pages + GitHub

1. Zet deze map in een GitHub-repository (bijvoorbeeld `seccalculaties-site`).
2. Ga in Cloudflare naar **Workers & Pages → Create → Pages → Connect to Git** en kies de repository.
3. Gebruik deze build-instellingen:
   - Build command: `python3 build.py`
   - Build output directory: `public`
4. Elke wijziging die op GitHub wordt opgeslagen, zet Cloudflare automatisch live.
   Het testadres `*.pages.dev` krijgt automatisch `noindex`, zodat Google geen dubbele site ziet.

## Google Tag Manager en Search Console

Vul `site.config.json` in (dat kan in GitHub zelf, via het potloodje):

```json
"google_tag_manager_id": "GTM-XXXXXXX",
"google_search_console_verification": "code-uit-search-console"
```

Search Console kun je beter met een **DNS-TXT-record** in Cloudflare verifiëren (type *Domein*). Dan dekt het alle varianten (www, http, https) en is er geen code in de site nodig.
Let op: zodra GTM cookies plaatst (bijvoorbeeld Google Analytics), is een cookiemelding nodig.

## Overstap van het domein, met de WordPress-site als vangnet

Uitgangssituatie (DNS bij Yourwebhoster/ispnoc):

| Record | Waarde |
|---|---|
| NS | ns1.ispnoc.eu, ns2.ispnoc.net |
| A `seccalculaties.nl` | 46.249.37.170 (Plesk: website **en** mail) |
| CNAME `www` | seccalculaties.nl |
| A `mail`, `webmail` | 46.249.37.170 |
| MX | mail.seccalculaties.nl (prio 10) |
| TXT (SPF) | `v=spf1 include:mxo.ispnoc.eu +a +mx +a:p001.dro.ispnoc.eu -all` |
| TXT `_dmarc` | `v=DMARC1; p=quarantine; adkim=s; aspf=s` |
| DKIM | Te controleren in Plesk (Mail → Instellingen). |

Stappen:

1. **Niets aan WordPress veranderen.** De WordPress-site blijft gewoon op de Plesk-hosting staan (bestanden + database).
2. Voeg `seccalculaties.nl` als site toe in Cloudflare (gratis plan). Neem **alle** bovenstaande records over, ook DKIM.
   Zet `mail`, `webmail` en de MX-records op **DNS only** (grijze wolk), anders werkt e-mail niet.
3. Koppel in Cloudflare Pages het eigen domein: `seccalculaties.nl` en `www.seccalculaties.nl`.
   Cloudflare zet de website-records dan naar Pages. Het A-record voor mail blijft naar 46.249.37.170 wijzen.
4. Wijzig de naamservers bij Yourwebhoster (Domeinen → seccalculaties.nl → Naamservers) naar de twee van Cloudflare.
5. Controleer: website (nieuwe site), e-mail versturen en ontvangen, en webmail.
6. **Terugdraaien (vangnet):** verwijder in Cloudflare het eigen domein bij Pages en zet het A-record van `seccalculaties.nl` weer op `46.249.37.170`. Binnen enkele minuten draait de WordPress-site weer. In het uiterste geval: naamservers terug naar ispnoc.
7. Na een stabiele periode: Search Console → sitemap `https://seccalculaties.nl/sitemap.xml` indienen.
