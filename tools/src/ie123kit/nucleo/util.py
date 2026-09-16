"""Ayudas puras de ie123kit: hashes estables, JSON y marcas de tiempo.

Sin dependencias externas y sin efectos al importar.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

__all__ = [
    "ahora_iso",
    "escribir_json",
    "leer_json",
    "sha256_arbol",
    "sha256_bytes",
    "sha256_file",
]

_BLOQUE = 1024 * 1024


def sha256_bytes(datos: bytes) -> str:
    """sha256 hexadecimal de una secuencia de bytes."""
    return hashlib.sha256(datos).hexdigest()


def sha256_file(ruta: str | os.PathLike[str]) -> str:
    """sha256 hexadecimal de un fichero, leído por bloques de 1 MiB."""
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        while bloque := f.read(_BLOQUE):
            h.update(bloque)
    return h.hexdigest()


def sha256_arbol(directorio: str | os.PathLike[str]) -> str:
    """Hash estable de un árbol de ficheros (ruta relativa POSIX + sha256 de cada fichero).

    Sirve para comprobar que una operación en modo simulación no ha escrito nada.
    """
    base = Path(directorio)
    h = hashlib.sha256()
    if not base.exists():
        return h.hexdigest()
    for ruta in sorted(base.rglob("*")):
        rel = ruta.relative_to(base).as_posix()
        if ruta.is_dir():
            h.update(f"D {rel}\n".encode())
        elif ruta.is_file():
            h.update(f"F {rel} {sha256_file(ruta)}\n".encode())
    return h.hexdigest()


def escribir_json(ruta: str | os.PathLike[str], obj: object) -> Path:
    """Escribe `obj` como JSON UTF-8 legible (indent 2, sin reordenar claves)."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False)
    destino.write_text(texto + "\n", encoding="utf-8")
    return destino


def leer_json(ruta: str | os.PathLike[str]) -> object:
    """Lee un JSON UTF-8."""
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def ahora_iso() -> str:
    """Instante actual en UTC, ISO-8601 con segundos enteros y sufijo Z."""
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
