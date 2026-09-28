# DGleich Labs – Deployment und DNS

Ziel: `https://dgleichlabs.de` (optional `https://www.dgleichlabs.de`) auf die
statische Website aus `public/` zeigen lassen – **kostenlos**, ohne Backend.

> **STATUS: NICHT DURCHGEFÜHRT.**
> Es wurde **keine** DNS-Einstellung geändert, **kein** Nameserver umgestellt,
> **keine** Domain transferiert und **kein** Hosting-Konto angelegt.
> Dieses Dokument beschreibt die Schritte inklusive der Stellen, an denen eine
> ausdrückliche Freigabe nötig ist.

## 0. Ausgangslage und Risiken

| Punkt | Annahme / offene Frage |
|---|---|
| Registrar + DNS | **STRATO** (laut Auftrag) |
| E-Mail | Postfach `info@dgleichlabs.de` läuft über **STRATO** |
| Website | bisher **keine** – falls doch etwas auf `dgleichlabs.de` läuft, **muss das vorher geprüft werden** |
| Risiko 1 | Ein Ändern der **A-Records am Apex** kann eine bestehende STRATO-Website/Weiterleitung abschalten |
| Risiko 2 | Ein **Nameserver-Wechsel** (Cloudflare) kann die **E-Mail** brechen, wenn MX/SPF/DKIM/TXT nicht vollständig mitgezogen werden |
| Risiko 3 | **Wildcard-DNS** (`*.dgleichlabs.de`) niemals anlegen (Domain-Takeover-Risiko) |

### Vorarbeiten (zwingend, bevor irgendein Record geändert wird)

1. Aktuellen DNS-Stand **exportieren/screenshotten** (mindestens A, AAAA, CNAME,
   MX, TXT/SPF/DKIM, evtl. SRV): STRATO-Domainverwaltung → DNS.
2. Notieren, **wohin** der Apex aktuell zeigt (`nslookup dgleichlabs.de`).
3. Prüfen, ob `info@dgleichlabs.de` **aktuell** Mails empfängt (Testmail).
4. Erst danach eine der beiden Optionen wählen.

## 1. Option A – **empfohlen**, mail-sicher: GitHub Pages

**Warum diese Option zuerst:** Die DNS-Verwaltung bleibt komplett bei STRATO.
Es werden nur **neue** Records ergänzt/geändert, die die Web-Auslieferung
betreffen. **MX-/Mail-Einträge werden nicht berührt**, es gibt **keinen**
Nameserver-Wechsel.

### 1.1 Repository

- Repository `dgleichlabs-website` auf GitHub (public), Branch `main`.
- Deployment über die mitgelieferte Workflow-Datei
  `.github/workflows/pages.yml` (nutzt den offiziellen Pages-Weg, **keine
  Secrets** nötig), oder alternativ manuell:
  - Branch `gh-pages` mit dem **Inhalt** von `public/` befüllen.

### 1.2 GitHub Pages aktivieren

1. Repository → **Settings** → **Pages**.
2. **Build and deployment**: `Source = GitHub Actions` (bei der Workflow-Variante).
3. **Custom domain**: `dgleichlabs.de` eintragen und **Save**.
   → Wichtig laut GitHub: **zuerst** hier die Domain hinterlegen, **danach** DNS
     setzen (Schutz vor Domain-Übernahme).
4. Optional: **Enforce HTTPS** aktivieren (kann bis zu 24 h dauern).

> **Wichtig:** Schritt 2 und 3 lassen sich **nicht** automatisieren. Der
> Workflow-Token darf keine Pages-Site anlegen – ein `enablement: true` in
> `configure-pages` scheitert mit `Resource not accessible by integration`.
> Solange Pages aus ist, bricht der Job *Prepare artifact* mit
> `Get Pages site failed. Please verify that the repository has Pages enabled`
> ab. Das ist **kein** Projektfehler: der vorgelagerte Job *Verify build output*
> läuft trotzdem und belegt mit `build.py --check` und `check.py`, dass die
> Seite gültig ist. Nach dem Aktivieren den Workflow erneut auslösen
> (*Actions → Deploy static site to GitHub Pages → Re-run all jobs*).

