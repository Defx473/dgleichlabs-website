#!/usr/bin/env python3
"""DGleich Labs - Qualitaetspruefung fuer die fertige Website.

Prueft public/ so, wie es spaeter ausgeliefert wird:

  * Pflichtdateien vorhanden
  * interne Links aufloesbar (und keine toten Ziele)
  * keine externen Ressourcen (keine Fremdschriften, kein CDN, kein Tracking)
  * kein JavaScript, keine Inline-Styles (passt zur strengen CSP)
  * SEO/Meta: Titel, Description, Canonical, OpenGraph, genau eine H1
  * robots.txt + sitemap.xml stimmen mit den ausgelieferten Seiten ueberein
  * nicht freigegebene Projekte (published=false) tauchen NICHT auf
  * Barrierearmut-Basics (lang, Skip-Link, Landmarks, Alt-Texte)
  * Secret-Scan ueber das gesamte Repository
  * Build-/Asset-Frische (public/ passt zum Quellstand)

Aufruf:
    python tools/check.py
Exit-Code 0 = alles gruen, 1 = mindestens ein Problem.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

SITE = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
PROJECTS = json.loads((ROOT / "content" / "projects.json").read_text(encoding="utf-8"))

REQUIRED_FILES = [
    "index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "site.webmanifest",
    ".htaccess",
    "assets/styles.css",
    "assets/favicon.svg",
    "assets/favicon-32.png",
    "assets/apple-touch-icon.png",
    "assets/icon-192.png",
    "assets/icon-512.png",
    "assets/og.png",
    "projekte/index.html",
    "fieldpro/index.html",
    "impressum/index.html",
    "datenschutz/index.html",
]

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "privater Schlüssel"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS Access Key"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "GitHub Token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "API Key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack Token"),
    (re.compile(r"(?i)\b(password|passwort|secret|token)\s*[:=]\s*['\"][^'\"]{6,}['\"]"), "Passwort/Secret"),
    (re.compile(r"[A-Za-z]:\\\\Users|[A-Za-z]:/Users|/c/Users/|/home/[a-z]+/"), "persönlicher Dateipfad"),
]

# Zusaetzlich nur fuer ausgelieferte Dateien (public/, content/, src/):
# interne Adressen gehoeren nicht ins Frontend. Dokumentation darf sie nennen.
DELIVERED_PATTERNS = [
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "IP-Adresse"),
]
DELIVERED_DIRS = ("public", "content", "src")

SKIP_DIRS = {".git", "__pycache__", ".vscode", ".idea"}
SKIP_FILE_SUFFIXES = {".png", ".ico", ".jpg", ".jpeg", ".webp", ".zip", ".pdf"}


class Collector(HTMLParser):
    """Sammelt genau die Informationen, die fuer die Pruefung noetig sind."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[tuple[str, str]] = []          # (tag, href)
        self.srcs: list[tuple[str, str]] = []           # (tag, src)
        self.meta: dict[str, str] = {}
        self.title = ""
        self.headings: list[str] = []
        self.lang = ""
        self.image_alts: list[str | None] = []
        self.link_rels: list[tuple[str, str]] = []
        self.script_count = 0
        self.inline_style_attrs = 0
        self.empty_links: list[str] = []
        self._in_title = False
        self._in_heading: str | None = None
        self._heading_text: list[str] = []
        self._in_anchor = False
        self._anchor_text: list[str] = []
        self._anchor_href = ""
        self._anchor_has_img = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "html":
            self.lang = data.get("lang", "")
        if "style" in data:
            self.inline_style_attrs += 1
        if tag == "script":
            self.script_count += 1
        if tag == "meta":
            key = data.get("name") or data.get("property")
            if key:
                self.meta[key.lower()] = data.get("content", "")
        if tag == "title":
            self._in_title = True
        if tag in {"h1", "h2", "h3"}:
            self._in_heading = tag
            self._heading_text = []
        if tag == "a":
            self._in_anchor = True
            self._anchor_text = []
            self._anchor_href = data.get("href", "")
            self._anchor_has_img = False
            if self._anchor_href:
                self.hrefs.append(("a", self._anchor_href))
        if tag == "link":
            href = data.get("href", "")
            rel = data.get("rel", "")
            if href:
                self.hrefs.append(("link", href))
            if rel:
                self.link_rels.append((rel.lower(), href))
        if tag in {"img", "script", "iframe"}:
            src = data.get("src", "")
            if src:
                self.srcs.append((tag, src))
        if tag == "img":
            self.image_alts.append(data.get("alt"))
            if self._in_anchor:
                self._anchor_has_img = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "a":
            text = "".join(self._anchor_text).strip()
            if not text and not self._anchor_has_img:
                self.empty_links.append(self._anchor_href)
            self._in_anchor = False
        if tag in {"h1", "h2", "h3"} and self._in_heading:
            self.headings.append("".join(self._heading_text).strip())
            self._in_heading = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_heading:
            self._heading_text.append(data)
        if self._in_anchor:
            self._anchor_text.append(data)


