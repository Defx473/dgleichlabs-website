#!/usr/bin/env python3
"""DGleich Labs - Production-Safety-Gate.

Diese Pruefung ist die NOTBREMSE fuer die Veroeffentlichung: sie laeuft in der
Deployment-Pipeline VOR dem Hochladen des Artefakts und bricht ab, solange die
ausgelieferte Website noch Platzhalter oder offene Pruefhinweise enthaelt.

Warum getrennt von tools/check.py:
  * tools/check.py prueft die Qualitaet der Seite und muss auch dann gruen sein,
    wenn die Rechtstexte noch nicht final sind (lokale Entwicklung).
  * Dieses Gate prueft ausschliesslich die Veroeffentlichungsreife. Es ist
    absichtlich NICHT Teil des normalen Builds - lokal darf man jederzeit
    bauen und ansehen (siehe README, Abschnitt "Production Gate").

Erkannt wird:
  1. Bekannte Pflicht-Platzhalter (unten explizit aufgelistet).
  2. Jede weitere eckige Klammer mit Text in der ausgelieferten Seite, sofern
     sie nicht wie ein Attribut-/JSON-Fragment aussieht. Damit fallen auch
     spaeter ergaenzte Platzhalter auf, ohne dass diese Datei gepflegt werden
     muss.
  3. Der Pruefhinweis "LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT".

Aufruf:
    python tools/production_gate.py                       # Exit 1 = blockiert
    python tools/production_gate.py --path public         # anderer Ordner
    python tools/production_gate.py --list                # alle Treffer zeigen

Es werden KEINE Daten ergaenzt oder erfunden. Das Gate blockiert nur.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# Platzhalter, die laut Auftrag sicher erkannt werden muessen. "[ANSCHRIFT]"
# ist historisch: im Impressum ist er in zwei praezisere Platzhalter aufgeteilt
# ([STRASSE UND HAUSNUMMER] und [PLZ UND ORT]). Beide Formen werden erkannt.
REQUIRED_PLACEHOLDERS = (
    "[VOLLSTÄNDIGER NAME]",
    "[ANSCHRIFT]",
    "[TELEFON]",
)

# Vollstaendiger Bestand zum Zeitpunkt der Einfuehrung (dokumentiert den
# tatsaechlichen Zustand, damit im Bericht nachvollziehbar bleibt, was blockiert).
KNOWN_PLACEHOLDERS = (
    "[VOLLSTÄNDIGER NAME]",
    "[STRASSE UND HAUSNUMMER]",
    "[PLZ UND ORT]",
    "[TELEFON]",
    "[HOSTING-PROVIDER]",
    "[E-MAIL-PROVIDER eintragen]",
)

# Offene Pruefhinweise: Text, der die Seite selbst als unfertig ausweist.
FORBIDDEN_MARKERS = ("LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT",)

# Eckige Klammer mit Inhalt. Ausgeschlossen sind Zeichen, die auf Code
# hindeuten: Quotes, Gleichheitszeichen, spitze Klammern (Templates) und
# verschachtelte Klammern. Damit fliegen `[aria-current="page"]` und
# `["Mobile", "Plattform"]` nicht faelschlich auf.
PLACEHOLDER = re.compile(r"\[([^\[\]\"<>=]{2,120})\]", re.S)

# Ein Treffer muss mindestens einen Buchstaben enthalten -> `argv[1]` bleibt ruhig.
HAS_LETTER = re.compile(r"[A-Za-zÄÖÜäöüß]")

SKIP_SUFFIXES = {".png", ".ico", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".woff", ".woff2"}
SKIP_DIRS = {".git", "__pycache__", "node_modules"}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    text: str
    kind: str  # "platzhalter" | "pruefhinweis"

    @property
    def label(self) -> str:
        return " ".join(self.text.split())[:80]


def scan_text(text: str, path: Path) -> list[Finding]:
    """Findet alle blockierenden Stellen in einem ausgelieferten Text."""
    findings: list[Finding] = []
    for match in PLACEHOLDER.finditer(text):
        inner = match.group(1)
        if not HAS_LETTER.search(inner):
            continue
        findings.append(
            Finding(path, text.count("\n", 0, match.start()) + 1, f"[{inner}]", "platzhalter")
        )
    for marker in FORBIDDEN_MARKERS:
        start = 0
        while (index := text.find(marker, start)) != -1:
            findings.append(
                Finding(path, text.count("\n", 0, index) + 1, marker, "pruefhinweis")
            )
            start = index + len(marker)
    return findings


def scan_directory(root: Path) -> list[Finding]:
    """Prueft alle ausgelieferten Textdateien unterhalb von root."""
    findings: list[Finding] = []
    if not root.is_dir():
        return findings
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text(text, path))
    return findings


def display(path: Path) -> str:
    """Pfad möglichst knapp anzeigen: relativ zum Projektwurzelverzeichnis."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def report(findings: list[Finding], root: Path, verbose: bool) -> int:
    print("DGleich Labs - Production-Safety-Gate")
    print(f"  Prüfgrundlage: {display(root)}/")

    if not findings:
        print("  Keine Platzhalter und keine offenen Prüfhinweise gefunden.")
        print("  Ergebnis: Veröffentlichung freigegeben.")
        return 0

    by_file: dict[Path, list[Finding]] = {}
    for finding in findings:
        by_file.setdefault(finding.path, []).append(finding)

    print()
    print(f"  BLOCKIERT: {len(findings)} offene Stelle(n) in {len(by_file)} Datei(en).")
    for path, items in by_file.items():
        print(f"   - {display(path)}")
        shown = items if verbose else items[:3]
        for item in shown:
            print(f"       Zeile {item.line:>4}  {item.kind}: {item.label}")
        if len(items) > len(shown):
            print(f"       … und {len(items) - len(shown)} weitere (--list zeigt alle)")

    print()
    print("  Warum das blockiert: Eine öffentlich ausgelieferte Seite mit")
    print("  Platzhaltern im Impressum oder in der Datenschutzerklärung verletzt")
    print("  die Pflichtangaben. Der Deploy muss bis zur Klärung ausbleiben.")
    print()
    print("  Vorgehen:")
    print("   1. src/pages/impressum.html und src/pages/datenschutz.html ergänzen")
    print("      (echte Angaben eintragen, nichts erfinden).")
    print("   2. Den Hinweis 'LEGAL REVIEW REQUIRED BEFORE PUBLIC DEPLOYMENT'")
    print("      erst nach der rechtlichen Prüfung entfernen.")
    print("   3. python tools/build.py && python tools/check.py")
    print("   4. python tools/production_gate.py   # muss jetzt 0 liefern")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Blockiert die Veröffentlichung, solange Platzhalter in der Seite stehen."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=ROOT / "public",
        help="zu prüfender Ordner (Standard: public/)",
    )
    parser.add_argument("--list", dest="verbose", action="store_true", help="alle Treffer zeigen")
    args = parser.parse_args(argv)

    root = args.path if args.path.is_absolute() else (ROOT / args.path)
    if not root.is_dir():
        print(f"FEHLER: Prüfordner nicht gefunden: {root.as_posix()}")
        return 2

    return report(scan_directory(root), root, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
