"""Prepara una copia de un SMDH con el título del slot español cambiado.

No modifica el icono original. El SMDH conserva 12 slots de idioma de 0x200
bytes; el español ocupa el slot 5.
"""
import argparse
from pathlib import Path


SMDH_MAGIC = b"SMDH"
TITLE_TABLE_OFFSET = 0x08
TITLE_SLOT_SIZE = 0x200
SPANISH_SLOT = 5


def patch_title(source: Path, output: Path, title: str, slot: int = SPANISH_SLOT) -> None:
    data = bytearray(source.read_bytes())
    if data[:4] != SMDH_MAGIC:
        raise ValueError(f"no es un SMDH: {source}")
    if not 0 <= slot < 12:
        raise ValueError("el slot de idioma debe estar entre 0 y 11")
    encoded = (title + "\0").encode("utf-16le")
    if len(encoded) > TITLE_SLOT_SIZE:
        raise ValueError("el título excede el tamaño del slot SMDH")
    start = TITLE_TABLE_OFFSET + slot * TITLE_SLOT_SIZE
    end = start + TITLE_SLOT_SIZE
    if end > len(data):
        raise ValueError("el SMDH no contiene la tabla completa de títulos")
    data[start:end] = encoded + bytes(TITLE_SLOT_SIZE - len(encoded))
    if output.resolve() == source.resolve():
        raise ValueError("la salida no puede sobrescribir el SMDH original")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
