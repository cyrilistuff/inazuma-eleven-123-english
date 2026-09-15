"""Diff genérico de candidatas: contenedores B123, capas, eventos PackNum y literales CRO.

No contiene reglas de ningún juego: las rutas concretas (eventos, CRO) las aporta el llamador
(por ejemplo ``ie123kit.ie1.verificar``). Cada fallo lanza ``ValidacionError`` con un código
estable en minúsculas y, como detalle, exactamente el mensaje que imprimía
``tools/verify_candidate.py``. No imprime ni termina el proceso.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ie123kit.nucleo.errores import ValidacionError

__all__ = [
    "cargar_capas",
    "comprobar_entradas",
    "comprobar_eventos_packnum",
    "comprobar_literales_cro",
    "indice",
    "payload",
    "sha256_fichero",
]


def sha256_fichero(path):
    """SHA-256 hexadecimal de un fichero, leído por bloques de 1 MiB."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def indice(arc):
    """Diccionario ruta → (offset, tamaño) de un ``FaArchive``, en el orden del contenedor."""
    return {p: (o, n) for p, o, n in arc.entries}


def payload(arc, idx, ruta):
    """Bytes de la entrada ``ruta`` según el índice ``idx``."""
    return bytes(arc.d[idx[ruta][0]:idx[ruta][0] + idx[ruta][1]])


def cargar_capas(capas):
    """Ruta POSIX relativa → bytes de todas las capas; las posteriores ganan."""
    expected = {}
    for layer in capas:
        layer = Path(layer)
        for f in sorted(layer.rglob('*')):
            if f.is_file():
                expected[f.relative_to(layer).as_posix()] = f.read_bytes()
    return expected


def _es_fuente(p):
    return '/font/' in p or p.startswith('font/')


def comprobar_entradas(base, cand, esperadas, *, ignoradas=(), es_fuente=_es_fuente):
    """Compara todas las entradas; devuelve (reemplazadas, fuentes idénticas)."""
    a = indice(base)
    b = indice(cand)
    if list(a) != list(b):
        raise ValidacionError('lista_entradas', None, 'entry list changed')
    replaced = fonts = 0
    for p in a:
        old, new = payload(base, a, p), payload(cand, b, p)
        if p in esperadas:
            if new != esperadas[p]:
                raise ValidacionError('capa_distinta', p, 'layer mismatch: ' + p)
            replaced += 1
        elif p in ignoradas:
            continue
        elif old != new:
            raise ValidacionError('cambio_inesperado', p, 'unexpected change: ' + p)
        if es_fuente(p):
            if old != new:
                raise ValidacionError('fuente_cambiada', p, 'font changed: ' + p)
            fonts += 1
    return replaced, fonts


def comprobar_eventos_packnum(base, cand, ruta_pkh, ruta_pkb, preparados):
    """Solo los eventos preparados (id → bytes descomprimidos) pueden cambiar; devuelve sus ids."""
    from ie123kit.nucleo.compresion.lz10 import decompress
    from ie123kit.nucleo.eventos.packnum import parse_index

    a = indice(base)
    b = indice(cand)
    get = payload
    staged = preparados
    ia = {e: (o, n) for e, o, n in parse_index(get(base, a, ruta_pkh))}
    ib = {e: (o, n) for e, o, n in parse_index(get(cand, b, ruta_pkh))}
    if list(ia) != list(ib):
        raise ValidacionError('indice_eventos', ruta_pkh, 'event index changed')
    pa, pb = get(base, a, ruta_pkb), get(cand, b, ruta_pkb)
    changed_events = []
    if pa != pb or get(base, a, ruta_pkh) != get(cand, b, ruta_pkh):
        for eid, (o, n) in ia.items():
            o2, n2 = ib[eid]
            old, new = decompress(pa[o:o + n]), decompress(pb[o2:o2 + n2])
            if eid in staged:
                if new != staged[eid]:
                    raise ValidacionError('evento_preparado_distinto', ruta_pkb, f'staged event mismatch: {eid}')
                changed_events.append(eid)
            elif old != new:
                raise ValidacionError('evento_cambiado', ruta_pkb, f'event {eid} changed')
    return changed_events


def comprobar_literales_cro(cro_a, cro_b, literales):
    """La CRO solo puede diferir en los huecos declarados (entradas offset/capacity)."""
    masked = bytearray(cro_b)
    for e in literales:
        masked[e['offset']:e['offset'] + e['capacity']] = cro_a[e['offset']:e['offset'] + e['capacity']]
    if len(cro_a) != len(cro_b) or masked != cro_a:
        raise ValidacionError('cro_fuera_de_literales', None, 'CRO changed outside declared literals')
