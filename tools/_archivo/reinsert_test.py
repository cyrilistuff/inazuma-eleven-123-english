#!/usr/bin/env python3
"""[Etapa 7 - PoC] Valida el ciclo de reinsercion a nivel de datos (sin emulador).

Ciclo: localizar eve.pkb dentro de archive.fa -> descomprimir un evento (LZ10) ->
sustituir una cadena de dialogo por uno de prueba del MISMO nº de bytes (relleno)
-> recomprimir LZ10 -> rellenar hasta el tamaño original de la entrada (el
descompresor ignora el padding) -> sobrescribir en archive.fa IN-PLACE (mismo
tamaño total) -> re-extraer y comprobar que el cambio aparece.

Mismo tamaño en cada capa => NO hay que reconstruir contenedores ni arreglar
offsets. Aqui se usa una cadena de prueba ASCII; el pipeline real (texto ES con
codigos de control + fuente) se construye encima de esto.
"""
import struct
import sys

sys.path.insert(0, "tools")
from fa_unpack import FaArchive
from lz10 import compress, decompress
from pkb_unpack import parse_index


def find_file(arc, suffix):
    for path, off, size in arc.entries:
        if path.endswith(suffix):
            return path, off, size
    raise SystemExit("no encontrado: " + suffix)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    fa_path = r"work\archive_patched.fa"
    src = r"work\shared\base_3ds\romfs\archive.fa"
    data = bytearray(open(src, "rb").read())
    arc = FaArchive(src)

    pkb_path, pkb_off, pkb_size = find_file(arc, "inazuma1/data_iz/script/eve.pkb")
    pkh_path, pkh_off, pkh_size = find_file(arc, "inazuma1/data_iz/script/eve.pkh")
    pkb = data[pkb_off:pkb_off + pkb_size]
    pkh = bytes(data[pkh_off:pkh_off + pkh_size])
    ents = parse_index(pkh)
    print(f"eve.pkb @{pkb_off} size={pkb_size}; {len(ents)} eventos")

    # evento 0
    eid, eoff, esize = ents[0]
    raw = bytes(pkb[eoff:eoff + esize])
    dec = bytearray(decompress(raw))
    print(f"evento {eid}: comprimido={esize}B descomprimido={len(dec)}B")

    # localizar primer chunk de dialogo (NUL-split con kana) y su rango de bytes
    def is_lead(b): return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc
    chunks = []
    start = 0
    for i, b in enumerate(dec):
        if b == 0:
            chunks.append((start, i)); start = i + 1
    target = None
    for s, e in chunks:
        seg = dec[s:e]
        if sum(1 for k in range(len(seg) - 1) if is_lead(seg[k])) >= 3:
            target = (s, e); break
    if not target:
        raise SystemExit("no se hallo chunk de dialogo")
    s, e = target
    orig_chunk = bytes(dec[s:e])
    print(f"chunk objetivo @{s}..{e} ({e-s}B): {orig_chunk.decode('shift-jis','replace')[:40]!r}")

    # reemplazar por cadena de prueba ASCII del MISMO nº de bytes (relleno con espacios)
    test = b"[ES-TEST-OK]"
    repl = (test + b" " * (e - s))[:e - s]
    dec[s:e] = repl

    # recomprimir y validar tamaño
    new_raw = compress(bytes(dec))
    print(f"recomprimido={len(new_raw)}B vs hueco={esize}B -> {'CABE' if len(new_raw)<=esize else 'NO CABE'}")
    if len(new_raw) > esize:
        raise SystemExit("no cabe; necesitaria rebuild de offsets")
    new_raw = new_raw + b"\x00" * (esize - len(new_raw))   # padding ignorado al descomprimir

    # sobrescribir en archive.fa (in-place, mismo tamaño)
    data[pkb_off + eoff: pkb_off + eoff + esize] = new_raw
    open(fa_path, "wb").write(data)
    print(f"archive.fa parcheado -> {fa_path} (mismo tamaño={len(data)})")

    # VERIFICAR: re-extraer y descomprimir
    arc2 = FaArchive(fa_path)
    _, o2, s2 = find_file(arc2, "inazuma1/data_iz/script/eve.pkb")
    pkb2 = open(fa_path, "rb").read()[o2:o2 + s2]
    dec2 = decompress(pkb2[eoff:eoff + esize])
    ok = test in dec2
    print(f"VERIFICACION: cadena de prueba presente tras re-extraer = {ok}")
    print("=> CICLO DE REINSERCION (datos) " + ("FUNCIONA" if ok else "FALLA"))


if __name__ == "__main__":
    main()
