# DGleich Labs – offizielle Website

Statische Website der Entwickler-/Software-Marke **DGleich Labs**.

| | |
|---|---|
| Domain | `dgleichlabs.de` (vorgesehen; noch **nicht** verbunden) |
| Kontakt | `info@dgleichlabs.de` |
| Version | v0.1 |
| Sprache | Deutsch (`<html lang="de">`), Claim englisch: „Software. Apps. Ideas.“ |
| Rechtsform | Geschäftsbezeichnung eines **deutschen Einzelunternehmens** (keine GmbH/UG) |

> Diese Website ist **nicht veröffentlicht**. Impressum und Datenschutz sind
> Vorlagen mit Platzhaltern und **vor** einem Deployment rechtlich zu prüfen
> (siehe „Before Production“).

## 1. Stack

Bewusst minimal und langfristig wartungsarm:

| Baustein | Entscheidung | Warum |
|---|---|---|
| Auslieferung | reines **statisches HTML/CSS** in `public/` | kein Server, keine Datenbank, keine Laufzeit-Abhängigkeiten |
| Build | **Python 3 (Standardbibliothek)** – `tools/build.py` | erzeugt HTML/Sitemap/Manifest aus Inhalten; kein Node/npm nötig |
| Styles | handgeschriebenes CSS (`public/assets/styles.css`) | Dark-First, kein CSS-Framework, keine Fremdschriften |
| JavaScript | **keines** | kleinste Angriffsfläche, beste Datenschutz-/CSP-Bilanz |
| Schriften | System-Font-Stack | kein externer Font-Abruf, damit keine Drittanbieter-Anfragen |
| Assets | eigenes SVG-Logo + per Pillow erzeugte PNGs | keine fremden Marken, keine gekauften Grafiken |
| Prüfung | `tools/check.py` (Links, SEO, Privacy, Secrets, Frische) | als „Lint“/„Test“ in einem Skript |

**Kein** WordPress, **kein** Astro/Next, **kein** Node-Build: Die Umgebung dieses
Projekts hatte keine Node-Toolchain, und die Anforderungen (schnell, günstig,
wartungsarm, ohne Backend) sind mit einem kleinen Generator vollständig erfüllt.

## 2. Voraussetzungen

- **Python 3.9+** (getestet mit Python 3.13)
- **Pillow** nur zum Neu-Erzeugen der Bilder-Assets:
  ```bash
  python -m pip install pillow
  ```
- **Git** (für Versionierung)
- Optional zum Testen der ausgelieferten Kopfzeilen: Cloudflare Pages (siehe `docs/DEPLOYMENT.md`)

Es ist **kein** `npm install` nötig.

## 3. Installation

```bash
git clone <repository-url> dgleichlabs-website
cd dgleichlabs-website
python -m pip install pillow     # optional, nur für Assets
```

## 4. Lokale Entwicklung

```bash
python tools/build.py            # Inhalte -> public/ erzeugen
python tools/serve.py            # Vorschau auf http://127.0.0.1:8788
python tools/serve.py --port 9000 --open
```

Der Vorschau-Server bildet das Hosting-Verhalten nach: Verzeichnisse werden über
`index.html` bedient, unbekannte Pfade liefern `404.html` mit Status 404, es gibt
keine Verzeichnis-Auflistung.

**Inhalte ändern:**

| Was | Wo |
|---|---|
| Texte/Seiteninhalte | `src/pages/*.html` |
| Kopf, Navigation, Fuß | `src/layout.html` |
| Metadaten, Domain, E-Mail, Navigation | `content/site.json` |
| Projekte | `content/projects.json` |
| Aussehen | `public/assets/styles.css` |
| Sicherheits-Header / Weiterleitungen | `src/static/_headers`, `src/static/_redirects` |

Nach jeder Änderung:

```bash
python tools/build.py && python tools/check.py
```

## 5. Production Build

```bash
python tools/build.py            # schreibt nur, was sich geändert hat
python tools/assets.py           # PNG-Assets neu erzeugen (nur bei Bedarf)
python tools/check.py            # Prüfbericht; Exit 0 = grün
python tools/build.py --check    # CI-Gate: public/ passt zum Quellstand
python tools/assets.py --check   # CI-Gate: Assets passen
```

