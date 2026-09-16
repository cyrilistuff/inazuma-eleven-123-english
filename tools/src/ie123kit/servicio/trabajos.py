"""Trabajos en segundo plano con eventos JSONL y cancelación.

Capa `servicio`: sin asyncio y sin efectos al importar. La GUI futura (PySide6)
consumirá :meth:`Trabajos.eventos` desde su propio hilo.

Camino preferido para emitir eventos: la función de trabajo recibe los
parámetros `progreso` (callable) y `cancel` (``CancelToken``); emite progreso o
incidencias llamando a `progreso(...)`. El método :meth:`Trabajos.emitir` existe
solo para llamantes externos que ya tienen el id del trabajo.
"""

from __future__ import annotations

import enum
import json
import queue
import threading
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from ie123kit.nucleo.errores import CanceladoError
from ie123kit.nucleo.tipos import CancelToken, Incidencia, Progreso, Resultado
from ie123kit.nucleo.util import ahora_iso

__all__ = ["EstadoTrabajo", "Trabajo", "Trabajos"]


class EstadoTrabajo(enum.StrEnum):
    """Estados posibles de un trabajo."""

    PENDIENTE = "pendiente"
    EJECUTANDO = "ejecutando"
    HECHO = "hecho"
    ERROR = "error"
    CANCELADO = "cancelado"


@dataclass(frozen=True)
class Trabajo:
    """Instantánea inmutable del estado de un trabajo."""

    id: str
    estado: EstadoTrabajo
    creado_en: str
    terminado_en: str | None = None
    resultado: Resultado | None = None
    error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "estado": str(self.estado),
            "creado_en": self.creado_en,
            "terminado_en": self.terminado_en,
            "resultado": self.resultado.to_json() if self.resultado is not None else None,
            "error": self.error,
        }


_FIN = object()


class _Entrada:
    """Estado interno de un trabajo (protegido por el lock de `Trabajos`)."""

    __slots__ = ("cancel", "cola", "cond", "eventos", "trabajo")

    def __init__(self, trabajo: Trabajo, cancel: CancelToken, cond: threading.Condition) -> None:
        self.trabajo = trabajo
        self.cancel = cancel
        # Cola por trabajo (canal en vivo para llamantes que prefieran `get`);
        # `eventos()` lee de la lista por índice para admitir varios consumidores.
        self.cola: queue.Queue[Any] = queue.Queue()
        self.eventos: list[Any] = []
        self.cond = cond


