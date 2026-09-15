"""Inspección genérica de audio SADL (.SAD) de Level-5.

Solo lee la cabecera (canales, frecuencia, bucle, tamaños) y calcula el sha256;
la conversión SAD<->WAV irá vía vgmstream en la fase 2.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

__all__ = ["SadInfo", "inspect_sad", "sha256"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SadInfo:
    size: int
    channels: int
    sample_rate: int
    codec_flag: str
    loop: bool
    data_size: int
    start_offset: int
    sha256: str


def inspect_sad(path: Path) -> SadInfo:
    data = path.read_bytes()
    if len(data) < 0x58 or data[:4] != b"sadl":
        raise ValueError(f"{path}: no es un SADL válido")
    flags = data[0x33]
    rate_bits = flags & 0x06
    if rate_bits == 0x04:
        sample_rate = 32728
    elif rate_bits in (0x00, 0x02):
        sample_rate = 16364
    else:
        raise ValueError(f"{path}: frecuencia SADL desconocida (flags=0x{flags:02x})")
    return SadInfo(
        size=len(data),
        channels=data[0x32],
        sample_rate=sample_rate,
        codec_flag=f"0x{flags:02x}",
        loop=bool(data[0x31]),
        data_size=struct.unpack_from("<I", data, 0x40)[0],
        start_offset=struct.unpack_from("<I", data, 0x48)[0],
        sha256=sha256(path),
    )
