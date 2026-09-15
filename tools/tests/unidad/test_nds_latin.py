"""nucleo.texto.nds_latin: dos tablas NDS distintas y decodificadores (valores capturados de 0af2abd)."""
from ie123kit.nucleo.texto import nds_latin as N


def test_tablas_distintas_y_diferencia_exacta():
    assert N.NDS_DEC is not N.DS_TABLE
    assert all(N.NDS_DEC.get(k) == v for k, v in N.DS_TABLE.items())
    assert {k: v for k, v in N.NDS_DEC.items() if k not in N.DS_TABLE} == {0xB5: "ä"}
    assert N.DS_TABLE[0xD9] == "É" and N.DS_TABLE[0xA6] == "Í"


def test_dec_es_frente_a_decode_ds():
    b = b"Hola\xb5 \x0a n.\x7e2 \x81\x67x\x81\x68 \xd9psilon \xff\x00resto"
    assert N.dec_es(b) == 'Holaä n.º2 "x" Épsilon ?'
    assert N.decode_ds(b"\xb5\x0a\x7e\xd9\xa6\xff") == "?\n~ÉÍ?"
    faltan = {}
    N.decode_ds(b"\xb5\xb5\xff", faltan)
    assert faltan == {0xB5: 2, 0xFF: 1}


def test_dec_jp():
    assert N.dec_jp("  テスト ".encode("shift_jis") + b"\x00zz") == "テスト"


def test_decode_cadena():
    assert N.decode_cadena("\x01テ\x02スト\n %s ".encode("shift_jis"), "sjis") == "テスト\n %s"
    assert N.decode_cadena(b"\x01Hola\x0a\xb2\xd9  x\xff\x7e", "nds") == "Hola áÉ x~"