class Trabajos:
    """Cola de trabajos ejecutados en hilos, con eventos y registro JSONL."""

    def __init__(self, dir_eventos: Path | None = None, *, max_hilos: int = 2, reloj: Callable[[], str] | None = None):
        self._dir_eventos = Path(dir_eventos) if dir_eventos is not None else None
        self._reloj = reloj or ahora_iso
        self._lock = threading.Lock()
        self._trabajos: dict[str, _Entrada] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_hilos, thread_name_prefix="ie123-trabajo")
        self._dir_listo = False

    # -- API pública ---------------------------------------------------

    def enviar(self, fn: Callable[..., Resultado | None], /, **kw: Any) -> str:
        """Encola `fn`, que se llamará como ``fn(progreso=..., cancel=..., **kw)``."""
        id_trabajo = uuid.uuid4().hex[:12]
        cancel = CancelToken()
        entrada = _Entrada(
            Trabajo(id=id_trabajo, estado=EstadoTrabajo.PENDIENTE, creado_en=self._reloj()),
            cancel,
            threading.Condition(self._lock),
        )
        with self._lock:
            self._trabajos[id_trabajo] = entrada
        self._executor.submit(self._ejecutar, id_trabajo, fn, kw)
        return id_trabajo

    def estado(self, id_trabajo: str) -> Trabajo:
        return self._entrada(id_trabajo).trabajo

    def eventos(self, id_trabajo: str, *, timeout: float | None = None) -> Iterator[Progreso | Incidencia | Trabajo]:
        """Itera los eventos del trabajo; reproduce los ya emitidos y sigue en vivo."""
        entrada = self._entrada(id_trabajo)
        indice = 0
        while True:
            with self._lock:
                while indice >= len(entrada.eventos):
                    if not entrada.cond.wait(timeout):
                        return
                evento = entrada.eventos[indice]
            indice += 1
            if evento is _FIN:
                return
            yield evento

    def emitir(self, id_trabajo: str, incidencia: Incidencia) -> None:
        """Emite una incidencia desde fuera del propio trabajo (camino secundario)."""
        self._publicar(self._entrada(id_trabajo), incidencia, "incidencia")

    def cancelar(self, id_trabajo: str) -> bool:
        entrada = self._entrada(id_trabajo)
        with self._lock:
            if _es_final(entrada.trabajo.estado):
                return False
        entrada.cancel.cancelar()
        return True

    def esperar(self, id_trabajo: str, timeout: float | None = None) -> Trabajo:
        entrada = self._entrada(id_trabajo)
        with self._lock:
            while not _es_final(entrada.trabajo.estado):
                if not entrada.cond.wait(timeout):
                    break
            return entrada.trabajo

    def cerrar(self) -> None:
        self._executor.shutdown(wait=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.cerrar()

    # -- interno -------------------------------------------------------

    def _entrada(self, id_trabajo: str) -> _Entrada:
        with self._lock:
            entrada = self._trabajos.get(id_trabajo)
        if entrada is None:
            raise KeyError(f"no existe el trabajo {id_trabajo!r}")
        return entrada

    def _ejecutar(self, id_trabajo: str, fn: Callable[..., Resultado | None], kw: dict[str, Any]) -> None:
        entrada = self._entrada(id_trabajo)
        self._cambiar_estado(entrada, EstadoTrabajo.EJECUTANDO)

        def progreso(evento: Progreso | Incidencia) -> None:
            tipo = "incidencia" if isinstance(evento, Incidencia) else "progreso"
            self._publicar(entrada, evento, tipo)

        resultado: Resultado | None = None
        estado = EstadoTrabajo.HECHO
        error: str | None = None
        try:
            resultado = fn(progreso=progreso, cancel=entrada.cancel, **kw)
        except CanceladoError:
            estado = EstadoTrabajo.CANCELADO
        except BaseException as exc:  # noqa: BLE001 - ninguna excepción debe escapar del hilo
            estado = EstadoTrabajo.ERROR
            error = repr(exc)
        if resultado is not None:
            self._publicar(entrada, resultado, "resultado")
        self._cambiar_estado(entrada, estado, resultado=resultado, error=error, final=True)

    def _cambiar_estado(
        self,
        entrada: _Entrada,
        estado: EstadoTrabajo,
        *,
        resultado: Resultado | None = None,
        error: str | None = None,
        final: bool = False,
    ) -> None:
        with self._lock:
            anterior = entrada.trabajo
            entrada.trabajo = Trabajo(
                id=anterior.id,
                estado=estado,
                creado_en=anterior.creado_en,
                terminado_en=self._reloj() if final else None,
                resultado=resultado,
                error=error,
            )
            trabajo = entrada.trabajo
        self._escribir_jsonl(trabajo.id, "estado", {"estado": str(estado)})
        self._encolar(entrada, trabajo)
        if final:
            self._encolar(entrada, _FIN)

    def _publicar(self, entrada: _Entrada, evento: Any, tipo: str) -> None:
        with self._lock:
            id_trabajo = entrada.trabajo.id
        self._escribir_jsonl(id_trabajo, tipo, evento.to_json())
        self._encolar(entrada, evento)

    def _encolar(self, entrada: _Entrada, evento: Any) -> None:
        with self._lock:
            entrada.eventos.append(evento)
            entrada.cond.notify_all()
        entrada.cola.put(evento)

    def _escribir_jsonl(self, id_trabajo: str, tipo: str, datos: dict[str, Any]) -> None:
        if self._dir_eventos is None:
            return
        linea = {"trabajo": id_trabajo, "ts": self._reloj(), "tipo": tipo, "datos": datos}
        with self._lock:
            if not self._dir_listo:
                self._dir_eventos.mkdir(parents=True, exist_ok=True)
                self._dir_listo = True
            destino = self._dir_eventos / f"{id_trabajo}.jsonl"
            with destino.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(linea, ensure_ascii=False) + "\n")
                fh.flush()


def _es_final(estado: EstadoTrabajo) -> bool:
    return estado in (EstadoTrabajo.HECHO, EstadoTrabajo.ERROR, EstadoTrabajo.CANCELADO)
