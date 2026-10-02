# DGleich Labs – Deployment auf netcup Webhosting

Ziel: Der Inhalt von `public/` wird als statische Website über das bereits
vorhandene **netcup Webhosting (Tarif „Webhosting 1000 NUE“)** unter
`https://dgleichlabs.de` ausgeliefert. Auslieferungsort ist das
Web-Verzeichnis **`httpdocs`** der Domain im Webhosting-Account.

> **STATUS: LIVE (Stand 2. Oktober 2026).** Der Inhalt von `public/` wird unter
> `https://dgleichlabs.de` ausgeliefert. HTTPS ist über Let's Encrypt für
> `dgleichlabs.de` und `www.dgleichlabs.de` aktiv; HTTP → HTTPS ist im
> Hosting-Control-Panel aktiviert. Das Deployment-Archiv wurde nach dem
> Entpacken vom Server gelöscht.
>
> Weiterhin **freigabepflichtig** und nichts automatisiert: jede weitere
> DNS-Änderung, jede Nameserver-Umstellung, jede Änderung an MX/TXT/SPF/DKIM/
> DMARC sowie jeder erneute Upload (Abschnitt 9). Zugangsdaten liegen **nicht**
> im Repository. Dieser Abschnitt ist die Aufzeichnung des Wegs – die Schritte
> unten bleiben als nachvollziehbarer Verlauf erhalten.

**Rahmen (vom Betreiber vorgegeben):**

| Punkt | Festlegung |
|---|---|
| Hoster | netcup GmbH, Daimlerstraße 25, 76185 Karlsruhe (Deutschland) |
| Tarif | Webhosting 1000 NUE |
| Ziel | Inhalt von `public/` → `httpdocs/` der Domain `dgleichlabs.de` |
| Technik | rein statisch: HTML/CSS, **kein** WordPress, **keine** Datenbank, **kein** PHP nötig |
| GitHub | nur noch Versionsverwaltung und Backup – **kein** Production-Hosting mehr |
| E-Mail | Postfach `info@dgleichlabs.de` bleibt bei STRATO (unangetastet) |

## 1. Was sich gegenüber der früheren Planung geändert hat

Früher war **GitHub Pages** als Production-Hosting geplant (mit Cloudflare Pages
als Alternative). Diese Planung ist ersetzt:

| Datei/Stelle | vorher | jetzt |
|---|---|---|
| `.github/workflows/pages.yml` | Verify → Gate → Pages-Upload → Pages-Deploy | **entfernt**; ersetzt durch `.github/workflows/ci.yml` (Verify → Gate → Paket-Artefakt, **ohne** Deployment) |
| `src/static/_headers` | Sicherheits-Header für Cloudflare Pages | **entfernt**; Regeln stehen jetzt in `src/static/.htaccess` |
| `src/static/_redirects` | Weiterleitungen für Cloudflare Pages | **entfernt**; Regeln stehen jetzt in `src/static/.htaccess` |
| `src/static/.nojekyll` | GitHub-Pages-Sonderfall | **entfernt** (für Apache ohne Funktion) |
| GitHub Pages als Hoster | geplant | **nicht mehr vorgesehen** |

Begründung: `_headers` und `_redirects` sind Cloudflare-Pages-Formate. netcup
wertet sie **nicht** aus – sie wären wirkungslos, würden aber als Textdateien
mit hochgeladen und wären dann unter `https://dgleichlabs.de/_headers` öffentlich
abrufbar. Deshalb gibt es nur noch eine Hosting-Konfiguration: `.htaccess`.

## 2. Hoster-Dateien: was wohin übersetzt wurde

`src/static/.htaccess` (wird als `/.htaccess` ausgeliefert) übernimmt beide
früheren Dateien:

