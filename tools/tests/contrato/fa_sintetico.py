"""Contenedor B123 sintético para la suite de contrato (Norma 2: ni un byte de ROM).

Copia del helper ``_fa_sintetico`` de tools/tests/unidad/test_construir_candidata.py.
"""

from __future__ import annotations

import struct
from pathlib import Path

__all__ = ["escribir_fa"]


def escribir_fa(ruta: Path, ficheros: dict[str, bytes]) -> Path:
    """Escribe un contenedor B123 mínimo que FaArchive sabe recorrer."""
    carpetas: dict[str, list[tuple[str, bytes]]] = {}
    for rel, datos in ficheros.items():
        carpeta, _, nombre = rel.rpartition("/")
        carpetas.setdefault(carpeta + "/" if carpeta else "", []).append((nombre, datos))
    nombres, datos_blob, de, fe = bytearray(), bytearray(), bytearray(), bytearray()
    primero = 0
    for carpeta, lista in carpetas.items():
        dir_name_off = len(nombres)
        nombres += carpeta.encode("ascii") + b"\0"
        name_base = len(nombres)
        for nombre, datos in lista:
            fe += struct.pack("<IIII", 0, len(nombres) - name_base, len(datos_blob), len(datos))
            nombres += nombre.encode("ascii") + b"\0"
            datos_blob += datos
        de += struct.pack("<IHHIIII", 0, len(lista), 0, name_base, primero, 0, dir_name_off)
        primero += len(lista)
    de_off = 32
    fe_off = de_off + len(de)
    name_off = fe_off + len(fe)
    data_off = name_off + len(nombres)
    cabecera = b"B123" + struct.pack("<5i", de_off, de_off, fe_off, name_off, data_off)
    cabecera += struct.pack("<HHI", len(carpetas), 0, primero)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(cabecera + de + fe + nombres + datos_blob)
    return ruta
