"""nucleo.eventos.instrucciones: EventPack sobre un paquete eve/mch sintético.

Norma 2: ni un byte procede de la ROM. El contenedor lo escribe el helper sintético
de la suite de contrato (solo lectura) y los SSD se construyen aquí.
"""

import importlib.util
import struct
import sys
from pathlib import Path

import pytest

from ie123kit.nucleo.compresion import lz10
from ie123kit.nucleo.contenedores.fa import FaArchive
from ie123kit.nucleo.errores import ValidacionError
from ie123kit.nucleo.eventos import ssd
from ie123kit.nucleo.eventos.instrucciones import DIR_SCRIPT, LIMITE_TEXTO, EventPack, comparar, stage


def _escribir_fa(ruta, ficheros):
    modulo = "fa_sintetico_contrato"
    if modulo not in sys.modules:
        origen = Path(__file__).resolve().parent.parent.parent / "contrato" / "fa_sintetico.py"
        spec = importlib.util.spec_from_file_location(modulo, origen)
        cargado = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cargado)
        sys.modules[modulo] = cargado
    return sys.modules[modulo].escribir_fa(ruta, ficheros)


# ----------------------------- SSD sintético -----------------------------

def _instruccion(ident, opcode, indices):
    argc = len(indices)
    tipos = 4 * ((argc + 7) // 8)
    length = 8 + tipos + 4 * argc
    tabla = bytearray(tipos)
    for a in range(argc):
        tabla[a // 2] |= 3 << (4 * (a % 2))
    valores = b"".join(struct.pack("<I", i) for i in indices)
    return struct.pack("<HHHBB", ident, length, opcode, argc, 0) + bytes(tabla) + valores


def _texto(ident, argumento, cuerpo):
    length = (4 + len(cuerpo) + 1 + 3) & ~3
    return struct.pack("<HBB", ident, argumento, length) + cuerpo + bytes(length - 4 - len(cuerpo))


def _ssd(instrucciones, textos):
    codigo = b"".join(instrucciones)
    tabla = b"".join(textos)
    cabecera = struct.pack(
        "<4sIIHHIIII", b"SSD\0", 0x00030001, 32 + len(codigo) + len(tabla),
        len(instrucciones), len(textos), len(codigo), len(tabla), 0, 0,
    )
    return cabecera + codigo + tabla


DIALOGO, ROTULO = 0x301D, 0x4037


def _evento_a():
    instrucciones = [_instruccion(1, DIALOGO, [0]), _instruccion(2, ROTULO, [1, 1, 1])]
    textos = [_texto(1, 1, b"hola"), _texto(2, 3, b"rotulo")]
    return _ssd(instrucciones, textos)


def _evento_b():
    return _ssd([_instruccion(7, DIALOGO, [0])], [_texto(7, 1, b"segundo evento")])


def _pkh(entradas):
    cab = b"PackNum 20260101" + struct.pack("<I", 0x30 + 12 * len(entradas))
    return cab + bytes(0x30 - len(cab)) + b"".join(struct.pack("<III", *e) for e in entradas)


def _paquete_bytes(eventos):
    pkb, entradas = bytearray(), []
    for eid, datos in eventos:
        bloque = lz10.compress(datos)
        entradas.append((eid, len(pkb), len(bloque)))
        pkb += bloque
        pkb += bytes((-len(pkb)) % 4)
    return _pkh(entradas), bytes(pkb)


EVENTOS = [(10010001, _evento_a()), (10010002, _evento_b())]


@pytest.fixture
def paquete_dir(tmp_path):
    pkh, pkb = _paquete_bytes(EVENTOS)
    base = tmp_path / "volcado"
    (base / DIR_SCRIPT).mkdir(parents=True)
    (base / DIR_SCRIPT / "eve.pkh").write_bytes(pkh)
    (base / DIR_SCRIPT / "eve.pkb").write_bytes(pkb)
    return base


def test_ssd_sintetico_valido():
    assert ssd.parse(_evento_a())[2][0].body == b"hola"


def test_from_dir_y_events(paquete_dir):
    pack = EventPack.from_dir(paquete_dir, "eve")
    assert pack.events() == dict(EVENTOS)


def test_from_archive(tmp_path):
    pkh, pkb = _paquete_bytes(EVENTOS)
    ruta = _escribir_fa(tmp_path / "archive.fa", {
        f"{DIR_SCRIPT}/mch.pkh": pkh,
        f"{DIR_SCRIPT}/mch.pkb": pkb,
    })
    pack = EventPack.from_archive(FaArchive(str(ruta)), "mch")
    assert pack.pack == "mch"
    assert pack.events() == dict(EVENTOS)


def test_pack_desconocido_y_ausente(tmp_path, paquete_dir):
    with pytest.raises(ValidacionError) as exc:
        EventPack.from_dir(paquete_dir, "xxx")
    assert exc.value.codigo == "evento_pack_desconocido"
    with pytest.raises(ValidacionError) as exc:
        EventPack.from_dir(paquete_dir, "mch")
    assert exc.value.codigo == "evento_pack_ausente"


def test_instructions_y_find(paquete_dir):
    pack = EventPack.from_dir(paquete_dir, "eve")
    tabla = pack.instructions(10010001)
    assert tabla[1][0] == DIALOGO
    assert tabla[2] == (ROTULO, [(3, 1), (3, 1), (3, 1)])
    assert [i for i, _ in pack.find(10010001)] == [0, 1]
    assert [r.body for _, r in pack.find(10010001, opcode=DIALOGO)] == [b"hola"]
    assert [i for i, _ in pack.find(10010001, opcode=ROTULO, argumento=3)] == [1]
    assert pack.find(10010001, opcode=ROTULO, argumento=1) == []
    with pytest.raises(ValidacionError):
        pack.instructions(99999999)


def test_stage_escribe_y_cuenta(paquete_dir, tmp_path):
    pack = EventPack.from_dir(paquete_dir, "eve")
    salida = tmp_path / "events"
    informe = stage(pack, {10010001: {0: b"adios", 1: b"rotulo"}}, salida)
    assert [e["evento"] for e in informe["eventos"]] == [10010001]
    assert informe["eventos"][0]["registros_cambiados"] == 1  # el segundo no cambia
    nuevo = (salida / "10010001.ssd").read_bytes()
    assert [r.body for r in ssd.parse(nuevo)[2]] == [b"adios", b"rotulo"]
    assert comparar(dict(EVENTOS)[10010001], nuevo) == 1


def test_stage_evento_desconocido(paquete_dir, tmp_path):
    pack = EventPack.from_dir(paquete_dir, "eve")
    with pytest.raises(ValidacionError) as exc:
        pack.stage({42: {0: b"x"}}, tmp_path / "events")
    assert exc.value.codigo == "evento_desconocido"


def test_stage_texto_demasiado_largo(paquete_dir, tmp_path):
    pack = EventPack.from_dir(paquete_dir, "eve")
    with pytest.raises(ValidacionError) as exc:
        pack.stage({10010001: {0: b"a" * (LIMITE_TEXTO + 1)}}, tmp_path / "events")
    assert exc.value.codigo == "ssd_texto_demasiado_largo"
    informe = pack.stage({10010001: {0: b"a" * LIMITE_TEXTO}}, tmp_path / "limite")
    assert informe["eventos"][0]["registros_cambiados"] == 1


def test_comparar_rechaza_tabla_de_instrucciones():
    otra = _ssd([_instruccion(1, DIALOGO + 1, [0]), _instruccion(2, ROTULO, [1, 1, 1])],
                [_texto(1, 1, b"hola"), _texto(2, 3, b"rotulo")])
    with pytest.raises(ValidacionError) as exc:
        comparar(_evento_a(), otra, 10010001)
    assert exc.value.codigo == "ssd_tabla_instrucciones_cambiada"


def test_comparar_rechaza_numero_de_registros():
    menos = _ssd([_instruccion(1, DIALOGO, [0]), _instruccion(2, ROTULO, [0, 0, 0])], [_texto(1, 1, b"hola")])
    with pytest.raises(ValidacionError) as exc:
        comparar(_evento_a(), menos, 10010001)
    assert exc.value.codigo in ("ssd_numero_de_registros", "ssd_tabla_instrucciones_cambiada")
    igual_tabla = _ssd([_instruccion(1, DIALOGO, [0]), _instruccion(2, ROTULO, [1, 1, 1])],
                       [_texto(1, 1, b"hola"), _texto(2, 3, b"rotulo"), _texto(2, 3, b"extra")])
    with pytest.raises(ValidacionError) as exc:
        comparar(_evento_a(), igual_tabla, 10010001)
    assert exc.value.codigo == "ssd_numero_de_registros"


def test_comparar_rechaza_identidad_de_registro():
    otra = _ssd([_instruccion(1, DIALOGO, [0]), _instruccion(2, ROTULO, [1, 1, 1])],
                [_texto(1, 1, b"hola"), _texto(2, 2, b"rotulo")])
    with pytest.raises(ValidacionError) as exc:
        comparar(_evento_a(), otra, 10010001)
    assert exc.value.codigo == "ssd_identidad_de_registro"


def test_comparar_sin_cambios():
    assert comparar(_evento_a(), _evento_a()) == 0
