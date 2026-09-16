"""Tests de `ie123kit.servicio.trabajos` (sin ROM, sin esperas largas)."""

from __future__ import annotations

import json
import threading

import pytest

from ie123kit.nucleo.tipos import Incidencia, Progreso, Resultado
from ie123kit.servicio.trabajos import EstadoTrabajo, Trabajos

TIEMPO = 2.0


def _resultado(ok: bool = True) -> Resultado:
    return Resultado(ok=ok, datos={"n": 3})


def _trabajo_ok(*, progreso, cancel, total: int = 3) -> Resultado:
    for i in range(1, total + 1):
        cancel.comprobar()
        progreso(Progreso(fase="prueba", actual=i, total=total, mensaje=f"paso {i}"))
    return _resultado()


def test_trabajo_correcto(tmp_path):
    with Trabajos(tmp_path) as trabajos:
        id_t = trabajos.enviar(_trabajo_ok)
        trabajo = trabajos.esperar(id_t, TIEMPO)
    assert trabajo.estado is EstadoTrabajo.HECHO
    assert trabajo.resultado is not None
    assert trabajo.resultado.ok is True
    assert trabajo.terminado_en


def test_progreso_monotono(tmp_path):
    with Trabajos(tmp_path) as trabajos:
        id_t = trabajos.enviar(_trabajo_ok, total=5)
        progresos = [e for e in trabajos.eventos(id_t, timeout=TIEMPO) if isinstance(e, Progreso)]
    assert [p.actual for p in progresos] == sorted(p.actual for p in progresos)
    assert len({p.total for p in progresos}) == 1
    assert len(progresos) == 5


def test_cancelacion(tmp_path):
    arrancado = threading.Event()

    def bucle(*, progreso, cancel):
        arrancado.set()
        while True:
            cancel.comprobar()

    with Trabajos(tmp_path) as trabajos:
        id_t = trabajos.enviar(bucle)
        assert arrancado.wait(TIEMPO)
        assert trabajos.cancelar(id_t) is True
        trabajo = trabajos.esperar(id_t, TIEMPO)
        assert trabajo.estado is EstadoTrabajo.CANCELADO
        assert trabajos.cancelar(id_t) is False


def test_excepcion_deja_error(tmp_path):
    def falla(*, progreso, cancel):
        raise RuntimeError("bum")

    with Trabajos(tmp_path) as trabajos:
        id_t = trabajos.enviar(falla)
        trabajo = trabajos.esperar(id_t, TIEMPO)
    assert trabajo.estado is EstadoTrabajo.ERROR
    assert "bum" in (trabajo.error or "")


def test_jsonl(tmp_path):
    def con_incidencia(*, progreso, cancel):
        # El código debe pertenecer al catálogo cerrado de nucleo/tipos.CODIGOS: uno inventado
        # hace que Incidencia lance ValueError dentro del trabajo y lo deje en ERROR.
        progreso(Progreso(fase="p", actual=1, total=1, mensaje="uno"))
        progreso(Incidencia(codigo="GLIFO_NO_SOPORTADO", severidad="aviso", mensaje="ojo"))
        return _resultado()

    with Trabajos(tmp_path) as trabajos:
        id_t = trabajos.enviar(con_incidencia)
        trabajos.esperar(id_t, TIEMPO)
    lineas = (tmp_path / f"{id_t}.jsonl").read_text(encoding="utf-8").splitlines()
    eventos = [json.loads(linea) for linea in lineas]
    for evento in eventos:
        assert set(evento) == {"trabajo", "ts", "tipo", "datos"}
        assert evento["trabajo"] == id_t
    tipos = [e["tipo"] for e in eventos]
    assert tipos[0] == "estado"
    assert tipos[-1] == "estado"
    assert eventos[0]["datos"] == {"estado": "ejecutando"}
    assert eventos[-1]["datos"] == {"estado": "hecho"}
    assert "progreso" in tipos and "incidencia" in tipos and "resultado" in tipos


def test_sin_dir_eventos_no_escribe(tmp_path):
    with Trabajos(None) as trabajos:
        id_t = trabajos.enviar(_trabajo_ok)
        trabajos.esperar(id_t, TIEMPO)
    assert list(tmp_path.iterdir()) == []


def test_eventos_reproducidos_tras_terminar(tmp_path):
    with Trabajos(tmp_path) as trabajos:
        id_t = trabajos.enviar(_trabajo_ok)
        trabajos.esperar(id_t, TIEMPO)
        primera = list(trabajos.eventos(id_t, timeout=TIEMPO))
        segunda = list(trabajos.eventos(id_t, timeout=TIEMPO))
    assert primera and [type(e) for e in primera] == [type(e) for e in segunda]
    assert [getattr(e, "actual", None) for e in primera] == [getattr(e, "actual", None) for e in segunda]


def test_trabajos_concurrentes_no_se_mezclan(tmp_path):
    def marcado(*, progreso, cancel, etiqueta):
        for i in (1, 2):
            progreso(Progreso(fase=etiqueta, actual=i, total=2, mensaje=etiqueta))
        return _resultado()

    with Trabajos(tmp_path, max_hilos=2) as trabajos:
        a = trabajos.enviar(marcado, etiqueta="a")
        b = trabajos.enviar(marcado, etiqueta="b")
        trabajos.esperar(a, TIEMPO)
        trabajos.esperar(b, TIEMPO)
        fases_a = {e.fase for e in trabajos.eventos(a, timeout=TIEMPO) if isinstance(e, Progreso)}
        fases_b = {e.fase for e in trabajos.eventos(b, timeout=TIEMPO) if isinstance(e, Progreso)}
    assert fases_a == {"a"}
    assert fases_b == {"b"}
    assert {p.name for p in tmp_path.iterdir()} == {f"{a}.jsonl", f"{b}.jsonl"}


def test_estado_id_desconocido(tmp_path):
    with Trabajos(tmp_path) as trabajos, pytest.raises(KeyError):
        trabajos.estado("inexistente")
