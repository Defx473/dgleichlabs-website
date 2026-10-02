#!/usr/bin/env python3
"""DGleich Labs - sauberes Deployment-Paket aus public/ erzeugen.

Der Inhalt von public/ ist das Produkt. In public/ liegen aber auch reine
Repository-Artefakte: vor allem .gitkeep-Dateien, die leere Ordner (z. B.
public/assets/projects/<id>/) im Git halten. Diese Dateien gehoeren NICHT in
einen Upload. Dieses Tool packt ausschliesslich die tatsaechlich ausgelieferten
Produktionsdateien und laesst Entwicklungsartefakte weg.

Sicherheit:
  * Es entsteht KEIN Paket, wenn public/ nicht zum Quellstand passt
    (tools/build.py --check) oder das Production-Gate rot ist
    (tools/production_gate.py). Die Notbremse bleibt damit vor dem Upload.
  * Gepackt wird ausschliesslich unterhalb von public/ (keine Repo-Dateien).

Aufruf:
    python tools/package.py                    # -> dgleichlabs-deploy-final.zip
    python tools/package.py --output x.zip     # anderer Zielname
    python tools/package.py --list             # nur die Dateiliste zeigen
    python tools/package.py --check [zip]      # vorhandenes ZIP pruefen

Es werden nur Module aus der Python-Standardbibliothek verwendet.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path, PurePosixPath

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
DEFAULT_OUTPUT = ROOT / "dgleichlabs-deploy-final.zip"

# Versteckte Dateien fliegen grundsaetzlich raus - ausser der Hosting-Datei
# .htaccess, die zwingend mit hochgeladen werden muss.
KEEP_HIDDEN = {".htaccess"}

# Nie ins Paket.
EXCLUDE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".gitkeep",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
}
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    ".tmp",
    "dist-cache",
}
EXCLUDE_SUFFIXES = {
    ".pyc", ".pyo", ".py", ".log", ".tmp", ".swp", ".swo",
    ".orig", ".rej", ".bak", ".zip", ".ds_store",
}

# Dateien, die in jedem Paket vorhanden sein muessen (sonst Abbruch).
REQUIRED_FILES = (
    ".htaccess",
    "index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "site.webmanifest",
    "assets/styles.css",
    "projekte/index.html",
    "fieldpro/index.html",
    "dimitri-ai-studio/index.html",
    "project-nova/index.html",
    "ai-game-assistant/index.html",
    "karto/index.html",
    "impressum/index.html",
    "datenschutz/index.html",
)

# Fester Zeitstempel -> das Archiv ist inhaltlich reproduzierbar.
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)


def is_excluded(relative: PurePosixPath) -> bool:
    """True, wenn die Datei nicht in ein Deployment-Paket gehoert."""
    name = relative.name
    lowered = name.lower()
    if name in KEEP_HIDDEN:
        return False
    if any(part in EXCLUDE_DIRS for part in relative.parts):
        return True
    if name in EXCLUDE_NAMES or lowered in {n.lower() for n in EXCLUDE_NAMES}:
        return True
    if lowered in EXCLUDE_SUFFIXES or relative.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if name.endswith("~"):
        return True
    # Versteckte Dateien/Ordner (z. B. .gitkeep) grundsaetzlich nicht ausliefern.
    if any(part.startswith(".") for part in relative.parts):
        return True
    return False


def collect() -> tuple[list[PurePosixPath], list[PurePosixPath]]:
    """Liefert (aufzunehmende, uebersprungene) Pfade relativ zu public/."""
    included: list[PurePosixPath] = []
    excluded: list[PurePosixPath] = []
    for path in sorted(PUBLIC.rglob("*")):
        if not path.is_file():
            continue
        relative = PurePosixPath(path.relative_to(PUBLIC).as_posix())
        if is_excluded(relative):
            excluded.append(relative)
        else:
            included.append(relative)
    return included, excluded


def ensure_releasable() -> None:
    """Bricht ab, wenn public/ nicht aktuell oder nicht freigegeben ist."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build.py"), "--check"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        print("FEHLER: public/ passt nicht zum Quellstand - kein Paket erzeugt.")
        print(f"  {result.stdout.strip()}\n  {result.stderr.strip()}".rstrip())
        raise SystemExit(1)

    if str(ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools"))
    import production_gate  # noqa: PLC0415

    findings = production_gate.scan_directory(PUBLIC)
    if findings:
        production_gate.report(findings, PUBLIC, verbose=True)
        print()
        print("FEHLER: Das Production-Gate ist rot - es wird KEIN Paket erzeugt.")
        raise SystemExit(1)

    print("OK: public/ ist aktuell und vom Production-Gate freigegeben.")


def build_zip(included: list[PurePosixPath], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative in included:
            info = zipfile.ZipInfo(relative.as_posix(), date_time=ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (PUBLIC / relative).read_bytes())


def inspect_zip(path: Path) -> list[str]:
    """Prueft ein ZIP gegen den erwarteten Inhalt. Leere Liste = sauber."""
    problems: list[str] = []
    if not path.is_file():
        return [f"ZIP fehlt: {path.name}"]

    expected, _ = collect()
    expected_names = {item.as_posix() for item in expected}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()

    for name in sorted(names):
        relative = PurePosixPath(name)
        if name.startswith("/") or ".." in relative.parts:
            problems.append(f"unsicherer Pfad im ZIP: {name}")
        elif is_excluded(relative):
            problems.append(f"Entwicklungsartefakt im ZIP: {name}")

    for missing in sorted(expected_names - set(names)):
        problems.append(f"fehlende Datei im ZIP: {missing}")
    for extra in sorted(set(names) - expected_names):
        problems.append(f"unerwartete Datei im ZIP: {extra}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deployment-Paket aus public/ erzeugen.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"ZIP-Ziel (Standard: {DEFAULT_OUTPUT.name})")
    parser.add_argument("--list", dest="list_only", action="store_true",
                        help="nur die Dateiliste zeigen, nichts schreiben")
    parser.add_argument("--check", type=Path, nargs="?", const=DEFAULT_OUTPUT,
                        help="vorhandenes ZIP pruefen (Standard: Standardpfad)")
    args = parser.parse_args(argv)

    if not PUBLIC.is_dir():
        print(f"FEHLER: {PUBLIC.as_posix()} fehlt - erst 'python tools/build.py' ausfuehren.")
        return 2

    included, excluded = collect()

    if args.list_only:
        print(f"Paketinhalt ({len(included)} Datei(en)):")
        for item in included:
            print(f"  + {item.as_posix()}")
        if excluded:
            print(f"\nAusgeschlossen ({len(excluded)} Artefakt(e)):")
            for item in excluded:
                print(f"  - {item.as_posix()}")
        return 0

    if args.check is not None:
        problems = inspect_zip(args.check)
        print(f"Pruefe {args.check.as_posix()}")
        if problems:
            for item in problems:
                print(f"  PROBLEM: {item}")
            return 1
        print(f"  OK: {len(included)} Datei(en), keine Artefakte, keine Fremddateien.")
        return 0

    ensure_releasable()

    missing = [name for name in REQUIRED_FILES if not (PUBLIC / name).is_file()]
    if missing:
        print(f"FEHLER: Pflichtdateien fehlen in public/: {', '.join(missing)}")
        return 1

    allowed = {item.as_posix() for item in included}
    if set(REQUIRED_FILES) - allowed:
        print("FEHLER: Pflichtdateien wuerden herausgefiltert: "
              f"{', '.join(sorted(set(REQUIRED_FILES) - allowed))}")
        return 1

    build_zip(included, args.output)
    print(f"OK: {len(included)} Datei(en) -> {args.output.name}")
    if excluded:
        print(f"  ausgeschlossen: {', '.join(item.as_posix() for item in excluded)}")

    problems = inspect_zip(args.output)
    if problems:
        for item in problems:
            print(f"  PROBLEM: {item}")
        return 1
    print("  Selbstpruefung: Inhalt vollstaendig, keine Entwicklungsartefakte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
