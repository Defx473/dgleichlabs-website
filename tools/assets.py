#!/usr/bin/env python3
"""DGleich Labs - Brand-Assets erzeugen.

Erzeugt die Raster-Assets aus einer rein geometrisch beschriebenen Marke
(kein fremdes Logo, keine gekauften Grafiken):

    public/assets/favicon-32.png       32x32
    public/assets/apple-touch-icon.png 180x180
    public/assets/icon-192.png         192x192
    public/assets/icon-512.png         512x512
    public/assets/og.png               1200x630 (Social-Vorschau)

Das Vektor-Pendant (public/assets/favicon.svg) ist eine handgeschriebene
SVG-Datei im Repository und nutzt dieselbe Geometrie.

Aufruf:
    python tools/assets.py           # Assets schreiben
    python tools/assets.py --check   # nur pruefen (Exit 1 bei Abweichung)

Abhaengigkeit: Pillow. Es wird KEINE Schriftdatei ausgeliefert - Schriften
werden nur lokal zum Rendern der Rasterbilder verwendet (bevorzugt DejaVu,
freie Lizenz). Ohne installierte Schrift wird auf Pillows Standardschrift
zurueckgefallen.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("FEHLER: Pillow ist nicht installiert (pip install pillow)")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "assets"

# --- Farben (Basisraster 32 x 32, gleiche Geometrie wie favicon.svg) --------
BG = (11, 15, 20)
FRAME = (22, 32, 45)
FRAME_LINE = (43, 61, 81)
GLYPH = (232, 238, 247)
ACCENT = (79, 224, 192)
MUTED = (159, 176, 198)
WHITE = (255, 255, 255)

FONTS = {
    "sans_bold": ["C:/Windows/Fonts/DejaVuSans-Bold.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "sans": ["C:/Windows/Fonts/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "mono": ["C:/Windows/Fonts/DejaVuSansMono.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}


def load_font(kind: str, size: int):
    for candidate in FONTS[kind]:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def draw_mark(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    """Monogramm: Rahmen + D (Balken und Bogen) + Akzentpunkt."""
    x0, y0, x1, y1 = box
    scale = min(x1 - x0, y1 - y0) / 32.0
    draw = ImageDraw.Draw(canvas)

    def s(value: float) -> int:
        return int(round(value * scale))

    draw.rounded_rectangle(
        box, radius=s(8), fill=FRAME, outline=FRAME_LINE, width=max(1, s(1))
    )

    # "D": linker Balken + rechter Bogen
    draw.rectangle([x0 + s(9), y0 + s(9), x0 + s(14), y0 + s(23)], fill=GLYPH)

    radius = s(7)
    cx, cy = x0 + s(14), y0 + s(16)
    draw.pieslice(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        start=-90,
        end=90,
        fill=GLYPH,
    )

    # Innenraum (Gegenform) ausstanzen - ergibt dieselbe Kontur wie favicon.svg
    draw.rectangle([x0 + s(14.4), y0 + s(12), x0 + s(16.1), y0 + s(20)], fill=FRAME)
    inner = s(4)
    ix, iy = x0 + s(16.1), y0 + s(16)
    draw.pieslice(
        [ix - inner, iy - inner, ix + inner, iy + inner],
        start=-90,
        end=90,
        fill=FRAME,
    )

    dot = s(2.2)
    dx, dy = x0 + s(23.5), y0 + s(24.5)
    draw.ellipse([dx - dot, dy - dot, dx + dot, dy + dot], fill=ACCENT)


def icon(size: int) -> Image.Image:
    image = Image.new("RGB", (size, size), BG)
    padding = int(size * 0.10)
    draw_mark(image, (padding, padding, size - padding, size - padding))
    return image


def spaced_text(draw: ImageDraw.ImageDraw, text: str, font, spacing: int, fill, origin) -> int:
    """Text mit zusaetzlichem Buchstabenabstand; liefert die End-X-Position."""
    x, y = origin
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += int(draw.textlength(char, font=font)) + spacing
    return x


def wordmark(canvas: Image.Image, x: int, y: int, size: int) -> None:
    font = load_font("sans_bold", size)
    draw = ImageDraw.Draw(canvas)
    draw.text((x, y), "DGleich", font=font, fill=WHITE)
    offset = int(draw.textlength("DGleich", font=font)) + int(size * 0.18)
    draw.text((x + offset, y), "Labs", font=font, fill=ACCENT)


def og_image() -> Image.Image:
    width, height = 1200, 630
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)

    # Dezenter vertikaler Verlauf.
    for row in range(height):
        factor = row / height
        draw.line(
            [(0, row), (width, row)],
            fill=(int(13 - 3 * factor), int(20 - 5 * factor), int(28 - 8 * factor)),
        )

    canvas = canvas.convert("RGBA")

    # Weicher Akzent-Glow aus mehreren transparenten Ellipsen.
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for step, alpha in enumerate((30, 22, 16, 11)):
        spread = step * 80
        glow_draw.ellipse(
            [120 - spread, -300 - spread, 940 + spread, 340 + spread],
            fill=(*ACCENT, alpha),
        )
    canvas = Image.alpha_composite(canvas, glow)

    draw_mark(canvas, (80, 96, 204, 220))
    wordmark(canvas, 80, 268, 78)

    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    spaced_text(ImageDraw.Draw(layer), "SOFTWARE. APPS. IDEAS.",
                load_font("mono", 27), 7, ACCENT, (82, 392))
    canvas = Image.alpha_composite(canvas, layer)

    footer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    footer_draw = ImageDraw.Draw(footer)
    footer_draw.line([(80, 468), (1120, 468)], fill=FRAME_LINE, width=1)

    # Zwei getrennte Zeilen - Domain und Einordnung dürfen sich nicht berühren.
    spaced_text(footer_draw, "dgleichlabs.de", load_font("mono", 24), 3, MUTED, (82, 496))
    footer_draw.text(
        (82, 540),
        "Unabhängige Software- und Entwicklungsmarke aus Deutschland",
        font=load_font("sans", 21),
        fill=MUTED,
    )
    canvas = Image.alpha_composite(canvas, footer)

    return canvas.convert("RGB")


def encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description="DGleich Labs Assets erzeugen")
    parser.add_argument("--check", action="store_true", help="nur pruefen, nichts schreiben")
    args = parser.parse_args()

    outputs = {
        OUT / "favicon-32.png": icon(32),
        OUT / "apple-touch-icon.png": icon(180),
        OUT / "icon-192.png": icon(192),
        OUT / "icon-512.png": icon(512),
        OUT / "og.png": og_image(),
    }

    stale: list[str] = []
    written = 0
    for path, image in outputs.items():
        data = encode(image)
        if path.is_file() and path.read_bytes() == data:
            continue
        if args.check:
            stale.append(path.relative_to(ROOT).as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written += 1

    if args.check:
        if stale:
            print("FEHLER: Assets weichen ab. Bitte 'python tools/assets.py' ausfuehren.")
            for name in stale:
                print(f"  abweichend: {name}")
            return 1
        print("OK: Assets sind aktuell.")
        return 0

    print(f"OK: {written} Asset(s) geschrieben, {len(outputs) - written} unveraendert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