| Regel aus `_headers` / `_redirects` | Umsetzung in `.htaccess` |
|---|---|
| `Content-Security-Policy` | `Header always set Content-Security-Policy …` (unverändert streng: `default-src 'none'`, `script-src 'none'`, `frame-ancestors 'none'`) |
| `X-Content-Type-Options: nosniff` | `Header always set X-Content-Type-Options` |
| `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, COOP/CORP, `X-Robots-Tag` | `Header always set …` |
| `Strict-Transport-Security: max-age=31536000` | `Header always set Strict-Transport-Security` (weiterhin **ohne** `includeSubDomains`) |
| `Cache-Control` für `/assets/*` | `<FilesMatch "\.(?:css|png|svg|ico|webmanifest)$">` → `Cache-Control: public, max-age=31536000, immutable` |
| `Cache-Control` für `/` | bewusst **kein** langes Caching für HTML – Änderungen sollen sofort greifen |
| `www` → Apex (301) | `RewriteCond %{HTTP_HOST} ^www\.dgleichlabs\.de$` + `RewriteRule … [R=301,L]` |
| `/index.html` → `/` (301) | `RewriteRule ^index\.html$ / [R=301,L,NC]` (analog `projekte`, `fieldpro`, `impressum`, `datenschutz`) |
| GitHub-Pages-`404.html` | `ErrorDocument 404 /404.html` |
| (neu) Verzeichnisauflistung | `Options -Indexes` |
| (neu) versteckte Dateien | `<FilesMatch "^\.">` → `Require all denied` |

**Bewusste Einschränkungen – es wird nichts angenommen:**

- Alle Blöcke stehen in `<IfModule>`-Prüfungen. Fehlt ein Modul (z. B.
  `mod_headers` oder `mod_rewrite`), wird der Block übersprungen statt einen
  500-Fehler zu erzeugen.
- Es wird **nicht** behauptet, dass `.htaccess` im Tarif ausgewertet wird
  (`AllowOverride`). Das ist eine **DECISION REQUIRED**-Prüfung nach dem ersten
  Upload (siehe Abschnitt 6).

## 3. Zielstruktur im Webhosting

Der **komplette Inhalt** von `public/` wird 1:1 nach `httpdocs/` kopiert – es
gibt keinen weiteren Unterordner, keinen Build-Schritt und keine
Server-Konfiguration darüber hinaus:

```
httpdocs/                      (= Inhalt von public/)
├─ .htaccess                   Hosting-Konfiguration (Header, Weiterleitungen, 404)
├─ index.html
├─ 404.html
├─ robots.txt
├─ sitemap.xml
├─ site.webmanifest
├─ projekte/index.html
├─ fieldpro/index.html
├─ impressum/index.html
├─ datenschutz/index.html
└─ assets/
   ├─ styles.css
   ├─ favicon.svg
   ├─ favicon-32.png
   ├─ apple-touch-icon.png
   ├─ icon-192.png
   ├─ icon-512.png
   └─ og.png
```

Vorhandene Fremd-Dateien im `httpdocs`-Verzeichnis (z. B. eine netcup-
Platzhalterseite) sind vor dem Upload zu **entfernen**, sonst bleiben sie
erreichbar. Es wird **nichts** überschrieben, ohne vorher hinzusehen.

## 4. Migrationsplan: GitHub Pages → netcup

Reihenfolge bewusst so, dass zu keinem Zeitpunkt zwei produktive Kopien
nebeneinander existieren:

1. **Repository sauber** – `git status` clean, alle Gates grün (Abschnitt 5).
2. **Hosting-Konfiguration steht bereit** – `.htaccess` ist Bestandteil von
   `public/`, `_headers`/`_redirects`/`.nojekyll` sind aus dem
   Auslieferungsstand entfernt (bereits umgesetzt).
3. **Automation entschärft** – kein Workflow kann mehr nach GitHub Pages
   deployen (`ci.yml` enthält keine Pages-Actions; `tools/check.py` bricht ab,
   wenn sie wieder auftauchen).
4. **GitHub Pages stilllegen** – *Owner-Action in GitHub, nicht automatisierbar*:
   *Settings → Pages → Source: **None***. Danach liefert GitHub unter
   `*.github.io` nichts mehr aus. Solange eine Custom Domain dort eingetragen
   ist, bleibt sie sonst als zweite Auslieferung bestehen.
   **Erledigt und verifiziert (2. Oktober 2026):** Die GitHub-API meldet für
   das Repository keine Pages-Konfiguration (HTTP 404), und
   `https://defx473.github.io/dgleichlabs-website/` liefert 404. Es gibt keine
   zweite Auslieferung neben netcup.
5. **Webhosting vorbereiten** (netcup CCP) – _ohne_ Zugangsdaten im Repository:
   Domain `dgleichlabs.de` mit der Webhosting-Instanz verbinden, Domain in den
   Webhosting-Einstellungen als Domain anlegen, `httpdocs` prüfen.
   Doku dazu: netcup Helpcenter „Domain mit Webhosting verbinden“.
6. **TLS sicherstellen** – SSL über Let's Encrypt im Webhosting (Helpcenter
   „SSL-Verschlüsselung mit Let's Encrypt“). **Erledigt:** Das Zertifikat deckt
   `dgleichlabs.de` und `www.dgleichlabs.de` ab, HTTP → HTTPS ist im
   Hosting-Control-Panel aktiviert. *Verlauf:* Im temporären Hosting war zuvor
   bewusst **noch kein** Zertifikat ausgewählt – das war kein Fehler, sondern
   der Zustand vor dem Verbinden der Domain.
7. **Upload** – Inhalt von `public/` nach `httpdocs/`. **Erledigt**; der Weg
   (FTP/SFTP oder Dateimanager) war eine Betreiberentscheidung (Abschnitt 5).
   Das Archiv wurde nach dem Entpacken vom Server gelöscht.
8. **Abnahme** – Checkliste in Abschnitt 6.
9. **Erst danach** – Legal-/Go-Live-Hinweis entfernen und `lastmod` in
   `content/site.json` aktualisieren. **Erledigt:** Der Prüfhinweis ist aus
   Impressum und Datenschutz entfernt, `lastmod` steht auf `2026-10-02`. Die
   Notbremse (`tools/production_gate.py`) bleibt aktiv und erkennt einen
   Rückfall.

**Reihenfolge-Warnung:** Schritt 4 (Pages stilllegen) und Schritt 7 (Upload)
dürfen sich nicht überlappen, ohne dass die Domain eindeutig zeigt. Es gibt
sonst zwei Antworten auf dieselbe Domain.

## 5. Veröffentlichungs-Schritt (lokal, vor jedem Upload)

```bash
python tools/build.py            # public/ erzeugen
python tools/build.py --check    # public/ passt zum Quellstand
python tools/assets.py --check   # Assets passen
python tools/check.py            # Qualität: Links, Header, Hosting-Dateien, Secrets
python tools/production_gate.py  # Freigabe: 0 = veröffentlichbar
python -m unittest discover -s tools/tests -t tools
```

> **Notbremse:** `python tools/production_gate.py` blockiert die
> Veröffentlichung, solange in `public/` noch Platzhalter oder der Hinweis
> `LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT` stehen. Sie darf **nicht**
> umgangen, übersprungen oder abgeschwächt werden – auch nicht, um schneller
> live zu gehen.
>
> In der Pipeline (`ci.yml`) hängt der Paket-Job am Job **Production safety
> gate**; solange er rot ist, entsteht kein auslieferbares Paket. Ein roter
> Lauf bedeutet dort ausdrücklich **nicht** „kaputt“, sondern „noch nicht
> freigegeben“.

**Upload-Weg – DECISION REQUIRED** (eine der Varianten, keine davon ist
vorbereitet oder automatisiert):

- **FTP/SFTP** mit den Zugangsdaten aus dem Webhosting-Interface
  (Helpcenter „FTP-Zugang“). Zugangsdaten **niemals** ins Repository, in
  Workflow-Dateien oder in Logs schreiben.
- **Dateimanager** im Webhosting-Interface (Helpcenter „Dateimanager
  verwenden“) – für einen einmaligen Upload ausreichend.

**Upload-Inhalt (exakt):** alle Dateien und Ordner aus `public/`, inklusive
`.htaccess` und inklusive der versteckten Dateien. **Nicht** hochladen:
`content/`, `src/`, `tools/`, `docs/`, `.github/`, `README.md`, `LICENSE` –
das sind Quellen bzw. Repository-Dateien.

## 6. Nach dem ersten Upload prüfen

| Prüfung | Wie | Erwartung |
|---|---|---|
| Domain zeigt auf netcup | `nslookup dgleichlabs.de` | der netcup-Zielhost (siehe Abschnitt 7) |
| Startseite lädt | `https://dgleichlabs.de/` | Website erscheint |
| Kein 500-Fehler | Startseite nach dem Upload | **500** ⇒ Tarif wertet `.htaccess` nicht aus: Datei entfernen, Einstellungen stattdessen im Webhosting-Interface unter „Hosting-Einstellungen“ setzen |
| Sicherheits-Header | `curl -I https://dgleichlabs.de/` | `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Strict-Transport-Security` |
| Header-Modul aktiv | `curl -I` | fehlen die Header, ist `mod_headers` nicht verfügbar oder nicht erlaubt (DECISION REQUIRED: Alternative prüfen) |
| `www` → Apex | `https://www.dgleichlabs.de/` | 301 auf `https://dgleichlabs.de/` (nur wenn `www` verbunden ist) |
| Kanonische Pfade | `/index.html`, `/projekte/index.html` | 301 auf `/`, `/projekte/` |
| 404 | `https://dgleichlabs.de/gibtsnicht` | gestaltete 404-Seite, HTTP 404 |
| Verzeichnisauflistung | `https://dgleichlabs.de/assets/` | 403/404, **keine** Dateiliste |
| `robots.txt`, `sitemap.xml` | direkt aufrufen | vorhanden, Sitemap mit der Live-Domain |
| Keine externen Requests | DevTools → Network | ausschließlich eigene Domain |
| Keine Altlasten erreichbar | `/_headers`, `/_redirects`, `/.nojekyll` | **404** (dürfen nicht mehr existieren) |
| TLS | Browser-Schloss / Zertifikatsdetails | gültig, automatische Verlängerung aktiv |
| Kontakt | Testmail an `info@dgleichlabs.de` | Zustellung unverändert (STRATO) |
| Mobile QA | echtes Gerät, 320 px, Querformat | lesbar, keine Überläufe |

## 7. DNS – Aufzeichnung der Entscheidung

Die Domain `dgleichlabs.de` und das Postfach `info@dgleichlabs.de` liegen bei
**STRATO**. Damit die Website auf netcup ausgeliefert wird, gab es zwei Wege:

| Variante | Was passiert | Risiko |
|---|---|---|
| **A: DNS bleibt bei STRATO**, nur der Web-Record zeigt auf netcup | A/AAAA am Apex auf den netcup-Zielhost ändern; MX/TXT für die Mail bleiben unberührt | gering – solange ausschließlich Web-Records geändert werden |
| **B: netcup als Nameserver** (netcup CloudDNS) | Zone zu netcup umziehen, **alle** Records nachziehen (MX, SPF, DKIM, DMARC) | hoch – ein fehlender Mail-Record bricht `info@dgleichlabs.de` |

**Vor jeder DNS-Änderung zwingend:**

1. Aktuellen DNS-Stand exportieren/screenshotten (A, AAAA, CNAME, MX,
   TXT/SPF/DKIM/DMARC).
2. Prüfen, ob `info@dgleichlabs.de` aktuell Mails empfängt (Testmail).
3. Den netcup-Zielhost aus dem Webhosting-Interface ablesen (nicht raten, nicht
   aus fremden Quellen übernehmen).

**Entschieden und umgesetzt:** Die Domain liefert inzwischen von netcup aus
(`https://dgleichlabs.de` ist live), das Postfach `info@dgleichlabs.de` bleibt
bei **STRATO**. Welche der beiden Varianten dabei konkret gewählt wurde, ist
hier **nicht** dokumentiert. Sollte Variante B (netcup-Nameserver) verwendet
worden sein, ist zusätzlich sicherzustellen, dass **alle** Mail-Records (MX,
SPF, DKIM, DMARC) mitgezogen wurden – sonst bricht `info@dgleichlabs.de`. Das
ist ein Betriebspunkt, kein Rechtsblocker (Abschnitt 10). Der konkrete
A/AAAA-Zielwert steht hier weiterhin **nicht**, weil er ohne Einsicht in das
netcup-Panel nicht belegt werden kann.

**Regeln für beide Varianten:** keine MX-, TXT-, SPF- oder DKIM-Records ändern
oder löschen; **niemals** einen Wildcard-Record (`*`) anlegen; ein vorhandener
A-Record am Apex wird nicht ersetzt, ohne vorher zu wissen, was dort ausgeliefert
wird.

## 8. Rollback

| Situation | Maßnahme |
|---|---|
| Website fehlerhaft | vorherige Dateien im `httpdocs` wiederherstellen oder Domain zurück auf den alten Web-Record zeigen |
| 500-Fehler nach Upload | `.htaccess` aus `httpdocs` entfernen (Fehlerursache fast immer `AllowOverride None`) |
| Header fehlen | `.htaccess` ist aktiv, aber `mod_headers` fehlt → Alternative prüfen (DECISION REQUIRED) |
| Mail gestört (nur Variante B) | Nameserver bei STRATO auf die vorherigen Werte zurücksetzen |
| Zwei Seiten parallel erreichbar | GitHub Pages auf *Source: None* stellen bzw. A-Record vollständig umstellen |

**Mail-Records werden in keinem Szenario angefasst.**

## 9. STOPP-Punkte (hier wird gefragt, nicht gemacht)

1. Jeder Upload auf den netcup-Server (FTP/SFTP/Dateimanager) – nur nach
   ausdrücklicher Freigabe und grünem Production-Gate.
2. Jede DNS-Änderung und jede Nameserver-Umstellung.
3. Jede Änderung an MX, TXT, SPF, DKIM, DMARC.
4. Zugangsdaten irgendwo speichern (Repository, Workflow, Log, Dokumentation).
5. Veröffentlichen, solange Impressum/Datenschutz offene Punkte enthalten
   (erzwingt technisch `tools/production_gate.py`).
6. Den Hinweis `LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT` entfernen, ohne
   dass die rechtliche Prüfung tatsächlich stattgefunden hat.
7. PHP, Datenbank, WordPress oder zusätzliche Dienste im Webhosting aktivieren –
   die Website braucht keine davon.

## 10. Status und offene Punkte für den Betreiber

**Erledigt und verifiziert (Stand: 1.–2. Oktober 2026):**

- [x] **AV-Vertrag mit netcup** (Art. 28 DSGVO) – liegt vor: im netcup CCP
      unter *Stammdaten → Auftragsverarbeitung* ist die Vereinbarung bereits
      erstellt; Vertragspartner sind DGleich Labs und die netcup GmbH. Inhalte
      der Vereinbarung werden bewusst nicht im Repository wiedergegeben. Die
      Datenschutzerklärung verweist nur knapp darauf.
- [x] **Log-Speicherdauer** – anhand der offiziellen netcup-Dokumentation
      bestätigt: für Webhosting-Tarife mit Plesk werden Zugriffe auf die
      Websites **maximal 14 Tage** gespeichert; Logdateien liegen im Verzeichnis
      `Logs`, sind einsehbar und vorzeitig löschbar, die Protokollrotation ist
      einstellbar. Die Formulierung in `src/pages/datenschutz.html` ist daran
      angeglichen.
- [x] **Webstatistiken** – im Account unter *Hosting-Einstellungen →
      Webstatistiken* als **Deaktiviert** verifiziert; derzeit ist **keine**
      optionale serverseitige Plesk-Webstatistik aktiv. In der
      Datenschutzerklärung so benannt.
- [x] **Domain verbunden und live** – `https://dgleichlabs.de` liefert den
      Inhalt von `public/` aus; HTTP → HTTPS ist im Hosting-Control-Panel aktiv.
- [x] **TLS aktiv** – Let's Encrypt schützt `dgleichlabs.de` und
      `www.dgleichlabs.de` (Abschnitt 4, Schritt 6).
- [x] **Upload durchgeführt** – Inhalt von `public/` liegt in `httpdocs/`; das
      Deployment-Archiv wurde nach dem Entpacken vom Server gelöscht.
- [x] **Legal-Gate abgeschlossen** – der Prüfhinweis
      `LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT` ist aus Impressum und
      Datenschutzerklärung entfernt; `EXPECTED_OPEN` im Production-Gate ist leer.
      Die Notbremse selbst bleibt aktiv und erkennt einen Rückfall.
- [x] **Sachangaben final** – keine Telefonnummer, keine USt-IdNr.,
      Einzelunternehmen (keine GmbH/UG, kein Handelsregister). Die Angaben
      stehen im Text und werden nicht als offene Entscheidung geführt.
- [x] **GitHub Pages stillgelegt** – verifiziert am 2. Oktober 2026: die
      GitHub-API meldet für das Repository keine Pages-Konfiguration (HTTP 404)
      und `https://defx473.github.io/dgleichlabs-website/` liefert 404. Damit
      besteht keine zweite Auslieferung neben netcup (Abschnitt 4, Schritt 4).

**Weiterhin offen (Betrieb, kein Rechtsblocker):**

- [ ] **Mail-Records prüfen**, falls netcup als Nameserver eingesetzt wurde
      (Abschnitt 7, Variante B): MX, SPF, DKIM, DMARC müssen mitgezogen sein.
- [ ] **`.htaccess`-Wirkung bestätigen** – `curl -I https://dgleichlabs.de/`
      zeigt CSP, `nosniff` und HSTS; `/_headers`, `/_redirects`, `/.nojekyll`
      liefern 404. Bei 500 die Datei entfernen und Header über
      „Hosting-Einstellungen“ setzen.
- [ ] **Aufsichtsbehörde** optional namentlich nennen (bewusste
      Einzelfallentscheidung, kein Blocker).

Details, Belege und der Stand der Rechtstexte: `docs/LEGAL_SOURCES.md` und
`README.md`, Abschnitt „Produktionsstatus“.
