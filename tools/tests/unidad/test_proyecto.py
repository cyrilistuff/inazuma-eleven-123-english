"""Tests del Workspace y del manifiesto de candidata (F2.1 T2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ie123kit.nucleo.config.raiz import find_root
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.servicio.proyecto import ManifiestoCandidata, Workspace

IE123_TOML = """
[proyecto]
idioma = "es-ES"
nombres_europeos = true

[candidatas]
patron = "probe_ie1_v{n}"
conservar = 2
golden = ["probe_ie1_v66", "probe_ie1_v67"]

[objetivos]
habilitados = ["juego_principal", "ie1"]

[fuentes]
ttf_ui = "del_proyecto.ttf"

[golden]
manifiestos = "tools/tests/compat/golden"
"""


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "AGENTS.md").write_text("", encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "ie123.toml").write_text(IE123_TOML, encoding="utf-8")
    return tmp_path


def _ws(repo: Path, entorno: dict[str, str] | None = None) -> Workspace:
    return Workspace.abrir(repo, entorno=entorno or {})


def test_precedencia_local_sobre_proyecto(repo: Path) -> None:
    (repo / "ie123.local.toml").write_text('[fuentes]\nttf_ui = "de_local.ttf"\n', encoding="utf-8")
    assert _ws(repo).ajuste("fuentes.ttf_ui") == "de_local.ttf"
    assert _ws(repo).ajuste("proyecto.idioma") == "es-ES"
    assert _ws(repo).ajuste("no.existe", "defecto") == "defecto"


def test_precedencia_variables_por_encima_de_todo(repo: Path) -> None:
    (repo / "ie123.local.toml").write_text('[fuentes]\nttf_ui = "de_local.ttf"\n', encoding="utf-8")
    ws = _ws(repo, {"IE123_FUENTE_TTF": "del_entorno.ttf", "IE123_AZAHAR": "mods"})
    assert ws.ajuste("fuentes.ttf_ui") == "del_entorno.ttf"
    assert ws.ajuste("azahar.mods_dir") == "mods"


def test_dirs_objetivo_simple_versionado_y_comun(repo: Path) -> None:
    ws = _ws(repo)
    d = ws.dirs("ie1")
    assert d.raiz == repo / "work" / "ie1"
    assert d.capas == d.raiz / "capas"
    assert d.qa == d.raiz / "qa"
    assert d.exportaciones == d.raiz / "exportaciones"
    assert d.registro == d.raiz / "registro.json"
    assert not d.capas.exists()
    assert ws.dirs("juego_principal").raiz == repo / "work" / "juego_principal"
    assert ws.dirs("ie2.tormenta_de_fuego").raiz == repo / "work" / "ie2" / "tormenta_de_fuego"
    assert ws.dirs("ie3.rayo_celeste").raiz == repo / "work" / "ie3" / "rayo_celeste"
    assert ws.dirs("ie2.comun").raiz == repo / "work" / "ie2" / "shared"
    assert ws.dirs("ie3.comun").raiz == repo / "work" / "ie3" / "shared"


def test_objetivo_desconocido(repo: Path) -> None:
    with pytest.raises(ValidacionError) as exc:
        _ws(repo).dirs("ie4.lo_que_sea")
    assert exc.value.codigo == "OBJETIVO_DESCONOCIDO"


def test_preparar_es_idempotente(repo: Path) -> None:
    ws = _ws(repo)
    for _ in range(2):
        d = ws.preparar("ie1")
        assert d.capas.is_dir() and d.qa.is_dir() and d.exportaciones.is_dir()


def test_objetivos_habilitados(repo: Path) -> None:
    assert _ws(repo).objetivos_habilitados() == ("juego_principal", "ie1")


def test_candidatas_ordenadas_numericamente(repo: Path) -> None:
    ws = _ws(repo)
    assert ws.nombre_candidata(68) == "probe_ie1_v68"
    assert ws.candidata("probe_ie1_v68") == repo / "work" / "shared" / "candidatas" / "probe_ie1_v68"
    assert ws.listar_candidatas() == []
    for nombre in ("probe_ie1_v67", "probe_ie1_v9", "probe_ie1_v70", "ruido"):
        (ws.candidatas / nombre).mkdir(parents=True)
    assert ws.listar_candidatas() == ["probe_ie1_v9", "probe_ie1_v67", "probe_ie1_v70"]
    assert ws.golden() == ("probe_ie1_v66", "probe_ie1_v67")
    assert ws.dir_manifiestos_golden() == repo / "tools/tests/compat/golden"


def test_manifiesto_ida_y_vuelta(repo: Path) -> None:
    destino = repo / "work" / "shared" / "candidatas" / "probe_ie1_v68"
    m = ManifiestoCandidata(
        nombre="probe_ie1_v68",
        base="probe_ie1_v67",
        base_sha256="a" * 64,
        capas=({"ruta": "capas/dialogo.tsv", "sha256": "b" * 64},),
        salidas={"romfs/data.fa": "c" * 64},
        objetivos=("ie1",),
    )
    ruta = m.escribir(destino)
    assert ruta == destino / "manifest.json"
    d = json.loads(ruta.read_text(encoding="utf-8"))
    assert d["esquema"] == 1
    assert d["runtime_verified"] is False
    assert d["generado_en"]
    leido = ManifiestoCandidata.leer(destino)
    assert leido.nombre == m.nombre
    assert leido.capas == m.capas
    assert leido.salidas == m.salidas
    assert leido.objetivos == ("ie1",)
    assert ManifiestoCandidata.leer(ruta).to_json()["runtime_verified"] is False


def test_doctor_serializable(repo: Path) -> None:
    (repo / "ie123.local.toml").write_text(
        '[herramientas]\nctrtool = "ctrtool_que_no_existe_ie123"\n', encoding="utf-8"
    )
    res = _ws(repo).doctor()
    assert res.ok
    assert any(i.codigo == "HERRAMIENTA_AUSENTE" for i in res.incidencias)
    json.dumps(res.datos)


def test_ie123_toml_real_del_repo() -> None:
    raiz = find_root()
    ws = Workspace.abrir(raiz, entorno={})
    for seccion in ("proyecto", "candidatas", "objetivos", "golden"):
        assert seccion in ws.proyecto, f"falta [{seccion}] en ie123.toml"
    assert ws.dir_manifiestos_golden().is_dir()
    assert "ie1" in ws.objetivos_habilitados()
