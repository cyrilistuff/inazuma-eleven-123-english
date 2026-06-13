#!/usr/bin/env python3
"""[Etapa 7] Re-encoder real: aplica el espanol (sin acentos) a archive.fa.

Estrategia bulletproof (no depende de la semantica exacta del formato de chunk):
- Cada cadena de dialogo es un chunk delimitado por NUL: [tipo][b2][texto...].
- Se conservan los 2 bytes de prefijo y se sustituye el texto por el ES romanizado
  (ASCII/Shift-JIS), manteniendo el MISMO nº de bytes del chunk (relleno con
  espacios / recorte). => tamano descomprimido del evento INVARIANTE => todo offset
  y longitud interna sigue valido. Se re-LZ10 y se rellena al tamano original de la
  entrada (padding ignorado). archive.fa queda del MISMO tamano -> parche in-place.

Acentos: de momento se romanizan (a/e/i/o/u/n, ! ?). La fuente (etapa 6) los
restaura luego. Solo se aplican lineas con es_final (estado != pendiente).

Uso:
    python tools/reinsert.py            # patчea work/romfs/archive.fa -> work/archive_es.fa
"""
import csv
import os
import struct
import sys

sys.path.insert(0, "tools")
from fa_unpack import FaArchive
from lz10 import compress, decompress
from pkb_unpack import parse_index, _decode_string

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ACC = str.maketrans({"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u",
                     "ñ": "n", "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
                     "Ü": "U", "Ñ": "N", "¡": "!", "¿": "?", "ª": "a", "º": "o",
                     "“": '"', "”": '"', "—": "-", "…": "..."})


def romanize(s):
    s = s.translate(ACC)
    return s.encode("shift-jis", "replace")


def find_file(arc, suffix):
    for path, off, size in arc.entries:
        if path.endswith(suffix):
            return off, size
    raise SystemExit("no encontrado: " + suffix)


def load_translations():
    """{event_id: {japones_limpio: es_final}} para lineas con es_final."""
    out = {}
    path = os.path.join(REPO, "translation", "game1", "dialogo.csv")
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["estado"] == "pendiente" or not row["es_final"]:
            continue
        out.setdefault(int(row["event_id"]), {})[row["japones"]] = row["es_final"]
    return out


def reencode_event(dec, trans):
    """Sustituye en el evento descomprimido las cadenas traducidas. Tamano invariante."""
    parts = dec.split(b"\x00")
    n_applied = 0
    for i, part in enumerate(parts):
        if len(part) < 3 or part[0] not in (1, 2, 4):
            continue
        clean = _decode_string(part, "sjis")
        es = trans.get(clean)
        if not es:
            continue
        budget = len(part) - 2                      # bytes de texto disponibles
        body = romanize(es)[:budget]
        body = body + b" " * (budget - len(body))   # rellenar a tamano exacto
        parts[i] = bytes(part[:2]) + body
        n_applied += 1
    return b"\x00".join(parts), n_applied


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.join(REPO, "work", "romfs", "archive.fa")
    dst = os.path.join(REPO, "work", "archive_es.fa")
    data = bytearray(open(src, "rb").read())
    arc = FaArchive(src)
    pkb_off, pkb_size = find_file(arc, "inazuma1/data_iz/script/eve.pkb")
    pkh_off, pkh_size = find_file(arc, "inazuma1/data_iz/script/eve.pkh")
    pkb = bytearray(data[pkb_off:pkb_off + pkb_size])
    ents = parse_index(bytes(data[pkh_off:pkh_off + pkh_size]))
    trans = load_translations()
    print(f"eve.pkb {pkb_size}B, {len(ents)} eventos; traducciones en {len(trans)} eventos")

    ev_ok = ev_skip = lines = 0
    for eid, eoff, esize in ents:
        if eid not in trans:
            continue
        dec = decompress(bytes(pkb[eoff:eoff + esize]))
        new_dec, n = reencode_event(dec, trans[eid])
        if n == 0:
            continue
        comp = compress(new_dec)
        if len(comp) > esize:
            ev_skip += 1
            continue                                # no cabe -> dejar japones
        comp = comp + b"\x00" * (esize - len(comp))
        pkb[eoff:eoff + esize] = comp
        ev_ok += 1; lines += n

    data[pkb_off:pkb_off + pkb_size] = pkb
    open(dst, "wb").write(data)
    print(f"eventos parcheados: {ev_ok} (skip por tamano: {ev_skip}); lineas ES: {lines}")
    print(f"-> {dst} (mismo tamano = {len(data)})")

    # verificacion
    arc2 = FaArchive(dst)
    o2, s2 = find_file(arc2, "inazuma1/data_iz/script/eve.pkb")
    pkb2 = open(dst, "rb").read()[o2:o2 + s2]
    eid, eoff, esize = ents[0]
    d2 = decompress(pkb2[eoff:eoff + esize])
    sample = [_decode_string(p, "sjis") for p in d2.split(b"\x00") if p[:1] and p[0] in (1, 2, 4)]
    sample = [s for s in sample if s.strip()][:3]
    print("verificacion (evento 0):", sample)


if __name__ == "__main__":
    main()
