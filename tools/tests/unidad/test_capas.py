"""Entorno de capa: Capa(__file__) y ejecutar(main)."""
from pathlib import Path

import pytest

from ie123kit.nucleo.construir.capas import Capa, ejecutar


def _capa_falsa(tmp_path: Path, *, con_toml: bool = True) -> Path:
    aqui = tmp_path / "work" / "ie1" / "capas" / "v70" / "pachangas"
    aqui.mkdir(parents=True)
    if con_toml:
        (aqui / "capa.toml").write_text(
            'version = "v70"\nobjetivo = "ie1"\nlinea = "pachangas"\n'
            'base = "probe_ie1_v67"\ndescripcion = "Rótulos de las pachangas"\n',
            encoding="utf-8",
        )
    (aqui / "apply.py").write_text("# capa de prueba\n", encoding="utf-8")
    return aqui


def test_rutas_y_metadatos(tmp_path):
    aqui = _capa_falsa(tmp_path)
    capa = Capa(aqui / "apply.py", raiz=tmp_path)
    assert capa.aqui == aqui
    assert capa.raiz == tmp_path.resolve()
    assert (capa.version, capa.objetivo, capa.linea) == ("v70", "ie1", "pachangas")
    assert capa.meta["base"] == "probe_ie1_v67"

    destino = capa.extra("inazuma1/data_iz/ui.bin")
    assert destino == aqui / "extra" / "inazuma1" / "data_iz" / "ui.bin"
    assert destino.parent.is_dir()
    assert capa.eventos("eve") == aqui / "events"
    assert capa.eventos("mch").is_dir()
    assert capa.romfs("cro/ina_main1.cro").parent.is_dir()
    assert capa.informe("resumen.json").parent.is_dir()
    with pytest.raises(ValueError):
        capa.eventos("otro")


def test_metadatos_deducidos_sin_toml(tmp_path):
    aqui = _capa_falsa(tmp_path, con_toml=False)
    capa = Capa(aqui / "apply.py", raiz=tmp_path)
    assert (capa.version, capa.objetivo, capa.linea) == ("v70", "ie1", "pachangas")


def test_aportacion(tmp_path):
    aqui = _capa_falsa(tmp_path)
    capa = Capa(aqui / "apply.py", raiz=tmp_path)
    capa.extra("")
    capa.romfs("cro/ina_main2.cro").write_bytes(b"cro")
    capa.eventos("mch")
    aportacion = capa.aportacion()
    assert aportacion["objetivo"] == "ie1"
    assert aportacion["cro"] == [aqui / "romfs" / "cro" / "ina_main2.cro"]
    assert "mch" in aportacion["eventos"]


def test_ejecutar_exito_y_fallo(capsys):
    assert ejecutar(lambda: None) == 0

    def falla():
        raise ValueError("falta la entrada b/dos.bin")

    assert ejecutar(falla) == 1
    salida = capsys.readouterr()
    assert salida.err.count("\n") == 1
    assert "falta la entrada b/dos.bin" in salida.err

    def revienta():
        raise KeyError("otro fallo")

    with pytest.raises(KeyError):
        ejecutar(revienta)
