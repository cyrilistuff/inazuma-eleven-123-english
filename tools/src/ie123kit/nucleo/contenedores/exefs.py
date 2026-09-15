"""ExeFS de 3DS: construcción, lectura y comprobación de hashes. EXPERIMENTAL.

Estructura: cabecera de 0x200 bytes con 8 entradas ``<8sII`` (nombre, offset, tamaño) y los SHA-256
de cada fichero en orden INVERSO (la entrada i ocupa 0x200-(i+1)*0x20), seguida de los ficheros,
cada uno rellenado a múltiplo de 0x200.

Lógica tomada de ``build_exefs`` del antiguo ``tools/patch_exefs.py`` (archivado) SIN el parcheo de
code.bin: patch_code y patch_cro son obsoletos y peligrosos (docs/FURIGANA_LECCIONES.md) y siguen
vigentes NO_CODE_PATCH=1 y SKIP_CRO=1. Aquí no se toca el exheader ni code_size. Lo usará el juego
principal para sustituir banner.bnr e icon.icn.
"""
from __future__ import annotations

import hashlib
import struct

__all__ = ["ARCHIVOS", "comprobar_hashes", "construir", "leer"]

ARCHIVOS = ((".code", "code.bin"), ("banner", "banner.bnr"), ("icon", "icon.icn"), ("logo", "logo.darc.lz"))


def construir(contenidos) -> bytes:
    """Construye un ExeFS a partir de una secuencia de (nombre, bytes), en ese orden."""
    header = bytearray(0x200)
    data = bytearray()
    offset = 0
    for i, (name, content) in enumerate(contenidos):
        struct.pack_into("<8sII", header, i * 0x10, name.encode(), offset, len(content))
        header[0x200 - (i + 1) * 0x20: 0x200 - i * 0x20] = hashlib.sha256(content).digest()
        data += content
        data += b"\x00" * ((-len(content)) % 0x200)            # relleno a 0x200
        offset = len(data)
    return bytes(header) + bytes(data)


def leer(datos) -> list[tuple[str, int, int]]:
    """Lista (nombre, offset relativo a los datos, tamaño) de las entradas no vacías."""
    salida = []
    for i in range(8):
        raw, off, size = struct.unpack_from("<8sII", datos, i * 0x10)
        nombre = raw.rstrip(b"\x00").decode("ascii")
        if nombre:
            salida.append((nombre, off, size))
    return salida


def comprobar_hashes(datos) -> bool:
    """True si el SHA-256 de cada entrada coincide con el de la cabecera."""
    for i, (_nombre, off, size) in enumerate(leer(datos)):
        contenido = bytes(datos[0x200 + off:0x200 + off + size])
        if len(contenido) != size:
            return False
        if bytes(datos[0x200 - (i + 1) * 0x20: 0x200 - i * 0x20]) != hashlib.sha256(contenido).digest():
            return False
    return True
