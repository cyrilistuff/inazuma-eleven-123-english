"""Cargador de los ficheros congelados de tools/ (bloqueo tipográfico v20).

Los ficheros bloqueados (AGENTS.md, ``tools/dialogue_lock.py``) nunca se copian ni se
reformatean: se importan tal cual como módulos de NIVEL SUPERIOR para compartir
``sys.modules`` con las capas de ``work/`` y los scripts de ``tools/``.
``build_ui_revision`` no se importa como módulo (v55 hace ``exec`` de su texto).

Importar este módulo no produce efectos: la carga ocurre al llamar a :func:`cargar`.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

from ie123kit.nucleo.config.raiz import find_root

__all__ = ["IMPORTABLES", "cargar"]

IMPORTABLES = ("dialogue_typography", "font_patch", "dialogue_lock", "build_ie1_probe")


def cargar(nombre: str, raiz: Path | None = None) -> ModuleType:
    """Importa el fichero congelado ``tools/<nombre>.py`` y lo devuelve.

    Lanza ValueError si ``nombre`` no está en IMPORTABLES e ImportError si el módulo
    resuelto no es el de ``tools/`` de la raíz.
    """
    if nombre not in IMPORTABLES:
        raise ValueError(f"{nombre!r} no es un fichero congelado importable: {IMPORTABLES}")
    tools = Path(raiz if raiz is not None else find_root()) / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    mod = importlib.import_module(nombre)
    origen = getattr(mod, "__file__", None)
    if origen is None or Path(origen).resolve().parent != tools.resolve():
        raise ImportError(f"{nombre} se ha resuelto fuera de {tools}: {origen}")
    return mod
