#!/usr/bin/env python3
"""Tests fuer das Deployment-Paket (tools/package.py).

Aufruf:
    python -m unittest discover -s tools/tests -t tools
    python tools/tests/test_package.py

Geprueft wird die Paketlogik gegen den echten public/-Baum: Pflichtdateien
sind enthalten, .htaccess bleibt drin, Entwicklungsartefakte (.gitkeep,
.DS_Store, __pycache__, *.pyc ...) fliegen raus, und das erzeugte ZIP enthaelt
ausschliesslich Dateien unterhalb von public/.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import package as pkg  # noqa: E402


class ExclusionRuleTests(unittest.TestCase):
    def test_htaccess_is_kept(self) -> None:
        self.assertFalse(pkg.is_excluded(PurePosixPath(".htaccess")))

    def test_gitkeep_is_excluded(self) -> None:
        self.assertTrue(pkg.is_excluded(PurePosixPath(".gitkeep")))
        self.assertTrue(pkg.is_excluded(PurePosixPath("assets/projects/x/.gitkeep")))

    def test_common_os_artifacts_are_excluded(self) -> None:
        for name in (".DS_Store", "Thumbs.db", "desktop.ini", ".gitignore"):
            with self.subTest(name=name):
                self.assertTrue(pkg.is_excluded(PurePosixPath(name)))

    def test_python_build_artifacts_are_excluded(self) -> None:
        self.assertTrue(pkg.is_excluded(PurePosixPath("__pycache__/x.pyc")))
        self.assertTrue(pkg.is_excluded(PurePosixPath("cache/x.pyo")))

    def test_logs_and_archives_are_excluded(self) -> None:
        self.assertTrue(pkg.is_excluded(PurePosixPath("debug.log")))
        self.assertTrue(pkg.is_excluded(PurePosixPath("backup.zip")))

    def test_editor_swap_and_backup_files_are_excluded(self) -> None:
        self.assertTrue(pkg.is_excluded(PurePosixPath("index.html~")))
        self.assertTrue(pkg.is_excluded(PurePosixPath("index.html.orig")))

    def test_normal_production_files_pass(self) -> None:
        for name in ("index.html", "assets/styles.css", "robots.txt", "sitemap.xml"):
            with self.subTest(name=name):
                self.assertFalse(pkg.is_excluded(PurePosixPath(name)))


class CollectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.included, self.excluded = pkg.collect()
        self.names = {item.as_posix() for item in self.included}

    def test_required_files_are_included(self) -> None:
        missing = set(pkg.REQUIRED_FILES) - self.names
        self.assertEqual(missing, set(), f"Pflichtdateien fehlen im Paket: {missing}")

    def test_htaccess_is_included(self) -> None:
        self.assertIn(".htaccess", self.names)

    def test_project_detail_pages_are_included(self) -> None:
        for name in ("fieldpro/index.html", "dimitri-ai-studio/index.html",
                     "project-nova/index.html", "ai-game-assistant/index.html",
                     "karto/index.html"):
            with self.subTest(name=name):
                self.assertIn(name, self.names)

    def test_no_development_artifacts_are_included(self) -> None:
        for name in self.names:
            with self.subTest(name=name):
                self.assertFalse(pkg.is_excluded(PurePosixPath(name)))

    def test_gitkeep_files_are_excluded(self) -> None:
        self.assertTrue(self.excluded, "Erwartet mindestens eine uebersprungene Datei")
        self.assertTrue(all(item.name == ".gitkeep" for item in self.excluded),
                        self.excluded)

    def test_all_paths_stay_inside_public(self) -> None:
        for item in self.included + self.excluded:
            with self.subTest(path=item.as_posix()):
                self.assertFalse(item.is_absolute())
                self.assertNotIn("..", item.parts)

    def test_included_files_exist_under_public(self) -> None:
        for item in self.included:
            with self.subTest(path=item.as_posix()):
                self.assertTrue((pkg.PUBLIC / item).is_file())


class ZipTests(unittest.TestCase):
    def _write(self, names: list[str]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "pkg.zip"
        with zipfile.ZipFile(out, "w") as archive:
            for name in names:
                archive.writestr(name, b"x")
        return out

    def test_built_zip_is_clean_and_complete(self) -> None:
        included, _ = pkg.collect()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "deploy.zip"

        pkg.build_zip(included, out)

        self.assertEqual(pkg.inspect_zip(out), [])
        with zipfile.ZipFile(out) as archive:
            names = archive.namelist()
        self.assertEqual(sorted(names), sorted(item.as_posix() for item in included))
        self.assertIn(".htaccess", names)
        self.assertFalse(any(name.endswith(".gitkeep") for name in names))

    def test_inspect_flags_gitkeep_as_artifact(self) -> None:
        out = self._write([".gitkeep", "assets/projects/x/.gitkeep"])
        problems = pkg.inspect_zip(out)
        self.assertTrue(any("Entwicklungsartefakt" in item for item in problems), problems)

    def test_inspect_flags_path_traversal(self) -> None:
        out = self._write(["../evil.html"])
        problems = pkg.inspect_zip(out)
        self.assertTrue(any("unsicherer Pfad" in item for item in problems), problems)

    def test_inspect_flags_missing_files(self) -> None:
        out = self._write([".htaccess"])
        problems = pkg.inspect_zip(out)
        self.assertTrue(any("fehlende Datei" in item for item in problems), problems)

    def test_inspect_flags_unknown_extra_files(self) -> None:
        out = self._write(["quellcode.py", "index.html"])
        problems = pkg.inspect_zip(out)
        self.assertTrue(any("unerwartete Datei" in item for item in problems), problems)

    def test_inspect_reports_missing_zip(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        problems = pkg.inspect_zip(Path(tmp.name) / "gibt-es-nicht.zip")
        self.assertTrue(any("ZIP fehlt" in item for item in problems), problems)


class RequiredFilesTests(unittest.TestCase):
    def test_required_files_exist_in_public(self) -> None:
        for name in pkg.REQUIRED_FILES:
            with self.subTest(name=name):
                self.assertTrue((pkg.PUBLIC / name).is_file(), name)

    def test_required_files_are_not_excluded_by_any_rule(self) -> None:
        for name in pkg.REQUIRED_FILES:
            with self.subTest(name=name):
                self.assertFalse(pkg.is_excluded(PurePosixPath(name)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
