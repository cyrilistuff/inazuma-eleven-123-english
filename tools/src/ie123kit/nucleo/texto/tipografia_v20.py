"""Perfil tipográfico v20 BLOQUEADO de toda la recopilación (menú, IE1, IE2 e IE3).

AVISO: cambiar la tipografía (caja, fuentes, codificación, espaciado o saltos)
requiere una petición explícita del usuario; una orden general de continuar no basta
(AGENTS.md, ``tools/dialogue_lock.py``).

Re-export PEREZOSO: ``layout`` es ``build_ie1_probe.layout`` (el mismo objeto);
``LAYOUT_HASH``, ``FONT_HASHES`` y ``SOURCE_HASHES`` vienen de ``dialogue_lock`` y
``FUENTES_BLOQUEADAS = tuple(dialogue_lock.FONT_HASHES)``. Nada se carga al importar.
"""
from __future__ import annotations

__all__ = ["approved_layout"]

_DE_LOCK = ("LAYOUT_HASH", "FONT_HASHES", "SOURCE_HASHES")


def _cargar(nombre):
    from ie123kit.nucleo.config.congelados import cargar
    return cargar(nombre)


def __getattr__(nombre: str):
    if nombre == "layout":
        return _cargar("build_ie1_probe").layout
    if nombre in _DE_LOCK:
        return getattr(_cargar("dialogue_lock"), nombre)
    if nombre == "FUENTES_BLOQUEADAS":
        return tuple(_cargar("dialogue_lock").FONT_HASHES)
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


def approved_layout(texto: str) -> str:
    """Ajuste de líneas aprobado (v20): ``dialogue_lock.approved_layout(texto, layout)``."""
    return _cargar("dialogue_lock").approved_layout(texto, _cargar("build_ie1_probe").layout)
