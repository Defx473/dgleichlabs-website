#!/usr/bin/env python3
"""Interne Linkziele pruefen: Fragmente (#anker) und eindeutige IDs.

Aufruf:
    python -m unittest discover -s tools/tests -t tools
    python tools/tests/test_links.py

tools/check.py prueft, ob das ZIEL einer internen URL als Datei existiert -
aber nicht, ob ein Fragment (#abschnitt) dort auch wirklich als id vorhanden
ist, und nicht, ob eine Seite eine id mehrfach vergibt. Genau diese Luecke
schliesst dieses Modul, ohne die bestehende Linkpruefung zu duplizieren:

  * doppelte id innerhalb eines Dokuments  -> Fehler
  * href="#x"        -> id="x" muss auf DERSELBEN Seite stehen
  * href="/foo/#x"   -> public/foo/index.html muss existieren UND id="x" dort
  * href="#x"        -> id="x" auf der Startseite
  * mailto:/externe URLs werden nicht als lokale Fragmente gedeutet

Die Logik ist als reine Funktion umgesetzt und wird gegen den echten
public/-Baum UND gegen temporaere Fixtures geprueft (inkl. Negativfaellen).
Es finden KEINE Netzwerkzugriffe statt und es werden keine Produktionsdateien
veraendert.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"

ID = re.compile(r'\sid="([^"]*)"')
HREF = re.compile(r'href="([^"]*)"')

# Diese Praefixe sind keine lokalen HTML-Ziele.
EXTERNAL_PREFIXES = (
    "mailto:", "tel:", "http://", "https://", "//", "data:", "javascript:",
)


def document_ids(html: str) -> list[str]:
    return ID.findall(html)


def collect_documents(root: Path) -> dict[str, str]:
    """Bildet jeden ausgelieferten Pfad (relativ zur Wurzel) auf sein HTML ab."""
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.html"))
    }


def resolve_target(path: str, docs: dict[str, str]) -> str:
    """Bildet einen internen URL-Pfad auf den Dokument-Schluessel in docs ab."""
    if path in ("", "/"):
        return "index.html"
    relative = path.lstrip("/")
    if relative == "":
        return "index.html"
    if relative.endswith("/"):
        return relative + "index.html"
    if relative in docs:
        return relative
    if f"{relative}/index.html" in docs:
        return f"{relative}/index.html"
    return relative  # existiert nicht -> wird als fehlendes Ziel gemeldet


def fragment_problems(docs: dict[str, str]) -> list[str]:
    """Sammelt doppelte IDs und kaputte interne Fragmente ueber alle Dokumente."""
    problems: list[str] = []
    id_sets = {route: set(document_ids(html)) for route, html in docs.items()}

    for route in sorted(docs):
        html = docs[route]

        seen: dict[str, int] = {}
        for value in document_ids(html):
            seen[value] = seen.get(value, 0) + 1
        for value, count in seen.items():
            if count > 1:
                problems.append(f'{route}: doppelte id="{value}" ({count}\u00d7)')

        for href in HREF.findall(html):
            if not href or href.startswith(EXTERNAL_PREFIXES):
                continue
            if "#" not in href:
                continue  # Dateiexistenz prueft bereits tools/check.py
            before, fragment = href.split("#", 1)
            target_path = before.split("?", 1)[0]
            fragment = fragment.strip()
            if not fragment:
                problems.append(f'{route}: leerer Fragment-Anker in href="{href}"')
                continue
            if target_path == "":
                target_route = route
            else:
                target_route = resolve_target(target_path, docs)
            target_html = docs.get(target_route)
            if target_html is None:
                problems.append(
                    f'{route}: Anker-Ziel fehlt: href="{href}" '
                    f"(\u2192 {target_route} existiert nicht)"
                )
                continue
            if fragment not in id_sets[target_route]:
                problems.append(
                    f'{route}: Anker "{href}" \u2192 id="{fragment}" fehlt in {target_route}'
                )
    return problems


def fixture(files: dict[str, str]) -> dict[str, str]:
    """Schreibt eine kleine Dokumenten-Menge in ein temporaeres Verzeichnis."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for relative, html in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
        return collect_documents(root)


class DuplicateIdTests(unittest.TestCase):
    def test_duplicate_id_is_reported(self) -> None:
        docs = fixture({
            "index.html": '<section id="kontakt"></section><div id="kontakt"></div>',
        })
        problems = fragment_problems(docs)
        self.assertTrue(any("doppelte" in item for item in problems), problems)

    def test_unique_ids_are_not_reported(self) -> None:
        docs = fixture({
            "index.html": '<section id="kontakt"></section><div id="main"></div>',
        })
        self.assertEqual(fragment_problems(docs), [])

    def test_same_id_on_different_pages_is_allowed(self) -> None:
        docs = fixture({
            "index.html": '<section id="kontakt"></section>',
            "projekte/index.html": '<section id="kontakt"></section>',
        })
        self.assertEqual(fragment_problems(docs), [])


