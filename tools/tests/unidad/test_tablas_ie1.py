"""ie1.texto.tablas: bytes esperados capturados de tools/ie1_tables.py en 0af2abd."""
import pytest

from ie123kit.ie1.texto import tablas as T
from ie123kit.nucleo.registros import tabla_fija


def test_write_field():
    d = bytearray(b"\xff" * 20)
    T.write_field(d, 2, 10, "Ab")
    assert d.hex() == "ffff82608282000000000000ffffffffffffffff"
    with pytest.raises(ValueError, match="^name exceeds field including terminator: Mark$"):
        T.write_field(bytearray(8), 0, 4, "Mark")


def test_escribir_campo_no_trunca():
    with pytest.raises(ValueError):
        tabla_fija.escribir_campo(bytearray(4), 0, 4, b"abcd", "abcd")
    d = bytearray(4)
    tabla_fija.escribir_campo(d, 0, 4, b"abc", "abc")
    assert d == b"abc\0"


def test_patch_string_pool():
    fuente = "名前".encode("shift_jis") + bytes(28) + "他".encode("shift_jis") + bytes(30)
    r, c = T.patch_string_pool(fuente, {"名前": "Evans"})
    assert r.hex() == ("826482968281828e82930000000000000000000000000000000000000000000091bc"
                       "000000000000000000000000000000000000000000000000000000000000")
    assert c == [0]
    with pytest.raises(ValueError, match="not a padded 32-byte string slot"):
        T.patch_string_pool(b"\x00" + "名前".encode("shift_jis") + bytes(29), {"名前": "x"})


def _tabla():
    t = bytearray(64)
    t[0:4] = "剣".encode("shift_jis") + b"\0\0"
    t[20:24] = b"\x01\x02\x03\x04"
    t[32:36] = "盾".encode("shift_jis") + b"\0\0"
    return bytes(t)


def test_patch_items():
    rt, rp = T.patch_items(_tabla(), b"abc", {"1": {"source": "盾", "name": "Escudo", "description": "Protege"},
                                              0: {"source": "剣", "name": "Espada"}})
    assert rt.hex() == ("826482938290828182848281000000000000000001020304000000000000000082648293"
                        "828382958284828f0000000000000000000000000000000000000100")
    assert rp.hex() == ("6162630000000000000000000000000000000000000000000000000000000000826f8292"
                        "828f8294828582878285000000000000000000000000000000000000")


@pytest.mark.parametrize("tabla,rep,msg", [
    (_tabla(), {"2": {"source": "x", "name": "y"}}, "item index out of range"),
    (_tabla(), {"0": {"source": "no", "name": "y"}}, "item source mismatch"),
    (bytes(33), {}, "invalid item table size"),
    (_tabla(), {"0": {"source": "剣", "name": "Espada de fuego"}}, "name exceeds field"),
])
def test_patch_items_errores(tabla, rep, msg):
    with pytest.raises(ValueError, match=msg):
        T.patch_items(tabla, b"", rep)
