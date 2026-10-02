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
- Optional zum Prüfen der ausgelieferten Kopfzeilen: eine Umgebung, die `.htaccess`
  auswertet (Apache). Lokal prüft `tools/check.py` den Inhalt von `.htaccess`
  statisch – siehe `docs/DEPLOYMENT.md`

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
| Sicherheits-Header / Weiterleitungen | `src/static/.htaccess` (Apache, netcup) |

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

### Production Gate (Deploy-Sperre)

`tools/check.py` prüft die **Qualität** der Seite und muss auch dann grün sein,
wenn die Rechtstexte noch unfertig sind – sonst wäre lokale Entwicklung
unmöglich. Ob die Seite **veröffentlichbar** ist, entscheidet eine eigene
Notbremse:

```bash
python tools/production_gate.py           # Exit 1 = Veröffentlichung blockiert
python tools/production_gate.py --list    # alle Treffer einzeln zeigen
python -m unittest discover -s tools/tests -t tools   # Tests des Gates
```

Der Gate bricht ab, solange in `public/` noch

1. ein bekannter Pflicht-Platzhalter (`[VOLLSTÄNDIGER NAME]`, `[ANSCHRIFT]`,
   `[TELEFON]`, `[STRASSE UND HAUSNUMMER]`, `[PLZ UND ORT]`,
   `[HOSTING-PROVIDER]`, `[E-MAIL-PROVIDER eintragen]`),
2. irgendeine **weitere** eckige Klammer mit Text (also auch später ergänzte
   Platzhalter, ohne diese Datei zu pflegen) oder
3. der Hinweis `LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT`

steht. Code-Fragmente wie `["Mobile", "Plattform"]` oder
`[aria-current="page"]` werden **nicht** fälschlich gemeldet.

In der Pipeline läuft der Gate als **eigener Job vor dem Artefakt-Upload**
(`production-gate` → `build` → `deploy`). Ist er rot, wird nichts hochgeladen
und nichts veröffentlicht – ein roter Lauf bedeutet dort also ausdrücklich
*nicht* „kaputt“, sondern *noch nicht freigegeben*.

Lokal ist der Gate **nicht** Teil des Builds: `python tools/build.py` und
`python tools/serve.py` funktionieren jederzeit.

Hinweis zu Pillow: `tools/assets.py` (nur Raster-Assets) und die Bildmaß-Prüfung
in `tools/check.py` brauchen **Pillow**. Ist es nicht installiert, meldet
`check.py` die Asset-Prüfungen als sichtbaren **Hinweis** statt als Fehler – so
bleibt eine CI ohne Pillow grün, ohne dass die Prüfung stillschweigend
verschwindet. PR-/Deploy-Checks laufen deshalb ohne Pillow; lokal ist der
Abgleich vollständig.

## 6. Deployment

Kurzfassung (Details und DNS-Records: **`docs/DEPLOYMENT.md`**):

- **Produktiv:** netcup Webhosting (Tarif „Webhosting 1000 NUE“). Der Inhalt von
  `public/` wird nach `httpdocs/` der Domain `dgleichlabs.de` hochgeladen.
  Kein WordPress, keine Datenbank, kein PHP. Die E-Mail bleibt unverändert bei
  STRATO; DNS-Records werden nicht angefasst, solange das nicht ausdrücklich
  freigegeben ist.
- **GitHub** bleibt Versionsverwaltung und Backup – **kein** Production-Hosting
  mehr. Der frühere Pages-Workflow ist entfernt; `ci.yml` verifiziert nur.

Upload-Inhalt: der komplette Ordner `public/` (inklusive `.htaccess`) ·
Build-Kommando beim Hoster: **keines** (bereits gebauter Ordner).

Die vollständige Anleitung inklusive Zielstruktur, Migrationsschritten,
DNS-Entscheidung und Abnahmeliste steht in **`docs/DEPLOYMENT.md`**.
Automatisch deployt wird nichts: der Upload ist ein bewusster, manueller
Schritt nach grünem Production Gate.

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
│     └─ .htaccess          CSP/Sicherheits-Header, www- und index.html-
│                           Weiterleitungen, 404 (Apache/netcup)
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
│  └─ .htaccess
├─ docs/DEPLOYMENT.md       Deployment auf netcup + DNS-Entscheidung
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
`src/static/.htaccess` angepasst werden.

## 10. Security

- Keine Secrets, Tokens, Zugangsdaten, internen IPs oder lokalen Pfade im
  Repository – `tools/check.py` prüft das automatisch.
- Strenge Header in `src/static/.htaccess`: CSP mit `default-src 'none'`,
  `script-src 'none'`, `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy`,
  `Permissions-Policy`, HSTS (ohne `includeSubDomains`). Regeln stehen in
  `<IfModule>`-Blöcken, damit ein fehlendes Apache-Modul keinen 500-Fehler
  erzeugt; `tools/check.py` prüft den Inhalt der Datei statisch.
- Externe Links: es gibt derzeit **keine**. Sollten welche dazukommen, sind sie
  mit `rel="noopener noreferrer"` und klarem Ziel zu setzen.
