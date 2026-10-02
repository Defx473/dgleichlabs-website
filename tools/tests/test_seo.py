#!/usr/bin/env python3
"""SEO- und Metadaten-Pruefungen fuer die ausgelieferten Seiten (public/).

Aufruf:
    python -m unittest discover -s tools/tests -t tools
    python tools/tests/test_seo.py

Die Tests pruefen den GEBAUTEN Stand so, wie er ausgeliefert wird: genau ein
Title/Description/Canonical je Seite, absolute Canonicals auf der Produktions-
domain, korrekte OpenGraph-/Twitter-Basis, passende Sitemap und ein 404 ohne
Indexierung. Sie ergaenzen check.py (Barrierearmut, Links, Sicherheit) um die
Metadaten-Sicht und fassen keine Quelldateien an.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
SITE = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["url"].rstrip("/")          # https://dgleichlabs.de
ROUTES = SITE["routes"]
ROUTE_FILES = [route["file"] for route in ROUTES]
INDEXABLE = [PUBLIC / name for name in ROUTE_FILES]
ALL_PAGES = sorted(PUBLIC.rglob("*.html"))
NOT_FOUND = PUBLIC / "404.html"


def text_of(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def count(pattern: str, haystack: str) -> int:
    return len(re.findall(pattern, haystack, re.IGNORECASE | re.DOTALL))


def first(pattern: str, haystack: str) -> str | None:
    match = re.search(pattern, haystack, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def canonical_of(html: str) -> str | None:
    return first(r'<link\s+rel="canonical"\s+href="([^"]*)"', html)


def meta_content(html: str, *, name: str | None = None, prop: str | None = None) -> str | None:
    if name is not None:
        pattern = rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"'
    else:
        pattern = rf'<meta\s+property="{re.escape(prop or "")}"\s+content="([^"]*)"'
    return first(pattern, html)


class TitleTests(unittest.TestCase):
    def test_every_page_has_exactly_one_title(self) -> None:
        for page in ALL_PAGES:
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertEqual(count(r"<title>", text_of(page)), 1)

    def test_titles_are_unique(self) -> None:
        titles = [first(r"<title>(.*?)</title>", text_of(p)) for p in ALL_PAGES]
        self.assertEqual(len(titles), len(set(titles)), f"Doppelte Titles: {titles}")

    def test_titles_are_not_too_long(self) -> None:
        for page in ALL_PAGES:
            title = first(r"<title>(.*?)</title>", text_of(page)) or ""
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertLessEqual(len(title), 70, title)

    def test_indexable_pages_name_the_brand(self) -> None:
        for page in INDEXABLE:
            title = first(r"<title>(.*?)</title>", text_of(page)) or ""
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertIn("DGleich Labs", title, title)


class DescriptionTests(unittest.TestCase):
    def test_every_page_has_exactly_one_description(self) -> None:
        for page in ALL_PAGES:
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertEqual(count(r'<meta\s+name="description"', text_of(page)), 1)

    def test_descriptions_have_a_sensible_length(self) -> None:
        for page in ALL_PAGES:
            desc = meta_content(text_of(page), name="description") or ""
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertGreaterEqual(len(desc), 50, desc)
                self.assertLessEqual(len(desc), 165, desc)


class CanonicalTests(unittest.TestCase):
    def test_every_page_has_exactly_one_canonical(self) -> None:
        for page in ALL_PAGES:
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertEqual(count(r'<link\s+rel="canonical"', text_of(page)), 1)

    def test_canonicals_use_https_on_the_production_domain(self) -> None:
        for page in ALL_PAGES:
            canonical = canonical_of(text_of(page)) or ""
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertTrue(canonical.startswith(BASE + "/"), canonical)

    def test_indexable_canonicals_match_their_route(self) -> None:
        for route in ROUTES:
            page = PUBLIC / route["file"]
            expected = BASE + route["path"]
            with self.subTest(route=route["path"]):
                self.assertEqual(canonical_of(text_of(page)), expected)


class ForbiddenReferenceTests(unittest.TestCase):
    def test_no_localhost_or_plain_http_or_www(self) -> None:
        for page in ALL_PAGES:
            html = text_of(page)
            rel = page.relative_to(PUBLIC).as_posix()
            with self.subTest(page=rel):
                self.assertNotIn("localhost", html.lower())
                self.assertNotIn("127.0.0.1", html)
                self.assertNotIn("http://dgleichlabs.de", html)
                self.assertNotIn("www.dgleichlabs.de", html)


class SocialMetadataTests(unittest.TestCase):
    def test_indexable_pages_have_open_graph_basics(self) -> None:
        for page in INDEXABLE:
            html = text_of(page)
            rel = page.relative_to(PUBLIC).as_posix()
            with self.subTest(page=rel):
                for prop in ("og:type", "og:title", "og:description", "og:url",
                             "og:site_name", "og:image", "og:image:alt"):
                    self.assertIsNotNone(meta_content(html, prop=prop), prop)

    def test_og_url_matches_canonical(self) -> None:
        for page in INDEXABLE:
            html = text_of(page)
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertEqual(meta_content(html, prop="og:url"), canonical_of(html))

    def test_twitter_card_basics_are_present(self) -> None:
        for page in INDEXABLE:
            html = text_of(page)
            rel = page.relative_to(PUBLIC).as_posix()
            with self.subTest(page=rel):
                for name in ("twitter:card", "twitter:title", "twitter:description",
                             "twitter:image", "twitter:image:alt"):
                    self.assertIsNotNone(meta_content(html, name=name), name)

    def test_no_invented_twitter_accounts(self) -> None:
        for page in ALL_PAGES:
            html = text_of(page)
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertIsNone(meta_content(html, name="twitter:site"))
                self.assertIsNone(meta_content(html, name="twitter:creator"))

    def test_og_image_is_absolute_and_delivered(self) -> None:
        for page in INDEXABLE:
            image = meta_content(text_of(page), prop="og:image") or ""
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertTrue(image.startswith(BASE + "/"), image)
                self.assertTrue((PUBLIC / image[len(BASE) + 1:]).is_file(), image)

    def test_no_scripts_anywhere(self) -> None:
        """Kein JavaScript und bewusst kein JSON-LD.

        Die CSP setzt script-src 'none'; Structured Data wurde deshalb nicht
        aufgenommen (siehe README/Bericht). Dieser Test haelt das fest.
        """
        for page in ALL_PAGES:
            with self.subTest(page=page.relative_to(PUBLIC).as_posix()):
                self.assertEqual(count(r"<script", text_of(page)), 0)


class NotFoundTests(unittest.TestCase):
    def test_404_is_not_indexable(self) -> None:
        robots = meta_content(text_of(NOT_FOUND), name="robots") or ""
        self.assertIn("noindex", robots.lower())

    def test_404_links_back_home(self) -> None:
        self.assertIn('href="/"', text_of(NOT_FOUND))

    def test_404_is_not_in_the_sitemap(self) -> None:
        sitemap = text_of(PUBLIC / "sitemap.xml")
        self.assertNotIn("404", sitemap)


class SitemapTests(unittest.TestCase):
    def test_sitemap_lists_exactly_the_indexable_routes(self) -> None:
        sitemap = text_of(PUBLIC / "sitemap.xml")
        locations = re.findall(r"<loc>([^<]+)</loc>", sitemap)
        expected = {BASE + route["path"] for route in ROUTES}
        self.assertEqual(set(locations), expected)
        self.assertEqual(len(locations), len(expected))

    def test_sitemap_uses_https_and_no_build_artifacts(self) -> None:
        sitemap = text_of(PUBLIC / "sitemap.xml")
        locations = re.findall(r"<loc>([^<]+)</loc>", sitemap)
        for loc in locations:
            with self.subTest(loc=loc):
                self.assertTrue(loc.startswith(BASE + "/"), loc)
                self.assertFalse(loc.endswith((".png", ".zip", ".xml", ".txt")), loc)

    def test_robots_points_at_the_sitemap(self) -> None:
        robots = text_of(PUBLIC / "robots.txt")
        self.assertIn(f"Sitemap: {BASE}/sitemap.xml", robots)
        self.assertIn("Allow: /", robots)


if __name__ == "__main__":
    unittest.main(verbosity=2)