### 1.3 DNS-Records bei STRATO (exakt diese Werte)

| Typ | Name/Host | Wert | Zweck |
|---|---|---|---|
| A | `@` (Apex `dgleichlabs.de`) | `185.199.108.153` | GitHub Pages |
| A | `@` | `185.199.109.153` | GitHub Pages |
| A | `@` | `185.199.110.153` | GitHub Pages |
| A | `@` | `185.199.111.153` | GitHub Pages |
| AAAA | `@` | `2606:50c0:8000::153` | optional (IPv6) |
| AAAA | `@` | `2606:50c0:8001::153` | optional (IPv6) |
| AAAA | `@` | `2606:50c0:8002::153` | optional (IPv6) |
| AAAA | `@` | `2606:50c0:8003::153` | optional (IPv6) |
| CNAME | `www` | `<GITHUB-BENUTZERNAME>.github.io` | `www`-Variante |

Quelle der IP-Adressen: GitHub-Dokumentation „Managing a custom domain for your
GitHub Pages site“.

**Regeln dazu:**

- `<GITHUB-BENUTZERNAME>.github.io` **ohne** Repository-Namen eintragen.
- **Niemals** einen Wildcard-Record (`*`) anlegen.
- **Keine** MX-, TXT-, SPF- oder DKIM-Records löschen oder ändern.
- Falls STRATO am Apex einen voreingestellten A-Record hat (z. B. auf
  STRATO-Hosting): bewusst entscheiden, ob er ersetzt wird – **das ist die
  einzige Änderung, die eine bestehende STRATO-Website abschalten würde**.
- `www` und Apex: GitHub leitet automatisch zwischen beiden um, wenn beide
  konfiguriert sind. Es wird **eine** Domain als Custom Domain gesetzt.

### 1.4 Grenzen von GitHub Pages

| Thema | GitHub Pages |
|---|---|
| `404.html` | ✅ wird verwendet |
| `_headers` (CSP & Co.) | ❌ **wird nicht ausgewertet** – Header fehlen |
| `_redirects` | ❌ wird nicht ausgewertet (GitHub leitet nur www↔Apex selbst) |
| HTTPS | ✅, mit „Enforce HTTPS“ erzwingbar |
| Kosten | kostenlos (public Repo) |

Wenn die strengen Sicherheits-Header (CSP, `nosniff`, HSTS) wirklich gebraucht
werden, ist Option B nötig – oder ein anderer Hoster mit `_headers`-Support.

## 2. Option B – Cloudflare Pages (bessere Header, aber Zone-Umzug)

**Warum das ein bewusster Schritt ist:** Für eine Custom Domain **muss die
gesamte DNS-Zone in Cloudflare liegen**. „Custom Domain hinzufügen“ bedeutet in
der Praxis also **Nameserver bei STRATO auf Cloudflare umstellen**. Damit hängt
die E-Mail an der korrekten Übernahme **aller** Records.

### 2.1 Ablauf (nur mit Freigabe)

1. In Cloudflare `dgleichlabs.de` als Zone anlegen – Cloudflare liest die
   bestehenden Records ein (Import prüfen!).
2. **Abgleich** gegen den Export aus Abschnitt 0:
   - MX-Records vorhanden und identisch? (Mail-Empfang)
   - SPF/DKIM/DMARC als TXT vorhanden?
   - Kein `Cloudflare Email Routing` aktivieren (das ändert MX-Records!).
   - A/AAAA/CNAME für Web prüfen.
3. **Erst danach** die beiden Cloudflare-Nameserver bei STRATO eintragen.
4. Propagation abwarten (Minuten bis Stunden; bis 24 h einplanen).
5. Cloudflare **Workers & Pages** → neues Pages-Projekt mit dem Repository
   verbinden:
   - **Build command:** *leer lassen*
   - **Build output directory:** `public`
   - Framework preset: *None*
6. Custom domains setzen: `dgleichlabs.de` und `www.dgleichlabs.de`.
7. Prüfen, dass `_headers` greift (siehe Abschnitt 4).

