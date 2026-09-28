#!/usr/bin/env python3
"""Tests fuer das Production-Safety-Gate (tools/production_gate.py).

Aufruf:
    python -m unittest discover -s tools/tests -t tools
    python tools/tests/test_production_gate.py

Die Tests arbeiten ausschliesslich in temporaeren Ordnern und fassen weder
public/ noch src/ an. Es werden keine echten personenbezogenen Daten verwendet -
nur erfundene Beispielwerte, die ausdruecklich als Testdaten erkennbar sind.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import production_gate as gate  # noqa: E402


def scan_html(html: str) -> list[gate.Finding]:
    """Hilfsfunktion: einen HTML-Text wie eine ausgelieferte Seite pruefen."""
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.html"
        page.write_text(html, encoding="utf-8")
        return gate.scan_directory(Path(tmp))


def labels(findings: list[gate.Finding]) -> list[str]:
    return [item.label for item in findings]


class RequiredPlaceholderTests(unittest.TestCase):
    """Die vom Auftrag geforderten Platzhalter muessen sicher erkannt werden."""

    def test_vollstaendiger_name_is_detected(self) -> None:
        self.assertEqual(labels(scan_html("<p>Inhaber: [VOLLSTÄNDIGER NAME]</p>")),
                         ["[VOLLSTÄNDIGER NAME]"])

    def test_anschrift_is_detected(self) -> None:
        self.assertEqual(labels(scan_html("<p>[ANSCHRIFT]</p>")), ["[ANSCHRIFT]"])

    def test_telefon_is_detected(self) -> None:
        self.assertEqual(labels(scan_html("<p>Telefon: [TELEFON]</p>")), ["[TELEFON]"])

    def test_every_required_placeholder_is_covered_by_known_list(self) -> None:
        for placeholder in gate.REQUIRED_PLACEHOLDERS:
            with self.subTest(placeholder=placeholder):
                self.assertEqual(labels(scan_html(f"<p>{placeholder}</p>")), [placeholder])

    def test_actual_project_placeholders_are_detected(self) -> None:
        """Der reale, noch offene Bestand wird erkannt."""
        for placeholder in gate.KNOWN_PLACEHOLDERS:
            with self.subTest(placeholder=placeholder):
                self.assertEqual(labels(scan_html(f"<p>{placeholder}</p>")), [placeholder])

    def test_historical_placeholder_wording_is_still_detected(self) -> None:
        """Umbenannte Platzhalter duerfen nicht durchs Raster fallen."""
        for placeholder in ("[STRASSE UND HAUSNUMMER]", "[PLZ UND ORT]",
                            "[HOSTING-PROVIDER]", "[E-MAIL-PROVIDER eintragen]"):
            with self.subTest(placeholder=placeholder):
                self.assertEqual(labels(scan_html(f"<p>{placeholder}</p>")), [placeholder])

    def test_multiline_placeholder_is_detected(self) -> None:
        """Impressum hat Platzhalter, die über zwei Zeilen umbrechen."""
        html = "<p>[ggf. Kleinunternehmerregelung nach § 19 UStG – nur eintragen,\n wenn zutreffend]</p>"
        self.assertEqual(len(scan_html(html)), 1)

    def test_line_number_points_at_the_placeholder(self) -> None:
        html = "<html>\n<body>\n<p>Inhaber: [VOLLSTÄNDIGER NAME]</p>\n</body>\n</html>"
        self.assertEqual(scan_html(html)[0].line, 3)

    def test_kind_is_platzhalter(self) -> None:
        self.assertEqual(scan_html("<p>[TELEFON]</p>")[0].kind, "platzhalter")


class ForbiddenMarkerTests(unittest.TestCase):
    """Der offene Pruefhinweis blockiert ebenfalls."""

    def test_legal_review_marker_is_detected(self) -> None:
        html = "<p>LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT</p>"
        findings = scan_html(html)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "pruefhinweis")

    def test_marker_is_detected_next_to_placeholder(self) -> None:
        html = "<p>[TELEFON]</p>\n<p>LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT</p>"
        self.assertEqual({item.kind for item in scan_html(html)}, {"platzhalter", "pruefhinweis"})


class FalsePositiveTests(unittest.TestCase):
    """Code-/Attributfragmente duerfen den Deploy nicht blockieren."""

    def test_json_like_fragment_is_ignored(self) -> None:
        self.assertEqual(scan_html('<script>var a = ["Mobile", "Plattform"];</script>'), [])

    def test_attribute_selector_is_ignored(self) -> None:
        self.assertEqual(scan_html('<style>[aria-current="page"] { color: red; }</style>'), [])

    def test_index_access_is_ignored(self) -> None:
        self.assertEqual(scan_html("<p>argv[1] und list[0]</p>"), [])

    def test_square_brackets_without_letters_are_ignored(self) -> None:
        self.assertEqual(scan_html("<p>[1] [2] [-3] [  ]</p>"), [])

    def test_clean_page_is_not_flagged(self) -> None:
        html = (
            "<html lang=\"de\"><head><title>DGleich Labs</title></head>"
            "<body><h1>DGleich Labs</h1><p>Software, Apps, Ideen.</p></body></html>"
        )
        self.assertEqual(scan_html(html), [])


class OutcomeTests(unittest.TestCase):
    """Exit-Code und Bericht verhalten sich wie gefordert."""

    def _run(self, html: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text(html, encoding="utf-8")
            findings = gate.scan_directory(root)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = gate.report(findings, root, verbose=True)
        return code, buffer.getvalue()

    def test_blocked_page_exits_non_zero(self) -> None:
        code, output = self._run("<p>Inhaber: [VOLLSTÄNDIGER NAME]</p>")
        self.assertNotEqual(code, 0)
        self.assertIn("BLOCKIERT", output)

    def test_clean_page_exits_zero(self) -> None:
        code, output = self._run("<p>DGleich Labs</p>")
        self.assertEqual(code, 0)
        self.assertIn("freigegeben", output)

    def test_report_lists_file_and_line(self) -> None:
        code, output = self._run("<p>[TELEFON]</p>")
        self.assertNotEqual(code, 0)
        self.assertIn("index.html", output)
        self.assertIn("Zeile", output)

    def test_missing_directory_exits_two(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = gate.main(["--path", "gibt-es-nicht-ordner"])
        self.assertEqual(code, 2)
        self.assertIn("nicht gefunden", buffer.getvalue())


class RealProjectTests(unittest.TestCase):
    """Der Gate gegen den echten Stand dieses Projekts."""

    def test_current_public_tree_is_blocked(self) -> None:
        findings = gate.scan_directory(gate.ROOT / "public")
        self.assertNotEqual(findings, [], "Erwartet: aktuell noch blockiert")

    def test_only_expected_items_are_open(self) -> None:
        """Blocker duerfen ausschliesslich die zwei lokalen Angaben sein.

        So faellt sofort auf, wenn irgendwo ein vergessener Platzhalter steht -
        der Gate bleibt dabei fuer neue, unbekannte Klammern scharf.
        """
        findings = gate.scan_directory(gate.ROOT / "public")
        unexpected = [item for item in findings if item.text not in gate.EXPECTED_OPEN]
        self.assertEqual(unexpected, [], f"Unerwartete offene Stellen: {unexpected}")

    def test_both_legal_pages_are_blocked_for_the_same_two_inputs(self) -> None:
        findings = gate.scan_directory(gate.ROOT / "public")
        placeholders = {item.label for item in findings if item.kind == "platzhalter"}
        self.assertEqual(placeholders, set(gate.KNOWN_PLACEHOLDERS))
        files = {item.path.name for item in findings}
        self.assertEqual(files, {"index.html"})
        pages = {item.path.parent.name for item in findings}
        self.assertEqual(pages, {"impressum", "datenschutz"})

    def test_gate_needs_no_network_or_secrets(self) -> None:
        source = (gate.ROOT / "tools" / "production_gate.py").read_text(encoding="utf-8")
        for banned in ("requests", "urllib.request", "http://", "https://"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned, source)


class WiringTests(unittest.TestCase):
    """Die Notbremse selbst darf nicht stillschweigend verschwinden.

    check.py prueft nur die VERDRAHTUNG (Datei vorhanden, Workflow ruft sie auf),
    nicht die Platzhalter - sonst waere lokale Entwicklung unmoeglich.
    """

    def setUp(self) -> None:
        if str(gate.ROOT / "tools") not in sys.path:
            sys.path.insert(0, str(gate.ROOT / "tools"))
        import check  # noqa: PLC0415

        self.check = check
        self.original_root = check.ROOT

    def tearDown(self) -> None:
        self.check.ROOT = self.original_root

    def test_missing_gate_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.check.ROOT = Path(tmp)
            problems: list[str] = []
            self.check.check_production_gate(problems)
        self.assertTrue(any("production_gate.py fehlt" in item for item in problems), problems)

    def test_unwired_workflow_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            (root / "tools" / "production_gate.py").write_text("", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "pages.yml").write_text(
                "name: irgendwas\n", encoding="utf-8"
            )
            self.check.ROOT = root
            problems = []
            self.check.check_production_gate(problems)
        self.assertTrue(any("nicht verdrahtet" in item for item in problems), problems)
        self.assertTrue(
            any("haengt nicht am production-gate" in item for item in problems), problems
        )

    def test_missing_tests_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            (root / "tools" / "production_gate.py").write_text("", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "pages.yml").write_text(
                "run: python tools/production_gate.py\nneeds: production-gate\n",
                encoding="utf-8",
            )
            self.check.ROOT = root
            problems = []
            self.check.check_production_gate(problems)
        self.assertTrue(any("Tests fuer das production_gate fehlen" in item for item in problems),
                        problems)

    def test_real_project_wiring_is_clean(self) -> None:
        problems: list[str] = []
        self.check.check_production_gate(problems)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
