"""Fachada sin cabeza del toolkit: la CLI y la futura GUI solo hablan con ``ServicioToolkit``.

Regla de capas: este módulo NO importa estáticamente ``ie123kit.juego_principal``/``ie1``/``ie2``/``ie3``.
El descubrimiento de juegos se hace con ``importlib.import_module`` sobre la tabla literal ``OBJETIVOS``.
Importar este módulo no tiene efectos: no lee ficheros ni resuelve la raíz del repositorio.
"""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ie123kit.nucleo.juego import InfoObjetivo, JuegoBase
from ie123kit.nucleo.tipos import API_VERSION, CancelToken, Incidencia, Progreso, Resultado

__all__ = [
    "API_VERSION",
    "OBJETIVOS",
    "ServicioToolkit",
    "SolicitudConstruccion",
    "descubrir_juegos",
]

#: Objetivos con ``activos.toml`` hoy y el paquete que los implementa.
OBJETIVOS: dict[str, str] = {
    "juego_principal": "ie123kit.juego_principal",
    "ie1": "ie123kit.ie1",
    "ie2.tormenta_de_fuego": "ie123kit.ie2.tormenta_de_fuego",
    "ie2.ventisca_eterna": "ie123kit.ie2.ventisca_eterna",
    "ie3.rayo_celeste": "ie123kit.ie3.rayo_celeste",
    "ie3.fuego_explosivo": "ie123kit.ie3.fuego_explosivo",
    "ie3.amenaza_del_ogro": "ie123kit.ie3.amenaza_del_ogro",
}

_APLAZADO = "se implementa en F2.2/F2.4"


def _juego_generico(paquete: str) -> JuegoBase:
    """Instancia mínima de JuegoBase para un paquete que aún no declara ``JUEGO`` (llega en F2.3)."""
    clase = type("JuegoGenerico", (JuegoBase,), {"PAQUETE": paquete, "__module__": __name__})
    return clase()


def _cargar_juego(paquete: str) -> JuegoBase | None:
    """Importa `paquete` y devuelve su JuegoBase; None si falta o está roto (nunca lanza).

    Un objetivo que no se carga no desaparece en silencio: `ServicioToolkit._juego` lo
    reporta como incidencia NOT_SUPPORTED en cuanto se pide.
    """
    try:
        modulo = importlib.import_module(paquete)
        declarado = getattr(modulo, "JUEGO", None)
        if declarado is None:
            return _juego_generico(paquete)
        return declarado() if isinstance(declarado, type) else declarado
    except Exception:
        return None


def descubrir_juegos(
    objetivos: dict[str, str] | None = None,
    *,
    extra: dict[str, JuegoBase] | None = None,
) -> dict[str, JuegoBase]:
    """Devuelve {id_objetivo: JuegoBase}. Un paquete ausente o roto se omite (nunca lanza)."""
    tabla = dict(OBJETIVOS if objetivos is None else objetivos)
    juegos: dict[str, JuegoBase] = {}
    for ident, paquete in tabla.items():
        juego = _cargar_juego(paquete)
        if juego is not None:
            juegos[ident] = juego
    for ident, juego in (extra or {}).items():
        juegos[ident] = juego
    return juegos


@dataclass(frozen=True)
class SolicitudConstruccion:
    """Petición de construcción de una candidata de TODA la recopilación."""

    base: str
    objetivos: tuple[str, ...]
    capas: tuple[str, ...]
    salida: str


def _incidencia(codigo: str, mensaje: str, **kw: Any) -> Incidencia:
    return Incidencia(codigo=codigo, severidad="error", mensaje=mensaje, **kw)


