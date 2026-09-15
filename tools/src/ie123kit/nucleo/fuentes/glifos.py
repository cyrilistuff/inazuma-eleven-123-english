"""Glifos del español en las fuentes BCFNT: re-export PEREZOSO de ``tools/font_patch.py``.

``tools/font_patch.py`` es un fichero bloqueado v20 (SHA-256 04cf7ff5…, ver
``tools/dialogue_lock.py``): nunca se copia ni se reformatea. Este módulo sirve sus
nombres por atributo sin cargarlo al importarse, de modo que ``glifos.PLAN is
font_patch.PLAN`` y ``glifos.Font is font_patch.Font``.
"""
from __future__ import annotations

from types import ModuleType

__all__ = ["NOMBRES", "modulo"]

NOMBRES = ("PLAN", "Font", "morton8", "ink_bbox", "add_acute", "add_diaer", "add_tilde",
           "vflip", "rot180", "patch_font", "patch_font_bytes")


def modulo() -> ModuleType:
    """Devuelve el módulo ``font_patch`` real de tools/."""
    from ie123kit.nucleo.config.congelados import cargar
    return cargar("font_patch")


def __getattr__(nombre: str):
    if nombre in NOMBRES or not nombre.startswith("_"):
        try:
            return getattr(modulo(), nombre)
        except AttributeError:
            pass
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


def __dir__():
    return sorted(set(globals()) | set(dir(modulo())))