def public_pages() -> list[Path]:
    return sorted(
        path for path in PUBLIC.rglob("*.html") if path.is_file()
    )


def resolve_internal(url: str) -> Path | None:
    """Bildet eine interne URL auf eine Datei in public/ ab."""
    path = url.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return PUBLIC / "index.html"
    if not path.startswith("/"):
        return None
    target = PUBLIC / path.lstrip("/")
    if path.endswith("/"):
        return target / "index.html"
    if target.is_dir():
        return target / "index.html"
    return target


def check_links(pages: list[Path], problems: list[str]) -> None:
    site_host = SITE["domain"]
    for page in pages:
        collector = Collector()
        collector.feed(page.read_text(encoding="utf-8"))
        rel = page.relative_to(ROOT).as_posix()

        for tag, href in collector.hrefs:
            if href.startswith(("mailto:", "#")):
                continue
            if href.startswith(("http://", "https://")):
                if site_host not in href:
                    problems.append(f"{rel}: externer Link ({tag}) -> {href}")
                elif tag == "link" and not href.startswith(SITE["url"]):
                    problems.append(f"{rel}: verdächtiger Link -> {href}")
                continue
            target = resolve_internal(href)
            if target is None:
                problems.append(f"{rel}: relativer Link nicht erlaubt -> {href}")
            elif not target.is_file():
                problems.append(f"{rel}: toter interner Link -> {href}")

        for tag, src in collector.srcs:
            if src.startswith(("http://", "https://", "//")):
                problems.append(f"{rel}: externe Ressource ({tag}) -> {src}")
            else:
                target = resolve_internal(src)
                if target is None or not target.is_file():
                    problems.append(f"{rel}: fehlende Ressource ({tag}) -> {src}")


