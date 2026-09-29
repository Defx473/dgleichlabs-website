#!/usr/bin/env python3
"""DGleich Labs - Website v0.1

Kleiner, abhaengigkeitsfreier Static-Site-Generator.

Aufruf:
    python tools/build.py            # erzeugt public/ (nur geaenderte Dateien)
    python tools/build.py --check    # Exit 1, wenn public/ nicht zum Quellstand passt

Quellen:
    content/site.json      Metadaten der Website
    content/projects.json  Projektliste (einzige Quelle fuer den Projektbereich)
    src/layout.html        Rahmen (Kopf, Navigation, Fuss)
    src/pages/*.html       Inhalte der einzelnen Seiten

Ergebnis:
    public/**              fertige, statische Dateien (direkt hostbar)

Es werden ausschliesslich Module aus der Python-Standardbibliothek verwendet.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SRC = ROOT / "src"
PUBLIC = ROOT / "public"

MARKER = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


@dataclass(frozen=True)
class Page:
    """Eine ausgelieferte Seite."""

    route: str
    source: str
    out: str
    title: str
    description: str
    robots: str = "index, follow"
    og_type: str = "website"
    active_nav: str = ""


PAGES: tuple[Page, ...] = (
    Page(
        route="/",
        source="index.html",
        out="index.html",
        title="DGleich Labs – Software, Apps & Digital Products",
        description=(
            "DGleich Labs ist eine unabhängige Software- und Entwicklungsmarke aus "
            "Deutschland. Schwerpunkte: mobile Apps, Desktop-Software, AI-Tools und "
            "digitale Produkte."
        ),
        active_nav="/",
    ),
    Page(
        route="/projekte/",
        source="projekte.html",
        out="projekte/index.html",
        title="Projekte – DGleich Labs",
        description=(
            "Projekte von DGleich Labs mit ehrlichem Status: in Entwicklung, geplant "
            "oder veröffentlicht. Ohne erfundene Zahlen, Bewertungen oder Store-Links."
        ),
        active_nav="/projekte/",
    ),
    Page(
        route="/fieldpro/",
        source="fieldpro.html",
        out="fieldpro/index.html",
        title="FieldPro – Mobile Dokumentation für Handwerk & Service",
        description=(
            "FieldPro ist eine mobile Dokumentationslösung für Handwerk und Service: "
            "Mängel, Fotos, Aufmaß und Berichte direkt beim Einsatz. Aktuell in der "
            "Pilotphase."
        ),
        active_nav="/fieldpro/",
    ),
    Page(
        route="/impressum/",
        source="impressum.html",
        out="impressum/index.html",
        title="Impressum – DGleich Labs",
        description=(
            "Impressum und Anbieterkennzeichnung der Website dgleichlabs.de. "
            "DGleich Labs ist die Geschäftsbezeichnung eines Einzelunternehmens."
        ),
        active_nav="/impressum/",
    ),
    Page(
        route="/datenschutz/",
        source="datenschutz.html",
        out="datenschutz/index.html",
        title="Datenschutz – DGleich Labs",
        description=(
            "Datenschutzerklärung für dgleichlabs.de: keine Cookies, kein Tracking, "
            "keine externen Schriftarten und keine Inhalte von Drittanbietern."
        ),
        active_nav="/datenschutz/",
    ),
    Page(
        route="/404.html",
        source="404.html",
        out="404.html",
        title="Seite nicht gefunden – DGleich Labs",
        description=(
            "Diese Adresse existiert nicht. Zurück zur Startseite von DGleich Labs."
        ),
        robots="noindex, follow",
    ),
)


def load_json(name: str) -> dict:
    path = CONTENT / name
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        sys.exit(f"FEHLER: {path} fehlt")
    except json.JSONDecodeError as error:
        sys.exit(f"FEHLER: {path} ist kein gültiges JSON ({error})")


def read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FEHLER: {path} fehlt")
    return path.read_text(encoding="utf-8")


def render_markers(template: str, values: dict[str, str], label: str) -> str:
    """Ersetzt {{ marker }} und bricht bei unbekannten Markern ab."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            sys.exit(f"FEHLER: {label} verwendet unbekannten Marker {{{{ {key} }}}}")
        return values[key]

    result = MARKER.sub(replace, template)
    leftover = MARKER.search(result)
    if leftover:
        sys.exit(f"FEHLER: nicht ersetzter Marker in {label}: {leftover.group(0)}")
    return result


# --------------------------------------------------------------------------
# Markup-Bausteine aus den Inhaltsdaten
# --------------------------------------------------------------------------


def render_nav(site: dict, active: str) -> str:
    lines = []
    for item in site["nav"]:
        current = ' aria-current="page"' if item["href"] == active and active else ""
        lines.append(
            f'          <li><a href="{html.escape(item["href"], quote=True)}"'
            f"{current}>{html.escape(item['label'])}</a></li>"
        )
    return "\n".join(lines)


