"""Subtítulos de películas DS (movie/txt/*.dat) y su incrustación en fotogramas.

Formato: registros (inicio, fin, tamaño) little-endian seguidos del texto
terminado en NUL, en codificación latina de NDS, y un terminador 0xFFFFFFFF.
Los tiempos van en ticks de 30 Hz, no en fotogramas del vídeo.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ie123kit.nucleo.texto.nds_latin import decode_ds

__all__ = ["SUBTITLE_TICK_RATE", "Subtitle", "add_caption", "fit_caption", "read_subtitles"]

SUBTITLE_TICK_RATE = 30  # movie/txt/*.dat: ticks de 30 Hz


@dataclass(frozen=True)
class Subtitle:
    start: int
    end: int
    text: str


def read_subtitles(path: Path | None) -> list[Subtitle]:
    if path is None:
        return []
    data = path.read_bytes()
    records: list[Subtitle] = []
    pos = 0
    while pos + 4 <= len(data):
        start = struct.unpack_from("<I", data, pos)[0]
        if start == 0xFFFFFFFF:
            if pos + 4 != len(data):
                raise ValueError(f"{path}: datos después del terminador")
            return records
        if pos + 12 > len(data):
            raise ValueError(f"{path}: cabecera de subtítulo truncada")
        end, size = struct.unpack_from("<II", data, pos + 4)
        pos += 12
        if end < start or size == 0 or pos + size > len(data):
            raise ValueError(f"{path}: registro de subtítulo inválido en 0x{pos - 12:x}")
        payload = data[pos:pos + size]
        pos += size
        text = decode_ds(payload.split(b"\0", 1)[0]).strip()
        records.append(Subtitle(start, end, text))
    raise ValueError(f"{path}: falta el terminador")


def fit_caption(text: str, draw: ImageDraw.ImageDraw, width: int, font_path: Path) -> ImageFont.FreeTypeFont:
    for size in range(14, 8, -1):
        font = ImageFont.truetype(str(font_path), size)
        if draw.textbbox((0, 0), text, font=font, stroke_width=1)[2] <= width:
            return font
    return ImageFont.truetype(str(font_path), 8)


def add_caption(image: Image.Image, text: str, font_path: Path) -> None:
    if not text:
        return
    draw = ImageDraw.Draw(image)
    font = fit_caption(text, draw, image.width - 10, font_path)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    x = (image.width - (box[2] - box[0])) // 2
    # Las películas DS ya reservan una banda negra inferior para esta pista.
    y = image.height - 23 - (box[3] - box[1]) // 2 - box[1]
    draw.text((x, y), text, font=font, fill=(255, 255, 255),
              stroke_width=1, stroke_fill=(0, 0, 0))
