"""Comprobación «enmascarada»: qué bytes cambian entre dos versiones de un fichero.

Recoge el patrón ``assert_only_declared_ranges_changed`` que las capas de ``work/`` repetían a
mano (copiar la salida, restaurar las ranuras declaradas desde la base y exigir igualdad). Los
rangos son semiabiertos ``[inicio, fin)`` y los bytes contiguos se fusionan en un solo rango.

Sin dependencias externas y sin efectos al importar.
"""

from __future__ import annotations

from collections.abc import Iterable

from ie123kit.nucleo.errores import ValidacionError

__all__ = ["assert_only_changed", "diff_ranges", "fusionar", "same_size"]

_CONTEXTO = 8


def same_size(old: bytes, new: bytes) -> int:
    """Devuelve la longitud común de ``old`` y ``new``; lanza :class:`ValidacionError` si difieren."""
    if len(old) != len(new):
        raise ValidacionError("tamano_distinto", detalle=f"base {len(old)} B, resultado {len(new)} B")
    return len(old)


def fusionar(rangos: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Ordena y fusiona rangos semiabiertos solapados o contiguos."""
    salida: list[tuple[int, int]] = []
    for inicio, fin in sorted((a, b) for a, b in rangos if b > a):
        if salida and inicio <= salida[-1][1]:
            salida[-1] = (salida[-1][0], max(salida[-1][1], fin))
        else:
            salida.append((inicio, fin))
    return salida


def diff_ranges(old: bytes, new: bytes) -> list[tuple[int, int]]:
    """Rangos semiabiertos en los que ``old`` y ``new`` difieren (bytes contiguos fusionados)."""
    same_size(old, new)
    salida: list[tuple[int, int]] = []
    inicio: int | None = None
    for i, (a, b) in enumerate(zip(old, new, strict=True)):
        if a != b:
            if inicio is None:
                inicio = i
        elif inicio is not None:
            salida.append((inicio, i))
            inicio = None
    if inicio is not None:
        salida.append((inicio, len(old)))
    return salida


def _hex(datos: bytes, offset: int) -> str:
    inicio = max(0, offset - _CONTEXTO)
    fin = min(len(datos), offset + _CONTEXTO + 1)
    return datos[inicio:fin].hex(" ")


def assert_only_changed(old: bytes, new: bytes, permitidos: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Exige que solo cambien bytes dentro de ``permitidos``.

    Devuelve los rangos realmente cambiados. Lanza :class:`ValidacionError` con el primer offset
    ofensor y su contexto hexadecimal en base y resultado.
    """
    cambiados = diff_ranges(old, new)
    libres = fusionar(permitidos)
    for inicio, fin in cambiados:
        for offset in range(inicio, fin):
            if not any(a <= offset < b for a, b in libres):
                raise ValidacionError(
                    "cambio_fuera_de_rango",
                    detalle=(
                        f"offset 0x{offset:x} fuera de los rangos declarados; "
                        f"base [{_hex(old, offset)}] resultado [{_hex(new, offset)}]"
                    ),
                )
    return cambiados
