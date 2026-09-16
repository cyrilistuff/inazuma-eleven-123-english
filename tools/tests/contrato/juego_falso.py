"""JuegoFalso: implementación de JuegoBase sobre un archive.fa sintético, sin ROM ni work/ real."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ie123kit.nucleo.contenedores.fa import FaArchive
from ie123kit.nucleo.juego import InfoObjetivo, JuegoBase, PerfilTexto
from ie123kit.nucleo.tipos import AssetRef, CancelToken, Incidencia, Progreso, Resultado, componer_id

__all__ = ["FICHEROS", "OBJETIVO", "JuegoFalso"]

OBJETIVO = "falso"

#: Contenido del archive.fa sintético que monta la suite de contrato.
FICHEROS: dict[str, bytes] = {
    "falso/uno.bin": b"uno" * 5,
    "falso/dos.bin": b"dos" * 4,
}


def _ruta_base(ws: Any) -> Path:
    return Path(ws.work) / "shared" / "base_3ds" / "romfs" / "archive.fa"


def _dir_exportaciones(ws: Any) -> Path:
    try:
        return Path(ws.dirs(OBJETIVO).exportaciones)
    except Exception:  # noqa: BLE001 - el doble vale para cualquier workspace, también los falsos
        return Path(ws.work) / OBJETIVO / "exportaciones"


class JuegoFalso(JuegoBase):
    """Objetivo de prueba con activos.toml embebido (no hay paquete en src/)."""

    PAQUETE = "tools.tests.contrato.juego_falso"

    def info(self) -> InfoObjetivo:
        return InfoObjetivo(
            id=OBJETIVO,
            nombre="Juego falso",
            prefijos_romfs=("falso/",),
            cros=("cro/ina_menu.cro",),
            capacidades=frozenset({"graficos"}),
        )

    def perfil_texto(self, ambito: str | None = None) -> PerfilTexto:
        return PerfilTexto("tipografia_v20", bloqueado=True)

    # -- activos ----------------------------------------------------------

    def _entradas(self, ws: Any) -> list[tuple[str, int, int]]:
        arc = FaArchive(_ruta_base(ws))
        return [(ruta, off, tam) for ruta, off, tam in arc.entries]

    def activos(self, ws: Any, tipo: str | None = None, filtro: str | None = None) -> list[AssetRef]:
        refs = []
        for ruta, _off, tam in self._entradas(ws):
            refs.append(
                AssetRef(
                    id=componer_id(OBJETIVO, "grafico", ruta),
                    objetivo=OBJETIVO,
                    tipo="grafico",
                    ruta_romfs=ruta,
                    cadena_contenedores=("fa",),
                    tamano=tam,
                    editable=True,
                )
            )
        if tipo is not None:
            refs = [r for r in refs if r.tipo == tipo]
        if filtro is not None:
            refs = [r for r in refs if filtro in r.id]
        return refs

    def _buscar(self, ws: Any, ref: Any) -> tuple[str, bytes] | None:
        identificador = getattr(ref, "id", ref)
        arc = FaArchive(_ruta_base(ws))
        for ruta, off, tam in arc.entries:
            if componer_id(OBJETIVO, "grafico", ruta) == identificador or ruta == identificador:
                return ruta, arc.file_bytes(off, tam)
        return None

    # -- exportar / importar ----------------------------------------------

    def exportar(self, ws: Any, ref: Any, destino: Any, formato: str | None = None,
                 progreso: Callable[[Any], None] | None = None,
                 cancel: CancelToken | None = None) -> Resultado:
        def paso(n: int, mensaje: str) -> None:
            if cancel is not None:
                cancel.comprobar()
            if progreso is not None:
                progreso(Progreso(fase="exportar", actual=n, total=3, mensaje=mensaje))

        paso(1, "localizando")
        hallado = self._buscar(ws, ref)
        if hallado is None:
            return Resultado.no_soportado(f"activo desconocido: {getattr(ref, 'id', ref)!r}")
        ruta, datos = hallado
        paso(2, "leyendo")
        destino = Path(destino)
        salida = destino / Path(ruta).name if destino.suffix == "" else destino
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_bytes(datos)
        paso(3, "escrito")
        return Resultado.correcto(datos={"ruta_romfs": ruta, "tamano": len(datos)}, artefactos=(str(salida),))

    def importar(self, ws: Any, ref: Any, origen: Any, simular: bool = True,
                 progreso: Callable[[Any], None] | None = None,
                 cancel: CancelToken | None = None) -> Resultado:
        if cancel is not None:
            cancel.comprobar()
        hallado = self._buscar(ws, ref)
        if hallado is None:
            return Resultado.no_soportado(f"activo desconocido: {getattr(ref, 'id', ref)!r}")
        ruta, datos = hallado
        origen = Path(origen)
        if not origen.is_file():
            return Resultado.fallo(
                [Incidencia("NOT_SUPPORTED", "error", f"no existe el fichero de origen: {origen}",
                            activo_id=getattr(ref, "id", str(ref)), ruta=str(origen))]
            )
        nuevos = origen.read_bytes()
        if progreso is not None:
            progreso(Progreso(fase="importar", actual=1, total=2, mensaje="validando"))
        if len(nuevos) != len(datos):
            return Resultado.fallo(
                [Incidencia("EXCEDE_BYTES", "error",
                            f"tamaño inesperado: {len(nuevos)} bytes; se esperaban {len(datos)}",
                            activo_id=getattr(ref, "id", str(ref)), ruta=str(origen))]
            )
        diff = {"ruta_romfs": ruta, "bytes_antes": len(datos), "bytes_despues": len(nuevos),
                "cambia": nuevos != datos}
        if simular:
            return Resultado.correcto(datos={"simulado": True, "diff": diff})
        destino = _dir_exportaciones(ws) / Path(ruta).name
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(nuevos)
        if progreso is not None:
            progreso(Progreso(fase="importar", actual=2, total=2, mensaje="escrito"))
        return Resultado.correcto(datos={"simulado": False, "diff": diff}, artefactos=(str(destino),))
