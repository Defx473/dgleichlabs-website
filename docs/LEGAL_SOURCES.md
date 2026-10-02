# Belege zu Impressum und Datenschutzerklärung

Diese Datei ist für die **menschliche Rechtsprüfung**: sie zeigt, woher jede
Aussage in `src/pages/impressum.html` und `src/pages/datenschutz.html` stammt.
Sie ist **nicht** Teil der ausgelieferten Website (liegt nicht in `public/`).

Abrufdatum der Quellen: **28. September 2026** – netcup-Quellen (Abschnitt 2):
**1. Oktober 2026** (dort auch die vom Betreiber im netcup-Panel verifizierten
Angaben zu AV-Vertrag, Log-Speicherdauer und Webstatistiken)

> **Status (2. Oktober 2026):** Die Website ist live. Der frühere interne
> Prüfhinweis `LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT` ist aus
> Impressum und Datenschutzerklärung **entfernt**. Die Betreiberentscheidungen,
> die er offen hielt (Telefonnummer, Umsatzsteuer-Identifikationsnummer), sind
> **abschließend getroffen** und im Text sachlich umgesetzt – nicht als offene
> Punkte. Details in den Abschnitten 5 und 6a.

## 1. Was die Website tatsächlich tut (technisch geprüft)

| Aussage in der Datenschutzerklärung | Prüfung |
|---|---|
| keine Cookies | kein `Set-Cookie`, keine Skripte in `public/` |
| kein JavaScript | `grep -c "<script"` in allen ausgelieferten Seiten = 0 |
| keine externen Ressourcen | `tools/check.py` verbietet externe `src`/`href`-Ressourcen; Browser-Netzwerkmitschnitt zeigt ausschließlich Anfragen an die eigene Domain |
| keine externen Fonts | kein `@font-face`, kein `@import` in `public/assets/styles.css`; nur Systemschriften |
| keine Bilder von Dritten | alle Assets liegen in `public/assets/` und werden selbst erzeugt |
| kein Kontaktformular | nur `mailto:`-Link |
| keine Analyse/Tracker | kein Drittanbieter-Code vorhanden |

Nachvollziehbar mit:

```bash
python tools/check.py     # u. a. externe Ressourcen, CSS, Header
```

## 2. Hosting: netcup GmbH

**Aussage auf der Seite:** Die Website wird über das Webhosting der netcup GmbH,
Daimlerstraße 25, 76185 Karlsruhe, Deutschland ausgeliefert; der Inhalt von
`public/` liegt im Web-Verzeichnis (`httpdocs`) der Domain `dgleichlabs.de`.

**Quellen:**

- netcup Impressum (Firmierung, Sitz, Anschrift),
  <https://www.netcup.com/de/kontakt/impressum>
- netcup Helpcenter „Speicherung von Logdateien“ – dort sind die in
  Webhosting-Tarifen gespeicherten Felder einzeln aufgeführt (IP-Adresse,
  Remote-Identität, Remote-User, Dauer des Requests, First Line of Request,
  Status, übertragene Daten, Referrer, User-Agent) und für Webhosting-Produkte
  mit Plesk eine Speicherung von **maximal 14 Tagen** für Zugriffe auf die
  Websites genannt; die Protokollrotation kann der Kunde einstellen,
  <https://www.netcup.com/de/helpcenter/dokumentation/sicherheit/speicher-dauer>
- netcup Helpcenter „Auftragsverarbeitung“ – netcup stellt Kunden eine
  Zusatzvereinbarung zur Auftragsverarbeitung bereit, erstellbar im Customer
  Control Panel, ohne zusätzliche Kosten,
  <https://www.netcup.com/de/helpcenter/dokumentation/general/avv>
- netcup „Rechenzentren in Europa“ – Rechenzentrumsinfrastruktur in Nürnberg (DE)
  und Wien (AT), <https://www.netcup.com/de/ueber-netcup/rechenzentren>

**Auf der Seite steht deshalb:** Anbieterin mit Sitz in Deutschland; die
Logfelder sind einzeln aufgezählt; die 14 Tage sind als Angabe aus der
netcup-Dokumentation gekennzeichnet und um das Verzeichnis `Logs`, die
vorzeitige Löschmöglichkeit und die einstellbare Protokollrotation ergänzt;
Rechenzentren in Nürnberg/Wien und damit keine angenommene Drittlandübermittlung
durch das Hosting.

**Vom Betreiber verifiziert (1. Oktober 2026):**

