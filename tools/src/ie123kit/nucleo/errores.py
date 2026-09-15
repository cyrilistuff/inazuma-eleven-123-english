"""Jerarquía de excepciones de ie123kit (sin dependencias)."""

from __future__ import annotations

import os

__all__ = [
    "BloqueoTipograficoError",
    "FormatoError",
    "Ie123Error",
    "RaizNoEncontradaError",
    "ValidacionError",
]


class Ie123Error(Exception):
    """Base de todos los errores de ie123kit."""


class RaizNoEncontradaError(Ie123Error):
    """No se localiza la raíz del repositorio."""


class FormatoError(Ie123Error, ValueError):
    """Datos con un formato inválido."""


class ValidacionError(Ie123Error):
    """Una comprobación ha fallado."""

    def __init__(self, codigo: str, ruta: str | os.PathLike | None = None, detalle: str = "") -> None:
        self.codigo = codigo
        self.ruta = os.fspath(ruta) if ruta is not None else None
        self.detalle = detalle
        partes = [p for p in (codigo, self.ruta, detalle) if p]
        super().__init__(": ".join(partes))


class BloqueoTipograficoError(ValidacionError):
    """Se ha violado el bloqueo tipográfico v20."""
