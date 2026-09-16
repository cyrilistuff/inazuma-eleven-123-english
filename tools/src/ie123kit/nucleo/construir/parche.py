"""Generación del parche .xdelta, el ÚNICO entregable que se distribuye (ver LEGAL.md).

Reproduce EXACTAMENTE la invocación de ``tools/build_patch.ps1`` para que el parche salga byte a
byte igual que el que se ha publicado hasta ahora::

    xdelta3.exe -e -f -B 2147483648 -s <rom_base> <rom_parcheada> <salida>

Banderas, en ese mismo orden (no se cambian ni se reordenan):

* ``-e``  codificar (generar el delta).
* ``-f``  forzar la sobrescritura del fichero de salida.
* ``-B 2147483648`` ventana de fuente = tamaño de la ROM (2 GiB). Sin esto xdelta usa la ventana
  por defecto de 64 MiB y el parche sale ENORME (~509 MB) en vez de unos pocos MB.
* ``-s <rom_base>`` ROM original como fuente; después el destino y el fichero de salida.

Cualquier cambio (otra versión de xdelta3, otras banderas, otro orden) produce un .xdelta
distinto y rompe la reproducibilidad de las releases ya publicadas.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ie123kit.nucleo import util
from ie123kit.nucleo.config import herramientas
from ie123kit.nucleo.errores import ValidacionError

__all__ = ["VENTANA_FUENTE", "xdelta"]

#: ``-B``: ventana de fuente de 2 GiB (idéntica a tools/build_patch.ps1).
VENTANA_FUENTE = "2147483648"


def _ejecutar(argumentos: list[str]) -> dict:
    """Ejecuta xdelta3. Función aparte para poder monkeypatchearla en los tests."""
    proceso = subprocess.run(argumentos, capture_output=True, text=True, check=False)
    return {
        "argumentos": list(argumentos),
        "returncode": proceso.returncode,
        "stdout": (proceso.stdout or "")[-4000:],
        "stderr": (proceso.stderr or "")[-4000:],
    }


def xdelta(rom_base, rom_parcheada, salida, *, herramienta=None) -> dict:
    """Genera ``salida`` (.xdelta) a partir de ``rom_base`` y ``rom_parcheada``."""
    rom_base = Path(rom_base).resolve()
    rom_parcheada = Path(rom_parcheada).resolve()
    salida = Path(salida).resolve()
    for rom in (rom_base, rom_parcheada):
        if not rom.is_file():
            raise FileNotFoundError(rom)
    tool = Path(herramienta).resolve() if herramienta is not None else herramientas.exigir("xdelta3")
    salida.parent.mkdir(parents=True, exist_ok=True)

    paso = _ejecutar([
        str(tool), "-e", "-f", "-B", VENTANA_FUENTE, "-s", str(rom_base), str(rom_parcheada), str(salida),
    ])
    if paso["returncode"] != 0:
        raise ValidacionError(
            "XDELTA_FALLO",
            detalle=f"código {paso['returncode']}: {(paso['stderr'] or paso['stdout']).strip()[-400:]}",
        )
    if not salida.is_file():
        raise ValidacionError("PARCHE_NO_GENERADO", ruta=salida, detalle="xdelta3 terminó sin crear el parche")
    return {
        "path": str(salida),
        "sha256": util.sha256_file(salida),
        "bytes": salida.stat().st_size,
        "rom_base": str(rom_base),
        "rom_parcheada": str(rom_parcheada),
        "herramienta": str(tool),
        "proceso": paso,
    }