class ServicioToolkit:
    """Fachada síncrona. Todos los métodos devuelven ``Resultado`` y admiten ``progreso``/``cancel``."""

    API_VERSION = API_VERSION

    def __init__(self, ws: Any, *, juegos: dict[str, JuegoBase] | None = None, trabajos: Any = None) -> None:
        self.ws = ws
        self.juegos: dict[str, JuegoBase] = juegos if juegos is not None else descubrir_juegos()
        self._trabajos = trabajos

    @classmethod
    def abrir(cls, raiz: str | Path | None = None, **kw: Any) -> ServicioToolkit:
        from ie123kit.servicio.proyecto import Workspace

        return cls(Workspace.abrir(raiz), **kw)

    # -- utilidades internas ------------------------------------------------

    @property
    def trabajos(self) -> Any:
        if self._trabajos is None:
            from ie123kit.servicio.trabajos import Trabajos

            self._trabajos = Trabajos()
        return self._trabajos

    @staticmethod
    def _cronometrar(inicio: float, resultado: Resultado) -> Resultado:
        try:
            object.__setattr__(resultado, "duracion_s", round(time.perf_counter() - inicio, 6))
        except (AttributeError, TypeError):  # no es una dataclass con ese campo
            pass
        return resultado

    def _juego(self, objetivo: str) -> JuegoBase | Resultado:
        juego = self.juegos.get(objetivo)
        if juego is None:
            validos = ", ".join(sorted(self.juegos)) or "(ninguno)"
            return Resultado.fallo(
                [_incidencia("NOT_SUPPORTED", f"Objetivo desconocido: {objetivo!r}. Objetivos válidos: {validos}.")]
            )
        return juego

    def _refs(self, juego: JuegoBase, *, progreso: Any = None, cancel: CancelToken | None = None) -> list[Any]:
        """Activos del objetivo: registro cacheado si se puede, si no el propio juego."""
        try:
            from ie123kit.servicio import registro_activos

            registro = registro_activos.obtener(self.ws, juego, progreso=progreso, cancel=cancel)
            return list(registro.activos)
        except Exception:
            salida = juego.activos(self.ws)
            return list(salida.datos.get("activos", ())) if isinstance(salida, Resultado) else list(salida)

    def _resolver(self, juego: JuegoBase, ident: Any) -> Any | None:
        """Convierte un id de activo en su AssetRef; devuelve None si no existe."""
        if not isinstance(ident, str):
            return ident
        for ref in self._refs(juego):
            if getattr(ref, "id", None) == ident:
                return ref
        return None

    # -- órdenes de proyecto ------------------------------------------------

    def objetivos(self, *, progreso: Callable[[Progreso], None] | None = None,
                  cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        infos: list[dict[str, Any]] = []
        incidencias: list[Incidencia] = []
        for ident, juego in self.juegos.items():
            try:
                info = juego.info()
                infos.append(info.to_json() if isinstance(info, InfoObjetivo) else info)
            except Exception as exc:
                incidencias.append(_incidencia("NOT_SUPPORTED", f"{ident}: no se puede leer info(): {exc}"))
        res = Resultado.correcto(datos={"objetivos": infos}, incidencias=incidencias) if not incidencias or infos \
            else Resultado.fallo(incidencias)
        return self._cronometrar(t0, res)

    def activos(self, objetivo: str, tipo: str | None = None, filtro: str | None = None, *,
                progreso: Callable[[Progreso], None] | None = None,
                cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        juego = self._juego(objetivo)
        if isinstance(juego, Resultado):
            return self._cronometrar(t0, juego)
        try:
            refs = self._refs(juego, progreso=progreso, cancel=cancel)
        except Exception as exc:
            return self._cronometrar(t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"{objetivo}: {exc}")]))
        if tipo is not None:
            refs = [r for r in refs if getattr(r, "tipo", None) == tipo]
        if filtro is not None:
            refs = [r for r in refs if filtro in getattr(r, "id", "")]
        return self._cronometrar(t0, Resultado.correcto(datos={"activos": [r.to_json() for r in refs]}))

    def exportar(self, objetivo: str, ids: list[str] | tuple[str, ...] | str, destino: str | Path, *,
                 formato: str | None = None,
                 progreso: Callable[[Progreso], None] | None = None,
                 cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        juego = self._juego(objetivo)
        if isinstance(juego, Resultado):
            return self._cronometrar(t0, juego)
        lista = [ids] if isinstance(ids, str) else list(ids)
        artefactos: list[str] = []
        incidencias: list[Incidencia] = []
        for ident in lista:
            ref = self._resolver(juego, ident)
            if ref is None:
                incidencias.append(_incidencia("NOT_SUPPORTED", f"{objetivo}: activo desconocido {ident!r}",
                                               activo_id=str(ident)))
                return self._cronometrar(t0, Resultado.fallo(incidencias, artefactos=tuple(artefactos)))
            try:
                res = juego.exportar(self.ws, ref, Path(destino), formato=formato, progreso=progreso, cancel=cancel)
            except Exception as exc:
                incidencias.append(_incidencia("NOT_SUPPORTED", f"{objetivo}:{ident}: {exc}", activo_id=str(ident)))
                return self._cronometrar(t0, Resultado.fallo(incidencias, artefactos=tuple(artefactos)))
            incidencias.extend(res.incidencias)
            artefactos.extend(str(a) for a in res.artefactos)
            if not res.ok:
                return self._cronometrar(t0, Resultado.fallo(incidencias, artefactos=tuple(artefactos)))
        return self._cronometrar(
            t0,
            Resultado.correcto(datos={"exportados": [str(i) for i in lista]},
                               incidencias=tuple(incidencias), artefactos=tuple(artefactos)),
        )

    def importar(self, objetivo: str, id: str, fichero: str | Path, simular: bool = True, *,
                 progreso: Callable[[Progreso], None] | None = None,
                 cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        juego = self._juego(objetivo)
        if isinstance(juego, Resultado):
            return self._cronometrar(t0, juego)
        ref = self._resolver(juego, id)
        if ref is None:
            return self._cronometrar(
                t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"{objetivo}: activo desconocido {id!r}",
                                                 activo_id=str(id))])
            )
        try:
            res = juego.importar(self.ws, ref, Path(fichero), simular=simular, progreso=progreso, cancel=cancel)
        except Exception as exc:
            return self._cronometrar(
                t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"{objetivo}:{id}: {exc}", activo_id=str(id))])
            )
        return self._cronometrar(t0, res)

    def construir(self, solicitud: SolicitudConstruccion, *,
                  progreso: Callable[[Progreso], None] | None = None,
                  cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        return self._cronometrar(t0, Resultado.no_soportado(f"construir {_APLAZADO}"))

    def verificar(self, candidata: str, golden: bool | str | None = None, *,
                  progreso: Callable[[Progreso], None] | None = None,
                  cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        return self._cronometrar(t0, Resultado.no_soportado(f"verificar {_APLAZADO}"))

    def instalar(self, candidata: str, emulador: str = "azahar", lanzar: bool = False, *,
                 progreso: Callable[[Progreso], None] | None = None,
                 cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        return self._cronometrar(t0, Resultado.no_soportado(f"instalar {_APLAZADO}"))

    def parche(self, rom_base: str | Path, rom_parcheada: str | Path, salida: str | Path, *,
               progreso: Callable[[Progreso], None] | None = None,
               cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        return self._cronometrar(t0, Resultado.no_soportado(f"parche {_APLAZADO}"))

    def limpiar(self, borrar: bool = False, *,
                progreso: Callable[[Progreso], None] | None = None,
                cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        try:
            from ie123kit.nucleo.construir import limpieza

            objetivos = [str(p) for p in limpieza.objetivos()]
            if borrar and hasattr(limpieza, "borrar"):
                limpieza.borrar()
            datos = {"objetivos": objetivos, "borrado": bool(borrar)}
            return self._cronometrar(t0, Resultado.correcto(datos=datos))
        except Exception as exc:
            return self._cronometrar(t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"limpiar: {exc}")]))

    def doctor(self, *, progreso: Callable[[Progreso], None] | None = None,
               cancel: CancelToken | None = None) -> Resultado:
        t0 = time.perf_counter()
        try:
            salida = self.ws.doctor()
        except Exception as exc:
            return self._cronometrar(t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"doctor: {exc}")]))
        if isinstance(salida, Resultado):
            datos = dict(salida.datos or {})
            datos["api_version"] = API_VERSION
            return self._cronometrar(
                t0, Resultado.correcto(datos=datos, incidencias=list(salida.incidencias))
                if salida.ok else Resultado.fallo(list(salida.incidencias))
            )
        datos = dict(salida) if isinstance(salida, dict) else {"doctor": salida}
        datos["api_version"] = API_VERSION
        return self._cronometrar(t0, Resultado.correcto(datos=datos))

    # -- trabajos -----------------------------------------------------------

    def enviar_trabajo(self, nombre_metodo: str, **kw: Any) -> Resultado:
        """Lanza un método de la fachada en un hilo de ``Trabajos`` y devuelve su id."""
        t0 = time.perf_counter()
        metodo = getattr(self, nombre_metodo, None)
        if not callable(metodo) or nombre_metodo.startswith("_"):
            return self._cronometrar(
                t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"Método desconocido: {nombre_metodo!r}")])
            )
        try:
            ident = self.trabajos.enviar(metodo, **kw)
        except Exception as exc:
            return self._cronometrar(t0, Resultado.fallo([_incidencia("NOT_SUPPORTED", f"enviar_trabajo: {exc}")]))
        return self._cronometrar(t0, Resultado.correcto(datos={"trabajo": ident}))