def check_page_quality(pages: list[Path], problems: list[str]) -> None:
    for page in pages:
        collector = Collector()
        html = page.read_text(encoding="utf-8")
        collector.feed(html)
        rel = page.relative_to(ROOT).as_posix()

        if collector.lang != SITE["lang"]:
            problems.append(f"{rel}: html lang ist '{collector.lang}' statt '{SITE['lang']}'")
        if "{{" in html or "}}" in html:
            problems.append(f"{rel}: nicht aufgelöster Template-Marker")
        if collector.script_count:
            problems.append(f"{rel}: JavaScript gefunden (CSP verbietet script-src)")
        if collector.inline_style_attrs:
            problems.append(f"{rel}: Inline-Style-Attribut (CSP verbietet 'unsafe-inline')")

        title = collector.title.strip()
        description = collector.meta.get("description", "")
        if not title:
            problems.append(f"{rel}: <title> fehlt")
        elif len(title) > 70:
            problems.append(f"{rel}: <title> zu lang ({len(title)} Zeichen)")
        if not description:
            problems.append(f"{rel}: meta description fehlt")
        elif not 50 <= len(description) <= 165:
            problems.append(f"{rel}: meta description unpassend lang ({len(description)})")
        if "canonical" not in [rel_name for rel_name, _ in collector.link_rels]:
            problems.append(f"{rel}: canonical fehlt")
        for key in ("og:title", "og:description", "og:image", "og:url", "og:type"):
            if not collector.meta.get(key):
                problems.append(f"{rel}: {key} fehlt")
        if not collector.meta.get("twitter:card"):
            problems.append(f"{rel}: twitter:card fehlt")

        h1_count = sum(1 for heading in collector.headings if heading and heading in collector.headings[:1])
        h1s = [h for h in collector.headings if h]
        # Titel der Seite muss genau einmal als Ueberschrift erster Ebene auftauchen.
        first_tag_h1 = html.count("<h1")
        if first_tag_h1 != 1:
            problems.append(f"{rel}: {first_tag_h1}× <h1> (erwartet genau 1)")
        if h1_count == 0 and not h1s:
            problems.append(f"{rel}: keine Überschrift gefunden")

        for alt in collector.image_alts:
            if alt is None:
                problems.append(f"{rel}: <img> ohne alt-Attribut ({alt})")
        if collector.empty_links:
            problems.append(f"{rel}: Links ohne Text: {collector.empty_links}")

        if "skip-link" not in html:
            problems.append(f"{rel}: Skip-Link fehlt")
        if 'id="main"' not in html:
            problems.append(f"{rel}: Hauptbereich (#main) fehlt")
        if "aria-label" not in html:
            problems.append(f"{rel}: keine aria-label (Navigation nicht benannt)")


def check_no_unpublished(pages: list[Path], problems: list[str]) -> None:
    """Nicht freigegebene Projekte duerfen im Auslieferungsstand nicht auftauchen."""
    delivered = {page.relative_to(ROOT).as_posix(): page.read_text(encoding="utf-8") for page in pages}
    for project in PROJECTS["projects"]:
        if project.get("published", False):
            continue
        for rel, html in delivered.items():
            if project["name"].lower() in html.lower():
                problems.append(
                    f"{rel}: nicht freigegebenes Projekt '{project['name']}' ist öffentlich sichtbar"
                )


def check_sitemap_and_robots(pages: list[Path], problems: list[str]) -> None:
    sitemap = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    robots = (PUBLIC / "robots.txt").read_text(encoding="utf-8")

    if f"Sitemap: {SITE['url']}/sitemap.xml" not in robots:
        problems.append("robots.txt: Sitemap-Verweis fehlt")
    if "Disallow: /404.html" not in robots:
        problems.append("robots.txt: 404 sollte ausgeschlossen sein")

    locations = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    if len(locations) != len(SITE["routes"]):
        problems.append(
            f"sitemap.xml: {len(locations)} Einträge, erwartet {len(SITE['routes'])}"
        )
    for route in SITE["routes"]:
        expected = SITE["url"] + route["path"]
        if expected not in locations:
            problems.append(f"sitemap.xml: {expected} fehlt")
        if not (PUBLIC / route["file"]).is_file():
            problems.append(f"sitemap.xml: Ziel fehlt -> {route['file']}")

    delivered_pages = {
        page.relative_to(PUBLIC).as_posix() for page in pages if page.name != "404.html"
    }
    for route in SITE["routes"]:
        if route["file"] not in delivered_pages:
            problems.append(f"sitemap.xml: Seite nicht ausgeliefert -> {route['file']}")


def check_asset_dimensions(problems: list[str], notices: list[str]) -> None:
    """Bildmaße der Raster-Assets. Braucht Pillow (nur lokal verlässlich)."""
    try:
        from PIL import Image
    except ImportError:
        notices.append("Pillow fehlt – Bildmaße nicht geprüft (pip install pillow)")
        return

    expectations = {
        "assets/favicon-32.png": (32, 32),
        "assets/apple-touch-icon.png": (180, 180),
        "assets/icon-192.png": (192, 192),
        "assets/icon-512.png": (512, 512),
        "assets/og.png": (1200, 630),
    }
    for name, size in expectations.items():
        path = PUBLIC / name
        if not path.is_file():
            problems.append(f"Asset fehlt: {name}")
            continue
        with Image.open(path) as image:
            if image.size != size:
                problems.append(f"{name}: Größe {image.size}, erwartet {size}")