- `tools/serve.py` ist **nur** für die lokale Vorschau (bindet auf `127.0.0.1`).

## 11. Before Production

> **LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT**
> Impressum und Datenschutzerklärung beschreiben die tatsächlich eingesetzte
> Technik (Hosting bei netcup, Postfach bei STRATO). Der Hinweis bleibt stehen,
> bis die unten aufgeführten Punkte entschieden und die Texte rechtlich geprüft
> sind.

**Personenbezogene Angaben sind eingetragen** (Name und ladungsfähige
Geschäftsanschrift des Inhabers, übernommen aus der Gewerbeanmeldung; Details
und Belege in `docs/LEGAL_SOURCES.md`). Es stehen **keine** Platzhalter mehr in
der Seite – das Production Gate blockiert daher ausschließlich wegen des
Prüfhinweises:

- [ ] `LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT` erst aus
      `src/pages/impressum.html` und `src/pages/datenschutz.html` entfernen,
      wenn alle Punkte unten entschieden sind

**Geklärt (Hosting, 1. Oktober 2026)** – verifiziert und in den Text übernommen:

- [x] **AV-Vertrag mit netcup** (Art. 28 DSGVO): im CCP unter *Stammdaten →
      Auftragsverarbeitung* bereits erstellt; Vertragspartner DGleich Labs und
      netcup GmbH. Die Datenschutzerklärung verweist darauf, ohne Inhalte zu
      zitieren.
- [x] **Log-Speicherdauer**: laut offizieller netcup-Dokumentation für
      Webhosting-Tarife mit Plesk **maximal 14 Tage**; Formulierung in
      `src/pages/datenschutz.html` daran angeglichen.
- [x] **Webstatistiken**: unter *Hosting-Einstellungen → Webstatistiken* als
      **Deaktiviert** verifiziert; keine serverseitige Statistik aktiv.
- [x] **TLS**: im temporären Hosting bewusst noch **kein** Zertifikat – kein
      Fehler; Let's Encrypt erst nach Verbindung von `dgleichlabs.de`.

**DECISION REQUIRED** (bewusst nicht entschieden, nichts erfunden):

- [ ] **Telefonnummer**: derzeit keine angegeben; Kontakt läuft ausschließlich über die E-Mail-Adresse. Für § 5 DDG ist eine schnelle elektronische Kontaktaufnahme erforderlich – ob die E-Mail-Adresse dafür genügt, ist die eigene Rechtsentscheidung.
- [ ] **Umsatzsteuer**: keine USt-IdNr. angegeben. Klären, ob eine vorliegt oder ob die Kleinunternehmerregelung nach § 19 UStG greift; erst dann eintragen.
- [ ] **Aufsichtsbehörde**: die Datenschutzerklärung benennt bewusst keine konkrete Behörde, sondern die Zuständigkeit des Sitz-Bundeslandes. Optional, aber üblich: die Behörde namentlich ergänzen.
- [ ] **`.htaccess`-Auswertung**: bestätigen, dass der Tarif `.htaccess` auswertet (Header, Weiterleitungen, 404). Bei 500-Fehler nach dem Upload: Datei entfernen, Einstellungen über die Hosting-Einstellungen setzen.
- [ ] **DNS-Variante**: entscheiden, ob nur der Web-Record auf netcup zeigt (Mail bleibt bei STRATO unangetastet) oder ob netcup Nameserver wird (dann müssen alle Mail-Records mitziehen).

Vor einer Veröffentlichung abzuarbeiten:

- [ ] **Impressum vervollständigen und prüfen** – Datei `src/pages/impressum.html`
- [ ] **Datenschutzerklärung prüfen** – Datei `src/pages/datenschutz.html`
- [ ] `content/site.json`: `lastmod` und `legalStand` aktualisieren
- [ ] **Domain im Webhosting verbinden** (`dgleichlabs.de`, optional `www`) – `docs/DEPLOYMENT.md`
- [ ] **GitHub Pages stilllegen** – *Settings → Pages → Source: None*; sonst bleibt eine zweite Auslieferung bestehen
- [ ] **HTTPS prüfen** (Let's Encrypt im Webhosting aktiv, Zertifikat gültig, automatische Verlängerung)
- [ ] **`.htaccess`-Wirkung prüfen** – `curl -I https://dgleichlabs.de/` zeigt CSP, `nosniff`, HSTS; `/_headers`, `/_redirects`, `/.nojekyll` liefern 404
- [ ] **Kontaktadresse testen** – E-Mail an `info@dgleichlabs.de`, Zustellung und Antwortadresse prüfen
- [ ] **Mobile QA** auf echtem Gerät (iOS + Android), Schriftgrößen, Zoom, Querformat
- [ ] Tastatur-/Screenreader-Kurztest (Tab-Reihenfolge, Skip-Link, Fokus sichtbar)
- [ ] **Production Gate grün bekommen**: `python tools/production_gate.py` muss `0` liefern – erst dann darf deployt werden
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
