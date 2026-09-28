# Belege zu Impressum und Datenschutzerklärung

Diese Datei ist für die **menschliche Rechtsprüfung**: sie zeigt, woher jede
Aussage in `src/pages/impressum.html` und `src/pages/datenschutz.html` stammt.
Sie ist **nicht** Teil der ausgelieferten Website (liegt nicht in `public/`).

Abrufdatum der Quellen: **28. September 2026**

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

## 2. Hosting: GitHub Pages

**Aussage auf der Seite:** Beim Besuch einer GitHub-Pages-Website wird die
IP-Adresse des Besuchers protokolliert und zu Sicherheitszwecken gespeichert –
unabhängig davon, ob er bei GitHub angemeldet ist.

**Quelle:** GitHub Docs – *What is GitHub Pages?*, Abschnitt „Data collection“,
<https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages>

Wörtlich: „When a GitHub Pages site is visited, the visitor's IP address is
logged and stored for security purposes, regardless of whether the visitor has
signed into GitHub or not.“

**Nicht** auf der Seite behauptet, weil nicht belegt:
- keine konkrete Speicherdauer für diese Protokolle (GitHub nennt keine),
- keine Aussage über konkrete Logfelder über die hinaus, die eine HTTP-Anfrage
  ohnehin übermittelt.

**Anbieter:** GitHub, Inc. (USA), Teil der Microsoft-Gruppe.

## 3. Drittlandübermittlung in die USA

**Aussage auf der Seite:** GitHub erklärt, sich zur Einhaltung der Grundsätze
des EU-U.S. Data Privacy Framework verpflichtet zu haben (inkl. Erweiterungen
für UK und Schweiz); im Übrigen stützt sich GitHub nach eigenen Angaben auf die
Standardvertragsklauseln der EU-Kommission.

**Quellen:**
- GitHub General Privacy Statement (Abschnitt zum Data Privacy Framework),
  <https://docs.github.com/site-policy/privacy-policies/github-privacy-statement>
  – „GitHub has certified to the U.S. Department of Commerce that it adheres to
  the EU-U.S. Data Privacy Framework Principles …“
- GitHub Data Protection Agreement (SCCs, DPF-Selbstzertifizierung),
  <https://github.com/customer-terms/github-data-protection-agreement>
- Data Privacy Framework Registry, Eintrag GitHub (EU-U.S., UK Extension und
  Swiss-U.S. jeweils „Active“), <https://www.dataprivacyframework.gov/participant/6174>

**Offener Punkt (DECISION REQUIRED):** Das GitHub Data Protection Agreement ist
laut eigener Beschreibung „part of the GitHub Customer Agreement“. Ob daraus für
ein **kostenloses** Konto mit öffentlichem Repository ein Auftragsverarbeitungs-
vertrag nach Art. 28 DSGVO folgt, ist zu klären, bevor veröffentlicht wird.

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
| Inhaber (vollständiger Name) | **offen** – Platzhalter, personenbezogen |
| Ladungsfähige Anschrift | **offen** – Platzhalter, personenbezogen |
| E-Mail-Adresse | eingetragen |
| Telefonnummer | nicht angegeben – **DECISION REQUIRED**, siehe unten |
| Handelsregister | nicht vorhanden, korrekt als „besteht nicht“ ausgewiesen |
| USt-IdNr. | nicht angegeben – **DECISION REQUIRED**, siehe unten |

**Telefonnummer:** § 5 Abs. 1 Nr. 2 DDG verlangt Angaben, die eine schnelle
elektronische Kontaktaufnahme und unmittelbare Kommunikation ermöglichen,
einschließlich der E-Mail-Adresse. Ob die E-Mail-Adresse allein genügt oder eine
Telefonnummer nötig ist, ist eine Rechtsfrage und **nicht** automatisch zu
entscheiden – deshalb steht auf der Seite keine erfundene Nummer.

**Umsatzsteuer:** Die Seite benennt keine USt-IdNr. und keine
Kleinunternehmerregelung. Beides darf erst eingetragen werden, wenn es
tatsächlich zutrifft.

**Verantwortlich für den Inhalt (§ 18 Abs. 2 MStV):** bewusst **nicht**
aufgeführt, weil die Website keine journalistisch-redaktionellen Inhalte
enthält. Sollte später ein Blog, News- oder Pressebereich entstehen, ist die
Angabe zu ergänzen.

## 6. Aufsichtsbehörde

In der Datenschutzerklärung wird **keine** konkrete Aufsichtsbehörde genannt.
Zuständig ist die Behörde des Bundeslandes, in dem der Verantwortliche seinen
Sitz hat – das ergibt sich erst aus der noch offenen Anschrift. Eine erfundene
oder geratene Behörde wäre falsch.

## 7. Was dieses Dokument nicht ist

Keine Rechtsberatung. Es dokumentiert ausschließlich, welche technischen
Tatsachen geprüft wurden und welche Quellen für die Anbieterangaben verwendet
wurden, damit die Prüfung nachvollziehbar ist.