def check_css(problems: list[str]) -> None:
    """CSS-Regeln, die zur Datenschutz- und CSP-Linie passen müssen."""
    css = (PUBLIC / "assets" / "styles.css").read_text(encoding="utf-8")
    if "@import" in css:
        problems.append("styles.css: @import gefunden (externer Abruf möglich)")
    if "url(http" in css:
        problems.append("styles.css: externe Ressource über url(http…)")
    if "font-face" in css:
        problems.append("styles.css: @font-face gefunden (lokale Schriftsätze prüfen)")
    if "all: unset" in css:
        problems.append("styles.css: 'all: unset' gefunden (Barrierefreiheit prüfen)")


# Hoster-Dateien, die GitHub Pages bzw. Cloudflare Pages vorausgesetzt haben.
# Sie werden von netcup/Plesk nicht ausgewertet und duerfen deshalb nicht mehr
# im Auslieferungsstand liegen - sonst waeren sie wirkungslos UND zusaetzlich
# oeffentlich als Textdatei abrufbar.
DEPRECATED_HOSTING_FILES = ("_headers", "_redirects", ".nojekyll")


def check_hosting_config(problems: list[str]) -> None:
    """Sicherheits-Header und Weiterleitungen fuer Apache (netcup-Webhosting).

    Quelle der Regeln ist src/static/.htaccess, ausgeliefert als /.htaccess im
    httpdocs-Verzeichnis. Geprueft wird, dass die frueheren Cloudflare-Pages-
    Dateien verschwunden sind und die Apache-Datei die geforderten Regeln
    weiterhin enthaelt.
    """
    for name in DEPRECATED_HOSTING_FILES:
        if (PUBLIC / name).is_file():
            problems.append(
                f"{name}: veraltete Pages-Datei in public/ – fuer netcup gilt .htaccess "
                "(siehe docs/DEPLOYMENT.md)"
            )

    path = PUBLIC / ".htaccess"
    if not path.is_file():
        problems.append(".htaccess fehlt – Header/Weiterleitungen waeren beim Hoster wirkungslos")
        return

    raw = path.read_text(encoding="utf-8")
    # Nur echte Direktiven pruefen - Kommentare erklaeren Entscheidungen.
    active = "\n".join(
        line for line in raw.splitlines() if line.strip() and not line.lstrip().startswith("#")
    )
    for required in (
        "Content-Security-Policy",
        "default-src 'none'",
        "script-src 'none'",
        "frame-ancestors 'none'",
        'X-Content-Type-Options "nosniff"',
        "Referrer-Policy",
        "Strict-Transport-Security",
        "ErrorDocument 404 /404.html",
        "DirectoryIndex index.html",
        "Options -Indexes",
    ):
        if required not in active:
            problems.append(f".htaccess: '{required}' fehlt")
    if "includeSubDomains" in active:
        problems.append(".htaccess: HSTS includeSubDomains bewusst nicht setzen")
    if "Header always set" not in active:
        problems.append(".htaccess: keine Header gesetzt (Header always set fehlt)")
    if "www\\.dgleichlabs\\.de" not in active:
        problems.append(".htaccess: www-Weiterleitung auf die Hauptdomain fehlt")
    canonical = ("^index\\.html$",) + tuple(
        f"^{name}/index\\.html$" for name in ("projekte", "fieldpro", "impressum", "datenschutz")
    )
    for rule in canonical:
        if rule not in active:
            problems.append(f".htaccess: kanonische Weiterleitung {rule} fehlt")