Es gibt keinen „compile“-Schritt: `public/` **ist** das Produkt. Der Ordner wird
mitgeliefert (committed), damit Hosting ohne Build-Pipeline funktioniert.

Konvention: `public/` wird ausschließlich generiert – niemals direkt bearbeiten.
Ausgenommen sind Dateien, die direkt in `public/assets/` gepflegt werden und
nicht generiert sind (`favicon.svg`, `styles.css`).

Hinweis zu Pillow: `tools/assets.py` (nur Raster-Assets) und die Bildmaß-Prüfung
in `tools/check.py` brauchen **Pillow**. Ist es nicht installiert, meldet
`check.py` die Asset-Prüfungen als sichtbaren **Hinweis** statt als Fehler – so
bleibt eine CI ohne Pillow grün, ohne dass die Prüfung stillschweigend
verschwindet. PR-/Deploy-Checks laufen deshalb ohne Pillow; lokal ist der
Abgleich vollständig.

## 6. Deployment

Kurzfassung (Details und DNS-Records: **`docs/DEPLOYMENT.md`**):

- **Empfohlen für „Mail bleibt bei STRATO“:** GitHub Pages + DNS bei STRATO über
  A-Records (Apex) und CNAME (`www`). Keine Nameserver-Änderung, damit **kein
  Risiko für MX-/Mail-Einträge**.
- **Alternative:** Cloudflare Pages – dafür muss die **gesamte Zone** inklusive
  MX/SPF/DKIM zu Cloudflare umziehen (Nameserver-Wechsel). Nur nach vollständigem
  DNS-Abgleich und ausdrücklicher Freigabe.

Publish-Verzeichnis: `public/` · Publish-Branch: `main` (Root) ·
Build-Kommando: **keines** (bereits gebauter Ordner).

Für GitHub Pages liegt ein fertiger Workflow bereit:`.github/workflows/pages.yml`
(*Verify* → *Build* → *Deploy*, keine Secrets nötig). Er verifiziert vor dem
Deploy, dass `public/` zum Quellstand passt, und lädt `public/` als Artefakt hoch.
Einmalig im Repository nötig: *Settings → Pages → Source: GitHub Actions* und die
Custom Domain `dgleichlabs.de`.

## 7. Projektstruktur

```
dgleichlabs-website/
├─ content/                 Inhalte als Daten
│  ├─ site.json             Metadaten, Domain, E-Mail, Navigation, Routen
│  └─ projects.json         Projektliste (published-Flag steuert Sichtbarkeit)
├─ src/                     Quellen (nicht direkt ausgeliefert)
│  ├─ layout.html           Rahmen: <head>, Kopf, Navigation, Fuß
│  ├─ pages/                Seiteninhalte: index, projekte, impressum,
│  │                        datenschutz, 404
│  └─ static/               Kopiervorlagen für das Hosting
│     ├─ _headers           CSP und Sicherheits-Header (Cloudflare Pages)
│     ├─ _redirects         www → apex, index.html-Kanonisierung
│     └─ .nojekyll          GitHub Pages: Dateien mit _ unverändert ausliefern
├─ tools/                   Werkzeuge (nur Python-Standardbibliothek + Pillow)
│  ├─ build.py              Generator
│  ├─ check.py              Qualitäts-/Sicherheitsprüfung
│  ├─ serve.py              lokaler Vorschau-Server
│  └─ assets.py             PNG-Assets erzeugen
├─ public/                  **Auslieferungsstand** (generiert, gehostet)
│  ├─ index.html, 404.html
│  ├─ projekte/ impressum/ datenschutz/
│  ├─ assets/               styles.css, favicon.svg, PNG-Icons, og.png
│  ├─ robots.txt, sitemap.xml, site.webmanifest
│  └─ _headers, _redirects, .nojekyll
├─ docs/DEPLOYMENT.md       Deployment + DNS-Records (STRATO-schonend)
├─ README.md
└─ LICENSE                  Alle Rechte vorbehalten
```

## 8. Projekte ergänzen

Ein neues Projekt ist **ein Eintrag** in `content/projects.json`:

```json
{
  "id": "mein-projekt",
  "name": "Mein Projekt",
  "status": "in-development",
  "statusLabel": "In Entwicklung",
  "summary": "Ein Satz, der ehrlich beschreibt, was existiert.",
  "areas": ["Mobile", "AI Tools"],
  "published": true
}
```