### 2.2 Mail-Schutzregeln

- MX-Records **niemals** anfassen und **niemals** proxien (Cloudflare proxyt MX
  nicht – aber ein fehlender MX bricht die Mail sofort).
- Kein „Email Routing“, keine „Email Workers“, keine neuen MX-Records.
- Vor dem Nameserver-Wechsel: Mail-Test **und** Web-Test gleichzeitig beobachten.
- Abbruchkriterium: Wenn im Cloudflare-Import auch nur **ein** Mail-relevanter
  Record fehlt → **nicht** umstellen, zuerst ergänzen.

## 3. Veröffentlichungs-Schritt (beide Optionen)

```bash
python tools/build.py --check     # public/ ist aktuell
python tools/assets.py --check    # Assets sind aktuell
python tools/check.py             # alles grün
```

Danach committen und pushen. Der Inhalt von `public/` ist das Produkt:
`index.html`, `404.html`, `projekte/`, `impressum/`, `datenschutz/`, `assets/`,
`robots.txt`, `sitemap.xml`, `site.webmanifest` (+ `_headers`, `_redirects`,
`.nojekyll`).

**Vor** dem ersten echten Push auf die Live-Domain:
- Impressum-Platzhalter ersetzt?
- Datenschutzerklärung geprüft (Hoster, Postfach, Drittland, Logs)?
- `lastmod` in `content/site.json` aktuell?

## 4. Nach dem Deployment prüfen

| Prüfung | Wie |
|---|---|
| DNS zeigt auf den Hoster | `nslookup dgleichlabs.de` |
| Apex und `www` erreichbar | beide URLs im Browser |
| Weiterleitung `www` ↔ Apex | eine der beiden leitet um |
| HTTPS aktiv, Zertifikat gültig | Browser-Schloss / Zertifikatsdetails |
| `404` funktioniert | `https://dgleichlabs.de/gibtsnicht` → gestaltete 404-Seite |
| Kopfzeilen (nur Cloudflare) | `curl -I https://dgleichlabs.de/` → CSP, `nosniff`, HSTS |
| `robots.txt` / `sitemap.xml` | direkt aufrufen |
| Kontakt | Testmail an `info@dgleichlabs.de` |
| Keine externen Requests | DevTools → Network: ausschließlich eigene Domain |
| Mobile | echtes Gerät, Hoch-/Querformat, 320 px Breite |

## 5. Rollback

| Situation | Maßnahme |
|---|---|
| Website falsch erreichbar | A-/AAAA-/CNAME-Records aus Abschnitt 1.3 entfernen bzw. alten Wert wiederherstellen |
| STRATO-Website war vorher aktiv | die vorher notierten A-Records zurücksetzen |
| Mail gestört (nur Option B) | Nameserver bei STRATO auf die vorherigen STRATO-Nameserver zurücksetzen |
| Header fehlen | erwartet bei GitHub Pages – nicht als Fehler behandeln oder Option B wählen |

**Mail-Records werden in keinem Szenario angefasst.**

## 6. STOPP-Punkte (hier wird gefragt, nicht gemacht)

1. Nameserver-Umstellung bei STRATO (Aktion außerhalb dieses Repos).
2. Löschen/Ersetzen eines **bestehenden** A-Records am Apex, wenn dort schon
   etwas ausgeliefert wird.
3. Jede Änderung an MX, TXT, SPF, DKIM, DMARC.
4. Anlegen eines Cloudflare-Kontos oder Pages-Projekts (kostenpflichtige
   Zusatzdienste / Konto-Bindung).
5. Domain-Transfer zu einem anderen Registrar.
6. Veröffentlichen der Website, solange Impressum/Datenschutz Platzhalter
   enthalten.

## 7. Was in diesem Auftrag bewusst NICHT passiert ist

- keine DNS-Änderung, kein Nameserver-Wechsel
- kein Cloudflare-/GitHub-Konto angelegt oder verbunden
- keine Domain reserviert oder transferiert
- kein Repository auf GitHub erstellt (GitHub-Zugang nicht authentifiziert
  verfügbar – siehe Abschlussbericht)
- keine Veröffentlichung
