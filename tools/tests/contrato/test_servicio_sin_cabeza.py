"""Ciclo completo de ServicioToolkit sin cabeza sobre el proyecto sintético (sin ROM, sin red)."""

from __future__ import annotations

import json
from pathlib import Path

from ie123kit.nucleo import util
from ie123kit.nucleo.tipos import Resultado
from ie123kit.servicio import esquemas
from ie123kit.servicio.api import ServicioToolkit, SolicitudConstruccion
from ie123kit.servicio.trabajos import Trabajos

OBJETIVO = "falso"


def _ok_serializable(res: Resultado) -> dict:
    assert isinstance(res, Resultado)
    datos = res.to_json()
    json.dumps(datos, ensure_ascii=False)
    assert esquemas.validar(datos, "resultado") == []
    return datos


def test_ciclo_completo(servicio: ServicioToolkit, proyecto_sintetico, tmp_path: Path) -> None:
    res_obj = servicio.objetivos()
    _ok_serializable(res_obj)
    assert res_obj.ok
    ids = [o["id"] for o in res_obj.datos["objetivos"]]
    assert OBJETIVO in ids

    res_act = servicio.activos(OBJETIVO)
    _ok_serializable(res_act)
    assert res_act.ok and res_act.datos["activos"]
    activo = res_act.datos["activos"][0]

    destino = tmp_path / "exportado"
    res_exp = servicio.exportar(OBJETIVO, [activo["id"]], destino)
    _ok_serializable(res_exp)
    assert res_exp.ok and res_exp.artefactos
    exportado = Path(res_exp.artefactos[0])
    assert exportado.is_file()

    antes = util.sha256_arbol(proyecto_sintetico.raiz)
    res_sim = servicio.importar(OBJETIVO, activo["id"], exportado, simular=True)
    _ok_serializable(res_sim)
    assert res_sim.ok and res_sim.datos["simulado"] is True
    assert util.sha256_arbol(proyecto_sintetico.raiz) == antes

    res_imp = servicio.importar(OBJETIVO, activo["id"], exportado, simular=False)
    _ok_serializable(res_imp)
    assert res_imp.ok and res_imp.artefactos
    assert Path(res_imp.artefactos[0]).is_file()
    assert util.sha256_arbol(proyecto_sintetico.raiz) != antes


def test_operaciones_aplazadas_no_soportadas(servicio: ServicioToolkit, tmp_path: Path) -> None:
    solicitud = SolicitudConstruccion(base="probe_ie1_v67", objetivos=("ie1",), capas=(), salida="probe_ie1_v68")
    resultados = {
        "construir": servicio.construir(solicitud),
        "verificar": servicio.verificar("probe_ie1_v67"),
        "instalar": servicio.instalar("probe_ie1_v67"),
        "parche": servicio.parche(tmp_path / "a.3ds", tmp_path / "b.3ds", tmp_path / "c.xdelta"),
    }
    for nombre, res in resultados.items():
        _ok_serializable(res)
        assert not res.ok, nombre
        assert [i.codigo for i in res.incidencias] == ["NOT_SUPPORTED"], nombre


def _base_lista(proyecto_sintetico) -> SolicitudConstruccion:
    """Crea la candidata base en el proyecto sintético y devuelve la solicitud de construcción."""
    from fa_sintetico import escribir_fa
    from juego_falso import FICHEROS

    base = Path(proyecto_sintetico.candidata("probe_ie1_v67"))
    base.mkdir(parents=True, exist_ok=True)
    escribir_fa(base / "archive.fa", FICHEROS)
    return SolicitudConstruccion(base="probe_ie1_v67", objetivos=(OBJETIVO,), capas=(), salida="probe_ie1_v68")


def test_construir_no_enmascara_un_typeerror_del_constructor(servicio, proyecto_sintetico, monkeypatch) -> None:
    """Un TypeError INTERNO del constructor es un fallo, nunca un reintento sin aportaciones.

    Regresión de F2.2: el `except TypeError` que reintentaba con la firma corta convertía
    cualquier fallo del constructor (una aportación mal formada, un reempaquetado roto) en una
    candidata construida sin aportaciones y devuelta como `ok`.
    """
    from ie123kit.nucleo.construir import candidata as constructor

    solicitud = _base_lista(proyecto_sintetico)
    llamadas: list[dict] = []

    def explota(base, salida, **kw):
        llamadas.append(kw)
        raise TypeError("aportación no válida (se esperaba un dict): 'x'")

    monkeypatch.setattr(constructor, "construir", explota)
    res = servicio.construir(solicitud)
    _ok_serializable(res)
    assert not res.ok
    assert len(llamadas) == 1, "se ha reintentado en silencio"
    assert "aportación no válida" in res.incidencias[0].mensaje
    assert not Path(proyecto_sintetico.candidata("probe_ie1_v68")).exists()


def test_construir_avisa_si_el_nucleo_tiene_la_firma_vieja(servicio, proyecto_sintetico, monkeypatch) -> None:
    """Si el constructor no admite `aportaciones`, se dice; no se construye a medias."""
    from ie123kit.nucleo.construir import candidata as constructor

    solicitud = _base_lista(proyecto_sintetico)
    llamadas: list[str] = []

    def firma_vieja(base, salida, *, ui=None, capas=None, cro=None):
        llamadas.append("llamado")
        return {}

    monkeypatch.setattr(constructor, "construir", firma_vieja)
    res = servicio.construir(solicitud)
    _ok_serializable(res)
    assert not res.ok and llamadas == []
    assert "aportaciones" in res.incidencias[0].mensaje


def test_doctor_serializable(servicio: ServicioToolkit) -> None:
    res = servicio.doctor()
    datos = _ok_serializable(res)
    assert datos["datos"]["api_version"] == servicio.API_VERSION


def test_objetivo_desconocido_da_fallo_controlado(servicio: ServicioToolkit, tmp_path: Path) -> None:
    res = servicio.activos("no_existe")
    _ok_serializable(res)
    assert not res.ok
    mensaje = res.incidencias[0].mensaje
    assert "no_existe" in mensaje and OBJETIVO in mensaje


def test_enviar_trabajo_escribe_eventos_jsonl(proyecto_sintetico, juego_falso, tmp_path: Path) -> None:
    from ie123kit.servicio.api import descubrir_juegos

    dir_eventos = tmp_path / "trabajos"
    with Trabajos(dir_eventos=dir_eventos, max_hilos=1) as trabajos:
        servicio = ServicioToolkit(
            proyecto_sintetico,
            juegos=descubrir_juegos(extra={OBJETIVO: juego_falso}),
            trabajos=trabajos,
        )
        activo = servicio.activos(OBJETIVO).datos["activos"][0]
        res = servicio.enviar_trabajo("exportar", objetivo=OBJETIVO, ids=[activo["id"]],
                                      destino=tmp_path / "trabajo_salida")
        _ok_serializable(res)
        assert res.ok
        id_trabajo = res.datos["trabajo"]
        trabajo = trabajos.esperar(id_trabajo, timeout=30)
        assert str(trabajo.estado) == "hecho", trabajo.to_json()

    fichero = dir_eventos / f"{id_trabajo}.jsonl"
    assert fichero.is_file()
    lineas = [json.loads(linea) for linea in fichero.read_text(encoding="utf-8").splitlines() if linea.strip()]
    assert lineas
    for linea in lineas:
        assert esquemas.validar(linea, "evento_trabajo") == [], linea
