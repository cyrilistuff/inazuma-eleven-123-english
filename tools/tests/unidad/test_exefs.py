"""Pruebas de ie123kit.nucleo.contenedores.exefs (EXPERIMENTAL) con ficheros sintéticos."""
import hashlib

from ie123kit.nucleo.contenedores import exefs

# sha256 de la salida de build_exefs del tools/patch_exefs.py original (commit 0af2abd, hoy en
# tools/_archivo) con patch_code.patch_code_bin sustituido por la identidad y estos mismos ficheros.
SHA_ORIGINAL = "68b96ab94308a8f7b3ab07df2d3420ca0a095bc6499d73e7d5f6d5295b4f0765"
TAMANOS = {"code.bin": 0x345, "banner.bnr": 0x200, "icon.icn": 0x36C0, "logo.darc.lz": 0x21}


def _contenidos():
    return [(n, bytes((i * 7 + len(f)) & 0xFF for i in range(TAMANOS[f]))) for n, f in exefs.ARCHIVOS]


def test_equivalente_al_original():
    assert hashlib.sha256(exefs.construir(_contenidos())).hexdigest() == SHA_ORIGINAL


def test_construir_leer_y_hashes():
    contenidos = _contenidos()
    datos = exefs.construir(contenidos)
    entradas = exefs.leer(datos)
    assert [n for n, _, _ in entradas] == [n for n, _ in contenidos]
    for (_n, off, size), (_, c) in zip(entradas, contenidos):
        assert off % 0x200 == 0 and size == len(c)
        assert datos[0x200 + off:0x200 + off + size] == c
    assert len(datos) % 0x200 == 0
    assert exefs.comprobar_hashes(datos)
    roto = bytearray(datos)
    roto[0x200] ^= 1
    assert not exefs.comprobar_hashes(bytes(roto))