Danach `python tools/build.py && python tools/check.py`.

`"published": false` bedeutet: der Eintrag ist **vorbereitet**, wird aber nirgends
ausgeliefert. `tools/check.py` schlägt Alarm, wenn ein nicht freigegebenes Projekt
doch im fertigen HTML auftaucht.

Status-Werte für `statusLabel` sind frei wählbar, üblich sind „In Entwicklung“,
„Coming soon“ oder ein echtes Veröffentlichungsdatum. **Keine** Store-Links,
Downloadbuttons oder Preise, solange nichts veröffentlicht ist.

## 9. Datenschutz im Design

Bewusste Technik-Entscheidungen, die die Datenschutzerklärung stützen:

- keine Cookies, kein Cookie-Banner, kein Tracking, keine Analytics
- **null** externe Requests (keine Fremdschriften, kein CDN, keine Embeds)
- kein JavaScript, damit auch die CSP `script-src 'none'` erlaubt ist
- kein Kontaktformular; Kontakt nur über `mailto:`

Wenn später etwas davon hinzukommt (Fonts, Analytics, Formular, Karten, Videos),
**muss** `src/pages/datenschutz.html` mitgeändert und die CSP in
`src/static/_headers` angepasst werden.

## 10. Security

- Keine Secrets, Tokens, Zugangsdaten, internen IPs oder lokalen Pfade im
  Repository – `tools/check.py` prüft das automatisch.
- Strenge Header in `src/static/_headers`: CSP mit `default-src 'none'`,
  `script-src 'none'`, `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy`,
  `Permissions-Policy`, HSTS (ohne `includeSubDomains`).
- Externe Links: es gibt derzeit **keine**. Sollten welche dazukommen, sind sie
  mit `rel="noopener noreferrer"` und klarem Ziel zu setzen.
- `tools/serve.py` ist **nur** für die lokale Vorschau (bindet auf `127.0.0.1`).

## 11. Before Production

> **LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT**
> Impressum und Datenschutzerklärung sind Vorlagen mit Platzhaltern und müssen
> vor der Veröffentlichung rechtlich geprüft und vervollständigt werden.

Vor einer Veröffentlichung abzuarbeiten:

- [ ] **Impressum vervollständigen und prüfen** (Name, Anschrift, Telefon, ggf. USt-IdNr.) – Datei `src/pages/impressum.html`
- [ ] **Datenschutzerklärung prüfen** (Hosting-Anbieter, E-Mail-Anbieter, Drittland, Log-Speicherdauer) – Datei `src/pages/datenschutz.html`
- [ ] `content/site.json`: `lastmod` aktualisieren
- [ ] **Domain verbinden** (`dgleichlabs.de`, optional `www`) – `docs/DEPLOYMENT.md`
- [ ] **HTTPS prüfen** (Zertifikat aktiv, „Enforce HTTPS“ bzw. Cloudflare-Universalschutz)
- [ ] `_headers`-Verhalten beim Hoster prüfen (Cloudflare Pages) oder bewusst darauf verzichten (GitHub Pages)
- [ ] **Kontaktadresse testen** – E-Mail an `info@dgleichlabs.de`, Zustellung und Antwortadresse prüfen
- [ ] **Mobile QA** auf echtem Gerät (iOS + Android), Schriftgrößen, Zoom, Querformat
- [ ] Tastatur-/Screenreader-Kurztest (Tab-Reihenfolge, Skip-Link, Fokus sichtbar)
- [ ] **Production Build prüfen**: `python tools/build.py --check && python tools/assets.py --check && python tools/check.py`
- [ ] `sitemap.xml`/`robots.txt` auf der Live-Domain erreichbar
- [ ] Lighthouse/„Page Speed“ einmal gegen die Live-URL laufen lassen
- [ ] Optional: GitHub-Link im Footer ergänzen (dann `githubUrl` in `content/site.json` **und** `footerGithub` in `tools/build.py` füllen)

## 12. Lizenz

Alle Rechte vorbehalten – siehe `LICENSE`. Die Inhalte und Assets sind
Eigentum des Inhabers von DGleich Labs.

## 13. Kontakt

- Website: `https://dgleichlabs.de` (nach Deployment)
- E-Mail: `info@dgleichlabs.de`

**Geschäftsbezeichnung eines deutschen Einzelunternehmens. Keine GmbH, keine UG.**
