#!/usr/bin/env python3
"""Integra el wordmark europeo de IE1 en el título sin efecto de pegatina."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from ctpk_ui import decode, encode, metadata
from fa_unpack import FaArchive
from ui_archive import entries, unwrap


REPO = Path(__file__).resolve().parents[1]
ENTRY = "inazuma1/data_iz/pic2d/title/title_t.arc"
TEXTURE = "ie01_title_t_tlogo.tga"
DEFAULT_BASE = REPO / "work" / "probe_ie1_v34" / "archive.fa"
DEFAULT_SOURCE = REPO / "work" / "trailer" / "incoming" / "logo_ie1_es.png"
DEFAULT_OUTPUT = (REPO / "work" / "volumen_1" / "ie1_media_mod" / "archive_extra" /
                  "inazuma1" / "data_iz" / "pic2d" / "title" / "title_t.arc")
DEFAULT_PREVIEW = REPO / "work" / "volumen_1" / "ie1_media_mod" / "title_logo_preview.png"


def archive_payload(archive: FaArchive, wanted: str) -> bytes:
    for path, offset, size in archive.entries:
        if path == wanted:
            return bytes(archive.d[offset:offset + size])
    raise ValueError(f"no existe {wanted}")


def extract_wordmark(source: Path) -> Image.Image:
    """Aísla las letras y descarta los componentes del balón y el rayo."""
    original = np.array(Image.open(source).convert("RGBA"))
    rgb, alpha = original[:, :, :3], original[:, :, 3]
    coloured = (
        (alpha > 20)
        & (rgb[:, :, 0] > 130)
        & (rgb[:, :, 1] > 20)
        & (rgb[:, :, 1] < 245)
        & (rgb[:, :, 2] < 120)
    )
    height, width = coloured.shape
    seen = np.zeros_like(coloured, dtype=bool)
    letters = np.zeros_like(coloured, dtype=bool)

    for sy, sx in zip(*np.where(coloured & ~seen)):
        if seen[sy, sx]:
            continue
        queue = deque([(int(sy), int(sx))])
        seen[sy, sx] = True
        component: list[tuple[int, int]] = []
        while queue:
            y, x = queue.popleft()
            component.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if (
                    0 <= ny < height
                    and 0 <= nx < width
                    and coloured[ny, nx]
                    and not seen[ny, nx]
                ):
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        ys = [point[0] for point in component]
        if len(component) > 8 and min(ys) >= 55 and max(ys) < 175:
            for y, x in component:
                letters[y, x] = True

    near_letters = np.array(
        Image.fromarray((letters * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    ) > 0
    black_outline = (alpha > 20) & (rgb.max(axis=2) < 105) & near_letters
    core = letters | black_outline
    halo = np.array(
        Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    ) > 0

    pixels = np.zeros_like(original)
    pixels[:, :, :3] = original[:, :, :3]
    pixels[:, :, 3] = np.where(core, alpha, 0)
    white = np.zeros_like(original)
    white[:, :, :3] = 255
    white[:, :, 3] = np.where(halo & ~core, 255, 0)
    result = Image.fromarray(white)
    result.alpha_composite(Image.fromarray(pixels))
    bounds = result.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"no se pudo aislar el wordmark de {source}")
    return result.crop(bounds)


def render_wordmark(
    size: tuple[int, int], box: tuple[int, int, int, int], source: Path
) -> Image.Image:
    wordmark = extract_wordmark(source)
    x0, y0, x1, y1 = box
    room = (x1 - x0 - 6, y1 - y0 - 4)
    factor = min(room[0] / wordmark.width, room[1] / wordmark.height)
    wordmark = wordmark.resize(
        (round(wordmark.width * factor), round(wordmark.height * factor)),
        Image.Resampling.LANCZOS,
    )
    output = Image.new("RGBA", size)
    output.alpha_composite(
        wordmark,
        (
            x0 + (x1 - x0 - wordmark.width) // 2,
            y0 + (y1 - y0 - wordmark.height) // 2,
        ),
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    args = parser.parse_args()

    archive = FaArchive(str(args.base.resolve()))
    raw = bytearray(unwrap(archive_payload(archive, ENTRY)))
    changed = 0
    preview = None
    for offset, length, _ in entries(raw):
        chunk = raw[offset : offset + length]
        if chunk[:4] != b"CTPK" or metadata(chunk)[0] != TEXTURE:
            continue
        image = decode(chunk)
        preview = render_wordmark(
            image.size, (0, 0, 352, 112), args.source.resolve()
        )
        replacement = encode(chunk, preview)
        if len(replacement) != length:
            raise ValueError("la textura CTPK cambió de tamaño")
        raw[offset : offset + length] = replacement
        changed += 1

    if changed != 1 or preview is None:
        raise ValueError(f"se esperaba una textura {TEXTURE}; se encontraron {changed}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    preview.save(args.preview)
    print(f"OK: {args.output}")


if __name__ == "__main__":
    main()
