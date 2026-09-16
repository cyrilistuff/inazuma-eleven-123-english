"""Localización de las herramientas externas (3dstool, xdelta3, mobipeg, vgmstream, ffmpeg).

Sustituye las rutas fijas ``tools/bin/<x>.exe`` copiadas por las capas de ``work/``.

Orden de búsqueda (la primera que existe gana):

1. Variable de entorno ``IE123_<NOMBRE>`` (por ejemplo ``IE123_3DSTOOL``).
2. Tabla ``[herramientas]`` de la configuración del proyecto: ``ie123.local.toml``
   (ignorado por git, rutas de la máquina) y luego ``ie123.toml``. También se admite
   ``herramientas.dir`` como carpeta donde buscar.
3. ``tools/bin/``.
4. ``work/shared/herramientas/**`` (búsqueda recursiva).
5. El ``PATH`` del sistema (``shutil.which``).

Este módulo vive en ``nucleo`` y por eso NO importa ``servicio``: replica la lectura de
``ie123.toml`` / ``ie123.local.toml`` que hace ``servicio.proyecto.Workspace``. No tiene
efectos al importar ni caché global mutable.
"""

from __future__ import annotations

import os
import shutil
import tomllib
from pathlib import Path

from ie123kit.nucleo.config.raiz import find_root
from ie123kit.nucleo.errores import ValidacionError

__all__ = ["HERRAMIENTAS", "HerramientaAusente", "exigir", "localizar"]


class HerramientaAusente(ValidacionError):
    """No se encuentra una herramienta externa necesaria."""


#: Nombre canónico -> nombres de fichero admitidos y pista para el usuario.
HERRAMIENTAS: dict[str, tuple[tuple[str, ...], str]] = {
    "3dstool": (("3dstool.exe", "3dstool"), "Reconstrucción de la ROM .3ds (romfs -> cxi -> 3ds)."),
    "xdelta3": (("xdelta3.exe", "xdelta3"), "Generación del parche .xdelta (único entregable)."),
    "mobipeg": (("mobipeg.exe", "mobipeg", "ffmpeg_x86_v2.1.exe"), "ffmpeg x86 v2.1 para los .moflex."),
    "vgmstream": (("vgmstream-cli.exe", "vgmstream-cli", "test.exe"), "Volcado de audio SADL/BCSTM."),
    "ffmpeg": (("ffmpeg.exe", "ffmpeg"), "Conversión de audio y vídeo genérica."),
}


def _variable(nombre: str) -> str:
    return "IE123_" + "".join(c if c.isalnum() else "_" for c in nombre).upper()


def _leer_toml(ruta: Path) -> dict:
    if not ruta.is_file():
        return {}
    with ruta.open("rb") as fh:
        return tomllib.load(fh)


def _tabla_herramientas(raiz: Path) -> dict:
    """Fusiona ``[herramientas]`` de ie123.toml y ie123.local.toml (local manda)."""
    fusion: dict = {}
    for fichero in ("ie123.toml", "ie123.local.toml"):
        tabla = _leer_toml(raiz / fichero).get("herramientas")
        if isinstance(tabla, dict):
            fusion.update(tabla)
    return fusion


def _archivo(candidato: Path) -> Path | None:
    return candidato.resolve() if candidato.is_file() else None


def _raiz(ws) -> Path | None:
    """Raíz del repositorio: la de ``ws`` si se pasa uno, si no la detectada."""
    if ws is not None:
        return Path(ws.raiz).resolve()
    try:
        return find_root()
    except Exception:  # noqa: BLE001 - fuera del repo aún se puede usar el PATH
        return None


def localizar(nombre: str, *, ws=None, entorno: dict[str, str] | None = None) -> Path | None:
    """Devuelve la ruta absoluta de la herramienta ``nombre`` o ``None`` si no aparece.

    ``ws`` es un ``servicio.proyecto.Workspace`` opcional (solo se lee su ``.raiz``), así que
    ``nucleo`` no depende de ``servicio``. ``entorno`` es inyectable para los tests.
    """
    if nombre not in HERRAMIENTAS:
        raise ValidacionError("HERRAMIENTA_DESCONOCIDA", detalle=f"'{nombre}'; conocidas: {', '.join(HERRAMIENTAS)}")
    nombres_fichero, _ = HERRAMIENTAS[nombre]
    entorno = dict(os.environ if entorno is None else entorno)

    valor = entorno.get(_variable(nombre))
    if valor:
        hallado = _archivo(Path(valor).expanduser())
        if hallado is not None:
            return hallado

    raiz = _raiz(ws)
    if raiz is not None:
        tabla = _tabla_herramientas(raiz)
        valor = tabla.get(nombre)
        if isinstance(valor, str) and valor:
            ruta = Path(valor).expanduser()
            hallado = _archivo(ruta if ruta.is_absolute() else raiz / ruta)
            if hallado is not None:
                return hallado
        carpeta = tabla.get("dir")
        carpetas = [] if not isinstance(carpeta, str) or not carpeta else [Path(carpeta).expanduser()]
        carpetas = [c if c.is_absolute() else raiz / c for c in carpetas]
        carpetas.append(raiz / "tools" / "bin")
        for c in carpetas:
            for fichero in nombres_fichero:
                hallado = _archivo(c / fichero)
                if hallado is not None:
                    return hallado
        externas = raiz / "work" / "shared" / "herramientas"
        if externas.is_dir():
            for candidato in sorted(externas.rglob("*")):
                if candidato.is_file() and candidato.name.lower() in {f.lower() for f in nombres_fichero}:
                    return candidato.resolve()

    for fichero in nombres_fichero:
        cual = shutil.which(fichero, path=entorno.get("PATH"))
        if cual:
            return Path(cual).resolve()
    return None


def exigir(nombre: str, *, ws=None, entorno: dict[str, str] | None = None) -> Path:
    """Como :func:`localizar` pero lanza ``HerramientaAusente`` si no aparece."""
    hallado = localizar(nombre, ws=ws, entorno=entorno)
    if hallado is None:
        _, pista = HERRAMIENTAS[nombre]
        raise HerramientaAusente(
            "HERRAMIENTA_AUSENTE",
            detalle=(
                f"no se encuentra '{nombre}'. {pista} Colócala en tools/bin/, apúntala en "
                f"[herramientas] de ie123.local.toml o fija {_variable(nombre)}."
            ),
        )
    return hallado