class FragmentTests(unittest.TestCase):
    def test_missing_same_page_fragment_is_reported(self) -> None:
        docs = fixture({"index.html": '<a href="#kontakt">Kontakt</a>'})
        problems = fragment_problems(docs)
        self.assertTrue(any("fehlt in index.html" in item for item in problems), problems)

    def test_valid_same_page_fragment_passes(self) -> None:
        docs = fixture({"index.html": '<a href="#kontakt">K</a><h2 id="kontakt">K</h2>'})
        self.assertEqual(fragment_problems(docs), [])

    def test_valid_cross_page_fragment_passes(self) -> None:
        docs = fixture({
            "index.html": '<a href="/fieldpro/#funktionen">F</a>',
            "fieldpro/index.html": '<h2 id="funktionen">Funktionen</h2>',
        })
        self.assertEqual(fragment_problems(docs), [])

    def test_missing_fragment_on_existing_target_page_is_reported(self) -> None:
        docs = fixture({
            "index.html": '<a href="/fieldpro/#funktionen">F</a>',
            "fieldpro/index.html": '<h2 id="problem">Problem</h2>',
        })
        problems = fragment_problems(docs)
        self.assertTrue(
            any("id=\"funktionen\" fehlt in fieldpro/index.html" in item for item in problems),
            problems,
        )

    def test_missing_target_page_is_reported(self) -> None:
        docs = fixture({"index.html": '<a href="/gibtsnicht/#x">X</a>'})
        problems = fragment_problems(docs)
        self.assertTrue(any("Anker-Ziel fehlt" in item for item in problems), problems)

    def test_start_page_fragment_resolves_to_index(self) -> None:
        docs = fixture({
            "projekte/index.html": '<a href="/#kontakt">K</a>',
            "index.html": '<section id="kontakt"></section>',
        })
        self.assertEqual(fragment_problems(docs), [])

    def test_empty_fragment_is_reported(self) -> None:
        docs = fixture({"index.html": '<a href="#">leer</a>'})
        problems = fragment_problems(docs)
        self.assertTrue(any("leerer Fragment-Anker" in item for item in problems), problems)


class NonFragmentTests(unittest.TestCase):
    def test_mailto_is_not_checked_as_fragment(self) -> None:
        docs = fixture({"index.html": '<a href="mailto:info@dgleichlabs.de#x">Mail</a>'})
        self.assertEqual(fragment_problems(docs), [])

    def test_external_url_is_ignored(self) -> None:
        docs = fixture({
            "index.html": '<a href="https://example.com/#whatever">extern</a>',
            "other/index.html": '<a href="//cdn.example.com/#x">cdn</a>',
        })
        self.assertEqual(fragment_problems(docs), [])

    def test_page_link_without_fragment_is_not_flagged_here(self) -> None:
        # Dateiexistenz prueft tools/check.py; hier darf nichts dupliziert werden.
        docs = fixture({"index.html": '<a href="/projekte/">Projekte</a>'})
        self.assertEqual(fragment_problems(docs), [])


class PathResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.docs = {"index.html": "", "projekte/index.html": "", "404.html": ""}

    def test_root_and_empty_map_to_index(self) -> None:
        self.assertEqual(resolve_target("/", self.docs), "index.html")
        self.assertEqual(resolve_target("", self.docs), "index.html")

    def test_trailing_slash_maps_to_index_html(self) -> None:
        self.assertEqual(resolve_target("/projekte/", self.docs), "projekte/index.html")

    def test_directory_without_slash_prefers_index(self) -> None:
        self.assertEqual(resolve_target("/projekte", self.docs), "projekte/index.html")

    def test_query_string_does_not_break_resolution(self) -> None:
        docs = {"index.html": '<h2 id="kontakt">K</h2>', "search/index.html": ""}
        problems = fragment_problems({
            **docs,
            "projekte/index.html": '<a href="/?q=1#kontakt">K</a>',
        })
        self.assertEqual(problems, [])

    def test_direct_html_file_resolves(self) -> None:
        self.assertEqual(resolve_target("/404.html", self.docs), "404.html")


class RealProjectTests(unittest.TestCase):
    """Der echte, ausgelieferte Stand muss frei von Anker-/ID-Fehlern sein."""

    def test_public_tree_has_no_fragment_or_id_problems(self) -> None:
        docs = collect_documents(PUBLIC)
        self.assertGreater(len(docs), 0)
        problems = fragment_problems(docs)
        self.assertEqual(problems, [], f"Anker-/ID-Fehler: {problems}")

    def test_every_page_defines_the_skip_link_target(self) -> None:
        docs = collect_documents(PUBLIC)
        for route, html in docs.items():
            with self.subTest(route=route):
                self.assertIn('id="main"', html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