- **AV-Vertrag:** Im netcup CCP unter *Stammdaten → Auftragsverarbeitung* ist
  die Vereinbarung zur Auftragsverarbeitung nach Art. 28 DSGVO bereits erstellt;
  Vertragspartner sind DGleich Labs und die netcup GmbH. Die Datenschutzerklärung
  sagt deshalb, dass eine solche Vereinbarung besteht – ohne Vertragsinhalte zu
  zitieren.
- **Log-Speicherdauer:** Die offizielle netcup-Dokumentation (Abschnitt oben)
  wurde geprüft und bestätigt für Webhosting-Tarife mit Plesk eine Speicherung
  der Website-Zugriffe von maximal 14 Tagen. Es werden keine über diese Quelle
  hinausgehenden Aussagen getroffen.
- **Webstatistiken:** Im konkreten Account unter *Hosting-Einstellungen →
  Webstatistiken* steht das Werkzeug auf **Deaktiviert**. Es ist derzeit
  **keine** optionale serverseitige Statistik aktiv; die Erklärung nennt das so.

**Nicht** auf der Seite behauptet, weil nicht belegt:

- keine Aussage darüber, ob netcup Unterauftragnehmer außerhalb der EU einsetzt
  (geregelt in der AV-Vereinbarung und der netcup-Datenschutzerklärung; hier
  nicht geprüft).

**Offene Punkte (DECISION REQUIRED):** keine mehr zum Hosting (AV-Vertrag,
Log-Speicherdauer und Webstatistik sind geklärt). Die verbliebenen offenen
Punkte betreffen Betreiberentscheidungen (Upload-Weg, DNS-Variante, TLS) – siehe
`docs/DEPLOYMENT.md`, Abschnitt 10.

## 3. Frühere Planung: GitHub Pages (ersetzt)

Das Hosting über GitHub Pages ist **nicht mehr vorgesehen** (Migration auf
netcup, siehe `docs/DEPLOYMENT.md`). Die folgenden Quellen belegen, dass die
früheren Aussagen belegt waren; für die Datenschutzerklärung sind sie nicht mehr
maßgeblich:

- GitHub Docs – *What is GitHub Pages?*, Abschnitt „Data collection“
  („When a GitHub Pages site is visited, the visitor's IP address is logged and
  stored for security purposes, regardless of whether the visitor has signed
  into GitHub or not.“),
  <https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages>
- GitHub General Privacy Statement (Data-Privacy-Framework-Abschnitt),
  <https://docs.github.com/site-policy/privacy-policies/github-privacy-statement>
- GitHub Data Protection Agreement,
  <https://github.com/customer-terms/github-data-protection-agreement>
- Data Privacy Framework Registry, Eintrag GitHub,
  <https://www.dataprivacyframework.gov/participant/6174>

GitHub bleibt **Versionsverwaltung und Backup** – dabei werden keine Daten der
Website-Besucher verarbeitet. Auch hier gilt: keine Aussage ohne Beleg.

## 4. E-Mail: STRATO GmbH

**Aussage auf der Seite:** Für das Postfach `info@dgleichlabs.de` wird das
E-Mail-Angebot der STRATO GmbH, Otto-Ostrowski-Straße 7, 10249 Berlin,
Deutschland genutzt.

**Quelle:** STRATO Impressum, <https://www.strato.de/impressum/> (Firmierung,
Sitz und Anschrift).

**Bewusst nicht behauptet:** dass die gesamte Kommunikation in Deutschland oder
der EU verbleibt. Das hängt von den Mailanbietern der jeweiligen
Kommunikationspartner ab.

## 5. Impressum: § 5 DDG

Angaben gemäß § 5 Digitale-Dienste-Gesetz: Name des Anbieters, ladungsfähige
Anschrift, schnelle elektronische Kontaktaufnahme und unmittelbare Kommunikation.

| Angabe | Status |
|---|---|
| Geschäftsbezeichnung „DGleich Labs“ | eingetragen |
| Inhaber (vollständiger Name) | eingetragen – Quelle: lokale Gewerbeanmeldung (Datei siehe unten) |
| Ladungsfähige Anschrift | eingetragen – Quelle: lokale Gewerbeanmeldung (Datei siehe unten) |
| E-Mail-Adresse | eingetragen |
| Telefonnummer | nicht angegeben – **entschieden**: keine Nummer, Kontakt nur über E-Mail (siehe unten) |
| Handelsregister | nicht vorhanden, korrekt als „besteht nicht“ ausgewiesen |
| USt-IdNr. | nicht angegeben – **entschieden**: derzeit keine Angabe (siehe unten) |

