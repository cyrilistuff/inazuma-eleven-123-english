#!/usr/bin/env python3
"""Convierte vídeo MobiClip de Nintendo DS (.mods) a 3DS (.moflex).

El MODS de DS almacena los planos cromáticos como YCgCo. FFmpeg los etiqueta
correctamente, pero su conversor de color no admite todavía esa transformación.
Este puente descodifica a Y/Cg/Co, convierte cada fotograma a RGB, incrusta si
existe la pista de subtítulos europea, lo gira al formato 240x320 usado por IE1
en 3DS y lo entrega al codificador MobiClip. Finalmente restaura en todos los
descriptores MOFLEX la marca de rotación que usa el juego original.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
# La compilación x64 v2.1 se bloquea al codificar imágenes complejas en Windows
# (0xc0000005). La compilación x86 del mismo lanzamiento supera ese caso.
DEFAULT_MOBIPEG = REPO / "work" / "shared" / "herramientas" / "media_tools" / "mobipeg-v2.1-x86"
SUBTITLE_TICK_RATE = 30  # movie/txt/*.dat: ticks de 30 Hz
DEFAULT_FONT = Path("C:/Windows/Fonts/arialbd.ttf")

DS_TABLE = {
    0xB2: "á", 0xBA: "é", 0xBE: "í", 0xC4: "ó", 0xCA: "ú",
    0xC2: "ñ", 0xCC: "ü", 0xD1: "Á", 0xD9: "É", 0xA6: "Í",
    0xAB: "Ó", 0xA2: "Ú", 0xA9: "Ñ", 0xDF: "¡", 0xA5: "¿",
}


@dataclass(frozen=True)
class Subtitle:
    start: int
    end: int
    text: str


def decode_ds(data: bytes) -> str:
    return "".join(chr(value) if value < 0x80 else DS_TABLE.get(value, "?") for value in data)


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


def set_moflex_rotation(path: Path, rotation: int) -> int:
    """Copia ImageRotation al nibble alto de cada descriptor type-3.

    Los MOFLEX retail de IE1 usan layout 0x16: Simple2D + giro 1. El muxer de
    mobipeg emite 0x06 y Azahar muestra entonces el fotograma 240x320 de lado.
    """
    if not 0 <= rotation <= 15:
        raise ValueError("la rotación MOFLEX debe estar entre 0 y 15")
    data = bytearray(path.read_bytes())
    changed = 0
    pos = 0
    while True:
        pos = data.find(b"\x4c\x32", pos)
        if pos < 0:
            break
        # Cabecera de sincronía (14 bytes), descriptor type 3, tamaño 13;
        # el byte de layout es el último byte del payload.
        if pos + 29 <= len(data) and data[pos + 14] == 3 and data[pos + 15] == 13:
            layout_pos = pos + 28
            data[layout_pos] = (rotation << 4) | (data[layout_pos] & 0x0F)
            changed += 1
        pos += 2
    if not changed:
        raise ValueError(f"{path}: no se encontró ningún descriptor de vídeo MOFLEX")
    path.write_bytes(data)
    return changed


def probe(ffprobe: Path, source: Path) -> tuple[int, int, str]:
    proc = subprocess.run(
        [
            str(ffprobe), "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate", "-of", "json",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(proc.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"]), stream["r_frame_rate"]


def ycgco420_to_rgb(frame: bytes, width: int, height: int) -> np.ndarray:
    y_size = width * height
    c_width, c_height = width // 2, height // 2
    c_size = c_width * c_height
    if len(frame) != y_size + c_size * 2:
        raise ValueError("fotograma YUV420 incompleto")

    y = np.frombuffer(frame, np.uint8, y_size, 0).reshape(height, width).astype(np.int16)
    cg = np.frombuffer(frame, np.uint8, c_size, y_size).reshape(c_height, c_width)
    co = np.frombuffer(frame, np.uint8, c_size, y_size + c_size).reshape(c_height, c_width)
    cg = np.repeat(np.repeat(cg, 2, axis=0), 2, axis=1).astype(np.int16) - 128
    co = np.repeat(np.repeat(co, 2, axis=0), 2, axis=1).astype(np.int16) - 128

    temporary = y - cg
    rgb = np.stack((temporary + co, y + cg, temporary - co), axis=2)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def rgb_to_yuv420(image: Image.Image) -> bytes:
    y, cb, cr = image.convert("YCbCr").split()
    half = (image.width // 2, image.height // 2)
    cb = cb.resize(half, Image.Resampling.BOX)
    cr = cr.resize(half, Image.Resampling.BOX)
    return y.tobytes() + cb.tobytes() + cr.tobytes()


def convert(source: Path, target: Path, mobipeg_dir: Path, qp: int,
            subtitles_path: Path | None = None, font_path: Path = DEFAULT_FONT,
            rotation: int = 1) -> tuple[int, int, int]:
    ffmpeg = mobipeg_dir / "ffmpeg.exe"
    ffprobe = mobipeg_dir / "ffprobe.exe"
    if not ffmpeg.is_file() or not ffprobe.is_file():
        raise FileNotFoundError(f"Falta mobipeg portátil en {mobipeg_dir}")

    width, height, fps = probe(ffprobe, source)
    num, _, den = fps.partition("/")
    fps_value = float(num) / float(den or 1)
    if width % 2 or height % 2:
        raise ValueError("MODS no usa dimensiones pares")
    frame_size = width * height * 3 // 2
    subtitles = read_subtitles(subtitles_path)
    if subtitles and subtitles[-1].end >= 10_000_000:
        raise ValueError(f"{subtitles_path}: tiempos de subtítulo inverosímiles")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".partial")

    decoder = subprocess.Popen(
        [
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(source),
            "-map", "0:v:0", "-an", "-c:v", "rawvideo", "-pix_fmt", "yuv420p",
            "-f", "rawvideo", "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )
    frames = 0
    raw_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="mods_to_moflex_", suffix=".yuv", dir=target.parent, delete=False
        ) as raw_file:
            raw_path = Path(raw_file.name)
            assert decoder.stdout is not None
            while True:
                raw = decoder.stdout.read(frame_size)
                if not raw:
                    break
                if len(raw) != frame_size:
                    raise RuntimeError("el descodificador entregó un fotograma truncado")
                rgb = ycgco420_to_rgb(raw, width, height)
                image = Image.fromarray(rgb, "RGB")
                # Los .dat de movie/txt cuentan en ticks de 30 Hz, no en fotogramas del vídeo
                # (op00: 1763 fotogramas a 20 fps y último subtítulo en 2675 = 1763 * 30/20).
                tick = frames * SUBTITLE_TICK_RATE / fps_value
                active = next((item.text for item in subtitles if item.start <= tick <= item.end), "")
                add_caption(image, active, font_path)
                image = image.transpose(Image.Transpose.ROTATE_270)
                image = image.resize((240, 320), Image.Resampling.LANCZOS)
                raw_file.write(rgb_to_yuv420(image))
                frames += 1
    finally:
        if decoder.stdout:
            decoder.stdout.close()

    decoder_code = decoder.wait()
    if decoder_code:
        if raw_path:
            raw_path.unlink(missing_ok=True)
        raise RuntimeError(f"falló la descodificación (código={decoder_code})")

    try:
        encoder = subprocess.run(
            [
                str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s:v", "240x320", "-r", fps,
                "-i", str(raw_path), "-an", "-c:v", "mobiclip", "-mobiclip", "1",
                "-moflex", "1", "-qp", str(qp), "-pix_fmt", "yuv420p",
                "-threads", "1", "-x264opts", "mvrange=32",
                "-f", "moflex", str(partial),
            ],
            check=False,
        )
        if encoder.returncode or not partial.is_file() or partial.stat().st_size == 0:
            partial.unlink(missing_ok=True)
            raise RuntimeError(f"falló la codificación (código={encoder.returncode})")
        descriptors = set_moflex_rotation(partial, rotation)
        partial.replace(target)
        return frames, len(subtitles), descriptors
    finally:
        if raw_path:
            raw_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--mobipeg", type=Path, default=DEFAULT_MOBIPEG)
    parser.add_argument("--qp", type=int, default=28)
    parser.add_argument("--subtitles", type=Path,
                        help="pista movie/txt/sp/*.dat que se incrustará en el vídeo")
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--rotation", type=int, default=1,
                        help="ImageRotation del MOFLEX (IE1 retail usa 1)")
    args = parser.parse_args()

    frames, subtitles, descriptors = convert(
        args.source.resolve(), args.target.resolve(), args.mobipeg.resolve(), args.qp,
        args.subtitles.resolve() if args.subtitles else None, args.font.resolve(), args.rotation,
    )
    print(f"OK: {frames} fotogramas, {subtitles} subtítulos, "
          f"{descriptors} descriptores de giro -> {args.target}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
