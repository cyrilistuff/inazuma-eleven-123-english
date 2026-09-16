"""`JuegoBase`: lectura de activos.toml, perfil de texto y despacho por tipo de activo."""

from __future__ import annotations

from pathlib import Path

from ie123kit.nucleo.juego import CAPACIDADES, Aportacion, JuegoBase, PerfilTexto
from ie123kit.nucleo.tipos import AssetRef, componer_id

RUTA = "inazuma1/data_iz/a_title/title_t.arc"


class JuegoDePrueba(JuegoBase):
    """Objetivo mínimo sobre un paquete real ya existente."""

    PAQUETE = "ie123kit.ie1"


def _ref(tipo: str) -> AssetRef:
    return AssetRef(id=componer_id("ie1", tipo, RUTA), objetivo="ie1", tipo=tipo, ruta_romfs=RUTA)


def test_info_desde_activos_toml() -> None:
    info = JuegoDePrueba().info()
    assert info.id == "ie1"
    assert info.nombre == "Inazuma Eleven"
    assert info.prefijos_romfs == ("inazuma1/",)
    assert info.cros == ("cro/ina_main1.cro",)
    assert all(c in CAPACIDADES for c in info.capacidades)
    datos = info.to_json()
    assert datos["capacidades"] == sorted(datos["capacidades"])


def test_info_cacheada() -> None:
    juego = JuegoDePrueba()
    assert juego.info() is juego.info()


def test_perfil_texto_bloqueado() -> None:
    perfil = JuegoDePrueba().perfil_texto()
    assert isinstance(perfil, PerfilTexto)
    assert perfil.nombre == "tipografia_v20"
    assert perfil.bloqueado is True


def test_sin_capacidad_devuelve_not_supported(tmp_path: Path) -> None:
    juego = JuegoDePrueba()
    ref = _ref("grafico")
    assert "graficos" not in juego.info().capacidades  # IE1 aún no declara capacidades (F2.3)

    exportado = juego.exportar(None, ref, tmp_path / "salida.png")
    importado = juego.importar(None, ref, tmp_path / "entrada.png", simular=True)
    for res in (exportado, importado):
        assert res.ok is False
        assert [i.codigo for i in res.incidencias] == ["NOT_SUPPORTED"]
        assert res.incidencias[0].activo_id == ref.id


def test_tipo_desconocido_tambien_es_not_supported(tmp_path: Path) -> None:
    res = JuegoDePrueba().exportar(None, _ref("inventado"), tmp_path / "x")
    assert not res.ok and res.incidencias[0].codigo == "NOT_SUPPORTED"


def test_defectos_vacios() -> None:
    juego = JuegoDePrueba()
    assert juego.activos(None) == []
    assert juego.reglas_validacion() == []
    aportacion = juego.aportaciones(None, [])
    assert isinstance(aportacion, Aportacion)
    assert aportacion.entradas_fa == {} and aportacion.eventos == {}
    assert aportacion.literales_cro == {} and aportacion.romfs_sueltos == {}


def test_aportaciones_no_comparten_diccionarios() -> None:
    a, b = Aportacion(), Aportacion()
    a.entradas_fa["x"] = b"1"
    assert b.entradas_fa == {}
