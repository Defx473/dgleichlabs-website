#!/usr/bin/env python3
"""DGleich Labs - lokaler Vorschau-Server.

Bildet das Verhalten des spaeteren statischen Hostings nach:

    - liefert public/ als Wurzel aus
    - /pfad/ -> /pfad/index.html (wie Cloudflare Pages / GitHub Pages)
    - unbekannte Pfade -> public/404.html mit HTTP 404
    - keine Verzeichnis-Auflistung, keine Traversierung ausserhalb von public/

Aufruf:
    python tools/serve.py                # http://127.0.0.1:8788
    python tools/serve.py --port 9000
    python tools/serve.py --open         # zusätzlich Standardbrowser öffnen
"""

from __future__ import annotations

import argparse
import socket
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "DGleichLabsPreview/0.1"

    def list_directory(self, path):  # noqa: A002 - Signatur der Basisklasse
        self.send_error(403, "Verzeichnisauflistung ist deaktiviert")
        return None

    def send_error(self, code, message=None, explain=None):  # noqa: A002
        if code == 404:
            body = (PUBLIC / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def end_headers(self) -> None:
        if self.path.endswith((".html", ".xml", ".txt", ".webmanifest")) or self.path.endswith("/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):  # ruhiger Ausgabe
        if " 404 " in (fmt % args) or " 403 " in (fmt % args):
            super().log_message(fmt, *args)


def free_port(host: str, preferred: int, attempts: int = 25) -> int:
    for candidate in range(preferred, preferred + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, candidate))
            except OSError:
                continue
            return candidate
    sys.exit(f"FEHLER: kein freier Port ab {preferred}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lokaler Vorschau-Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--open", action="store_true", help="Standardbrowser öffnen")
    args = parser.parse_args()

    if not (PUBLIC / "index.html").is_file():
        sys.exit("FEHLER: public/index.html fehlt. Bitte 'python tools/build.py' ausführen.")

    port = free_port(args.host, args.port)
    handler = partial(Handler, directory=str(PUBLIC))
    with ThreadingHTTPServer((args.host, port), handler) as server:
        url = f"http://{args.host}:{port}/"
        print(f"DGleich Labs – Vorschau läuft: {url}")
        print(f"Wurzel: {PUBLIC}")
        print("Beenden mit Strg+C")
        if args.open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer beendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