def render_project_card(project: dict) -> str:
    areas = "\n".join(
        f"            <li>{html.escape(area)}</li>" for area in project.get("areas", [])
    )
    summary = html.escape(project.get("summary", ""))
    if not project.get("published", False) and project.get("note"):
        summary = f"{summary}\n            <span class=\"muted\">{html.escape(project['note'])}</span>"
    return (
        '          <li class="project-card">\n'
        '            <div class="project-head">\n'
        f"              <h3>{html.escape(project['name'])}</h3>\n"
        f'              <span class="badge">{html.escape(project["statusLabel"])}</span>\n'
        "            </div>\n"
        f"            <p>{summary}</p>\n"
        '            <ul class="project-areas">\n'
        f"{areas}\n"
        "            </ul>\n"
        "          </li>"
    )


def published_projects(projects: dict) -> list[dict]:
    return [item for item in projects["projects"] if item.get("published", False)]


def render_project_grid(projects: dict, limit: int | None = None) -> str:
    items = published_projects(projects)
    if limit is not None:
        items = items[:limit]
    if not items:
        return (
            '          <li class="card"><h3>Noch nichts veröffentlicht</h3>'
            "<p>Aktuell ist kein Projekt öffentlich verfügbar.</p></li>"
        )
    return "\n".join(render_project_card(item) for item in items)


# --------------------------------------------------------------------------
# Dateien erzeugen
# --------------------------------------------------------------------------


def build_files() -> dict[Path, str]:
    site = load_json("site.json")
    projects = load_json("projects.json")

    layout = read_text(SRC / "layout.html")
    url = site["url"]
    year = site["lastmod"][:4]

    files: dict[Path, str] = {}

    for page in PAGES:
        values = {
            "lang": site["lang"],
            "locale": site["locale"],
            "siteName": site["name"],
            "tagline": site["tagline"],
            "legalNote": site["legalNote"],
            "email": site["email"],
            "url": url,
            "year": year,
            "themeColor": site["themeColor"],
            "themeColorLight": site["themeColorLight"],
            "legalStand": site["legalStand"],
            "title": page.title,
            "ogTitle": page.title,
            "description": page.description,
            "robots": page.robots,
            "ogType": page.og_type,
            "canonical": url + page.route if page.route != "/404.html" else url + "/",
            "nav": render_nav(site, page.active_nav),
            "footerGithub": "",
            "projectsTeaser": render_project_grid(projects, limit=2),
            "projectsList": render_project_grid(projects),
        }
        # Erst den Seiteninhalt aufloesen, dann in den Rahmen einsetzen:
        # so funktionieren Marker (z. B. E-Mail, Claim) auch innerhalb der Seite.
        body = render_markers(read_text(SRC / "pages" / page.source), values, page.out)
        values["body"] = body
        files[PUBLIC / page.out] = render_markers(layout, values, page.out)

    # robots.txt ----------------------------------------------------------
    files[PUBLIC / "robots.txt"] = (
        "# DGleich Labs\n"
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /404.html\n\n"
        f"Sitemap: {url}/sitemap.xml\n"
    )

    # sitemap.xml ---------------------------------------------------------
    entries = []
    for route in site["routes"]:
        loc = url + route["path"]
        entries.append(
            "  <url>\n"
            f"    <loc>{html.escape(loc)}</loc>\n"
            f"    <lastmod>{site['lastmod']}</lastmod>\n"
            f"    <changefreq>{route['changefreq']}</changefreq>\n"
            f"    <priority>{route['priority']}</priority>\n"
            "  </url>"
        )
    files[PUBLIC / "sitemap.xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )

    # statische Hosting-Dateien (1:1 kopieren) ----------------------------
    static_dir = SRC / "static"
    if static_dir.is_dir():
        for source in sorted(static_dir.rglob("*")):
            if source.is_file():
                relative = source.relative_to(static_dir)
                files[PUBLIC / relative] = source.read_text(encoding="utf-8")

    # site.webmanifest ----------------------------------------------------
    manifest = {
        "name": site["name"],
        "short_name": site["name"],
        "lang": site["lang"],
        "start_url": "/",
        "scope": "/",
        "display": "browser",
        "background_color": site["themeColor"],
        "theme_color": site["themeColor"],
        "icons": [
            {"src": "/assets/favicon-32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    files[PUBLIC / "site.webmanifest"] = (
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )

    return files


def write_files(files: dict[Path, str], check: bool) -> int:
    stale: list[str] = []
    written = 0

    for path, content in sorted(files.items()):
        relative = path.relative_to(ROOT).as_posix()
        existing = path.read_text(encoding="utf-8") if path.is_file() else None
        if existing == content:
            continue
        if check:
            stale.append(relative)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" haelt die Zeilenenden im Repository stabil.
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        written += 1

    if check:
        if stale:
            print("FEHLER: public/ ist nicht aktuell. Bitte 'python tools/build.py' ausführen.")
            for name in stale:
                print(f"  veraltet/fehlt: {name}")
            return 1
        print("OK: public/ entspricht dem Quellstand.")
        return 0

    print(f"OK: {written} Datei(en) geschrieben, {len(files) - written} unverändert.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DGleich Labs Website-Generator")
    parser.add_argument(
        "--check",
        action="store_true",
        help="nur prüfen, ob public/ zum Quellstand passt (kein Schreiben)",
    )
    args = parser.parse_args()
    return write_files(build_files(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