def check_secrets(problems: list[str]) -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_FILE_SUFFIXES:
            continue
        if path.name in {"check.py"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        patterns = list(SECRET_PATTERNS)
        if path.parts[0] in DELIVERED_DIRS:
            patterns += DELIVERED_PATTERNS
        for pattern, label in patterns:
            for match in pattern.finditer(text):
                hit = match.group(0)
                # Loopback-/Dokumentationsadressen sind keine Secrets.
                if label == "IP-Adresse" and hit in {"127.0.0.1", "0.0.0.0", "255.255.255.255"}:
                    continue
                problems.append(f"{rel}: möglicher Treffer ({label}) -> {hit[:40]}")
                break


def check_production_gate(problems: list[str]) -> None:
    """Stellt sicher, dass die Deploy-Notbremse vorhanden UND verdrahtet ist.

    Bewusst nur die Verdrahtung: check.py darf NICHT an Platzhaltern scheitern,
    sonst waere lokale Entwicklung unmoeglich. Ob die Seite veroeffentlichbar
    ist, entscheidet allein tools/production_gate.py.
    """
    gate = ROOT / "tools" / "production_gate.py"
    if not gate.is_file():
        problems.append("production_gate.py fehlt – Deploy waere nicht blockiert")
        return

    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        problems.append("ci.yml fehlt – Prueflauf nicht nachvollziehbar")
        return
    text = workflow.read_text(encoding="utf-8")
    if "tools/production_gate.py" not in text:
        problems.append("ci.yml ruft production_gate.py nicht auf – Notbremse nicht verdrahtet")
    if "needs: production-gate" not in text:
        problems.append("ci.yml: das Paket haengt nicht am production-gate")

    # GitHub Pages ist nicht mehr das Production-Hosting: kein Workflow darf
    # einen Pages-Deploy enthalten, sonst gaebe es ein versehentliches zweites
    # Deployment neben netcup.
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        content = path.read_text(encoding="utf-8")
        for forbidden in (
            "actions/configure-pages",
            "actions/upload-pages-artifact",
            "actions/deploy-pages",
        ):
            if forbidden in content:
                problems.append(
                    f"{path.name}: {forbidden} – GitHub-Pages-Deployment nicht mehr erwünscht"
                )

    tests = ROOT / "tools" / "tests" / "test_production_gate.py"
    if not tests.is_file():
        problems.append("Tests fuer das production_gate fehlen")


def check_freshness(problems: list[str], notices: list[str]) -> None:
    for script in ("build.py", "assets.py"):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / script), "--check"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            continue
        output = f"{result.stdout}\n{result.stderr}"
        # assets.py braucht Pillow. Fehlt es, ist das eine Umgebungsgrenze und
        # kein inhaltlicher Fehler - z.B. in einer CI ohne Pillow.
        if script == "assets.py" and "Pillow ist nicht installiert" in output:
            notices.append("assets.py übersprungen – Pillow nicht installiert")
            continue
        problems.append(f"Frische: {script} meldet veralteten Stand")


def main() -> int:
    problems: list[str] = []
    notices: list[str] = []

    for name in REQUIRED_FILES:
        if not (PUBLIC / name).is_file():
            problems.append(f"Pflichtdatei fehlt: {name}")

    pages = public_pages()
    if not pages:
        problems.append("keine ausgelieferten HTML-Dateien gefunden")

    if pages:
        check_links(pages, problems)
        check_page_quality(pages, problems)
        check_no_unpublished(pages, problems)

    check_sitemap_and_robots(pages, problems)
    check_asset_dimensions(problems, notices)
    check_css(problems)
    check_hosting_config(problems)
    check_secrets(problems)
    check_production_gate(problems)
    check_freshness(problems, notices)

    print("DGleich Labs – Prüfbericht")
    print(f"  Grundlage: {len(pages)} Seite(n), {PUBLIC.relative_to(ROOT).as_posix()}/")
    for item in notices:
        print(f"  Hinweis: {item}")
    if problems:
        print(f"\n  {len(problems)} Problem(e):")
        for item in problems:
            print(f"   - {item}")
        return 1

    print("  Alle Prüfungen bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
