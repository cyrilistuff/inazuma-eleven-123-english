"""Localización de la raíz del repositorio (AGENTS.md junto a tools/pyproject.toml)."""

from __future__ import annotations

import os
from pathlib import Path

from ie123kit.nucleo.errores import RaizNoEncontradaError

__all__ = ["es_raiz", "find_root"]


def es_raiz(d: str | os.PathLike) -> bool:
    """Indica si ``d`` contiene AGENTS.md y tools/pyproject.toml."""
    d = Path(d)
    return (d / "AGENTS.md").is_file() and (d / "tools" / "pyproject.toml").is_file()


def find_root(inicio: str | os.PathLike | None = None) -> Path:
    """Devuelve la raíz del repositorio; la variable IE123_ROOT tiene prioridad."""
    valor = os.environ.get("IE123_ROOT")
    if valor:
        p = Path(valor).expanduser().resolve()
        if es_raiz(p):
            return p
        faltan = [n for n in ("AGENTS.md", "tools/pyproject.toml") if not (p / n).is_file()]
        raise RaizNoEncontradaError(f"IE123_ROOT={p} no es la raíz del repositorio: falta {', '.join(faltan)}")
    if inicio is not None:
        puntos = [Path(inicio).resolve()]
    else:
        puntos = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for punto in puntos:
        for d in [punto, *punto.parents]:
            if es_raiz(d):
                return d
    raise RaizNoEncontradaError(
        "No se encuentra la raíz del repositorio: se busca AGENTS.md junto a tools/pyproject.toml subiendo desde "
        + ", ".join(str(p) for p in puntos)
        + ". Se puede fijar la variable de entorno IE123_ROOT."
    )
