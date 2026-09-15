"""activos.toml por objetivo (F1.4, #45): esquema 1, declarativo y sin ROM."""

import re
import tomllib
from importlib import resources

import pytest

OBJETIVOS = {
    "juego_principal": "ie123kit.juego_principal",
    "ie1": "ie123kit.ie1",
    "ie2.tormenta_de_fuego": "ie123kit.ie2.tormenta_de_fuego",
    "ie2.ventisca_eterna": "ie123kit.ie2.ventisca_eterna",
    "ie3.rayo_celeste": "ie123kit.ie3.rayo_celeste",
    "ie3.fuego_explosivo": "ie123kit.ie3.fuego_explosivo",
    "ie3.amenaza_del_ogro": "ie123kit.ie3.amenaza_del_ogro",
}
CROS_VALIDAS = {"cro/ina_menu.cro", "cro/ina_main1.cro", "cro/ina_main2.cro", "cro/ina_main3ogre.cro"}
UNIDAD = re.compile(r"^[A-Za-z]:")


def _leer(paquete: str) -> dict:
    recurso = resources.files(paquete).joinpath("activos.toml")
    assert recurso.is_file(), f"{paquete}: falta activos.toml"
    return tomllib.loads(recurso.read_text(encoding="utf-8"))


def _cadenas(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _cadenas(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from _cadenas(v)


@pytest.mark.parametrize("objetivo", list(OBJETIVOS))
def test_activos_basicos(objetivo):
    datos = _leer(OBJETIVOS[objetivo])
    assert datos["esquema"] == 1
    obj = datos["objetivo"]
    assert obj["id"] == objetivo
    assert OBJETIVOS[objetivo] == "ie123kit." + obj["id"]
    assert obj["perfil_texto"] == "tipografia_v20"
    assert isinstance(obj["capacidades"], list)
    if objetivo.startswith(("ie2.", "ie3.")):
        assert obj["capacidades"] == []
    romfs = datos["romfs"]
    for prefijo in romfs["prefijos_fa"] + romfs.get("solo_lectura", []):
        assert prefijo.endswith("/") and not prefijo.startswith("/"), prefijo
    assert set(romfs["cros"]) <= CROS_VALIDAS
    for cadena in _cadenas(datos):
        assert ".." not in cadena, cadena
        assert not cadena.startswith(("/", "\\")), cadena
        assert not UNIDAD.match(cadena), cadena


def test_union_de_prefijos():
    union = set()
    for paquete in OBJETIVOS.values():
        union |= set(_leer(paquete)["romfs"]["prefijos_fa"])
    esperados = {
        "inazuma1/",
        "inazuma2/",
        "inazuma3/",
        "inazuma3_ogre/",
        "menu/",
        "movie/",
        "message/",
        "patchscript/",
    }
    assert esperados <= union, esperados - union