**Herkunft der personenbezogenen Angaben:** `~/Downloads/Gewerbe - Ummeldung (PDF).pdf`
(Gewerbeanmeldung/Gewerbeummeldung der zuständigen Verbandsgemeinde, Datum im
Formular 26.09.2026). Übernommen wurden **ausschließlich** Name und
Betriebsstättenanschrift. Nicht übernommen: Geburtsdatum, Geburtsort,
Telefonnummer, private E-Mail-Adresse und alle weiteren Formularangaben.

Zur Eindeutigkeit: das Formular enthält mehrere Adressen. Ausgewertet wurden die
Formularfelder (AcroForm-Feldnamen) – `anschrift_betriebsstaette` ist die
ladungsfähige Geschäftsanschrift. Die im Kopf des Formulars genannte Adresse
gehört laut Feldnamen (`meta_VG_*`, „Verbandsgemeinde Vordereifel“) zur
**Behörde**, nicht zum Anbieter.

Es existieren drei Exporte derselben Anmeldung im Download-Ordner
(`…(1).pdf`, `…(2).pdf`, `….pdf`). Sie stimmen in den hier verwendeten Angaben
überein; maßgeblich war `….pdf`.

**Telefonnummer (entschieden):** § 5 Abs. 1 Nr. 2 DDG verlangt Angaben, die
eine schnelle elektronische Kontaktaufnahme und unmittelbare Kommunikation
ermöglichen, einschließlich der E-Mail-Adresse. **Betreiberentscheidung:** Es
wird **keine** Telefonnummer angegeben; die Kontaktaufnahme läuft ausschließlich
über `info@dgleichlabs.de`. Auf der Seite steht daher keine Nummer – und
insbesondere **nicht** die im Gewerbeformular vorhandene private Nummer.

**Umsatzsteuer (entschieden):** **Betreiberentscheidung:** Es wird derzeit
**keine** USt-IdNr. angegeben. Wird künftig eine erteilt und ist eine Angabe
erforderlich, wird die Website aktualisiert. Die Seite benennt daher weder
USt-IdNr. noch Kleinunternehmerregelung; beides darf erst eingetragen werden,
wenn es tatsächlich zutrifft.

**Verantwortlich für den Inhalt (§ 18 Abs. 2 MStV):** bewusst **nicht**
aufgeführt, weil die Website keine journalistisch-redaktionellen Inhalte
enthält. Sollte später ein Blog, News- oder Pressebereich entstehen, ist die
Angabe zu ergänzen.

## 6. Aufsichtsbehörde

In der Datenschutzerklärung wird **keine** konkrete Aufsichtsbehörde genannt,
sondern die Zuständigkeit des Bundeslandes beschrieben, in dem der
Verantwortliche seinen Sitz hat. Eine namentliche Nennung wäre möglich, ist aber
eine bewusste Einzelfallentscheidung und im README als **optionaler
Betriebspunkt** geführt – kein Blocker für die Veröffentlichung.

## 6a. Weitere bewusste Entscheidungen im Text

- **Kein Datenschutzbeauftragter erwähnt.** Der Hinweis „kein DSB bestellt“ wurde
  entfernt, weil keine Veröffentlichungspflicht festgestellt ist.
- **Keine Aussage über fehlenden Zugriff auf Hoster-Protokolle.** Frühere Fassung
  behauptete, es bestehe „kein Zugriff“ auf die beim Hoster anfallenden
  Protokolle. Diese absolute Aussage ist nicht belastbar belegt und wurde
  ersetzt durch die nachweisbare Tatsache: Diese Website erhebt **keine eigenen
  Zugriffsdaten** – keine eigene Protokollierung, keine Auswertung, keine
  Reichweitenmessung (nachweisbar über `tools/check.py` und den fehlenden
  Drittanbieter-Code).
- **Telefonnummer:** Es wird keine genannt – auch nicht die im Formular
  vorhandene private Nummer (abschließende Betreiberentscheidung, Abschnitt 5).

## 7. Was dieses Dokument nicht ist

Keine Rechtsberatung. Es dokumentiert ausschließlich, welche technischen
Tatsachen geprüft wurden und welche Quellen für die Anbieterangaben verwendet
wurden, damit die Prüfung nachvollziehbar ist.
