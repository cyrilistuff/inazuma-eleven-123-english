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
from font_patch import patch_font_bytes

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Acentos/signos del espanol -> caracter griego reusado (glifo sustituido en la
# fuente, ver font_patch.PLAN). Al codificar en Shift-JIS dan 2 bytes (rango 0x839F+)
# que el juego mapea a U+0391.. -> CMAP -> el glifo ES.
GREEK = str.maketrans({"á": "Α", "é": "Β", "í": "Γ", "ó": "Δ", "ú": "Ε",
                       "ü": "Ζ", "ñ": "Η", "Á": "Θ", "É": "Ι", "Í": "Κ",
                       "Ó": "Λ", "Ú": "Μ", "Ñ": "Ν", "¡": "Ξ", "¿": "Ο",
                       "ª": "a", "º": "o", "“": '"', "”": '"', "—": "-", "…": "..."})

FONTS = ["font/FONT12T.bcfnt", "font/FONT12.bcfnt", "font/FONT8.bcfnt"]


def es_encode(s, budget):
    """Codifica el ES (acentos->griego->SJIS) sin partir multibyte ni pasar budget."""
    out = b""
    for ch in s.translate(GREEK):
        b = ch.encode("shift-jis", "replace")
        if len(out) + len(b) > budget:
            break
        out += b
    return out


def find_file(arc, suffix):
    for path, off, size in arc.entries:
        if path.endswith(suffix):
            return off, size
    raise SystemExit("no encontrado: " + suffix)


# (carpeta_3ds, carpeta_translation) de cada juego incluido en la build
GAMES = [("inazuma1", "game1"), ("inazuma2", "game2")]


def load_translations(game):
    """{event_id: {japones_limpio: es_final}} para lineas con es_final."""
    out = {}
    path = os.path.join(REPO, "translation", game, "dialogo.csv")
    if not os.path.exists(path):
        return out
    for row in csv.DictReader(open(path, encoding="utf-8")):
        if row["estado"] == "pendiente" or not row["es_final"]:
            continue
        out.setdefault(int(row["event_id"]), {})[row["japones"]] = row["es_final"]
    return out


def reencode_event(dec, trans, esize):
    """Sustituye las cadenas traducidas (tamano de chunk invariante). Si el evento
    recomprimido no cabe, revierte lineas (las que mas ocupan) hasta que quepa, en
    vez de saltar el evento entero. Devuelve (comp_bytes_o_None, n_aplicadas)."""
    orig = dec.split(b"\x00")
    parts = list(orig)
    changed = []                                    # (idx, peso_es)
    for i, part in enumerate(orig):
        if len(part) < 3 or part[0] not in (1, 2, 4):
            continue
        # SEGURO: no tocar chunks con furigana (sus lecturas 0x03 descuadran el
        # script si se quitan los marcadores). Se traducen en una fase posterior.
        if any(m in part for m in (b"%1F", b"%2F", b"%3F", b"%4F")):
            continue
        es = trans.get(_decode_string(part, "sjis"))
        if not es:
            continue
        budget = len(part) - 2
        body = es_encode(es, budget)
        weight = len(body)
        body = body + b" " * (budget - len(body))
        parts[i] = bytes(part[:2]) + body
        changed.append((i, weight))
    if not changed:
        return None, 0
    comp = compress(b"\x00".join(parts))
    n = len(changed)
    if len(comp) > esize:
        for idx, _w in sorted(changed, key=lambda x: -x[1]):
            parts[idx] = orig[idx]                   # revertir a japones (el peor primero)
            n -= 1
            comp = compress(b"\x00".join(parts))
            if len(comp) <= esize:
                break                                # reverter todo -> original siempre cabe
    if len(comp) > esize:
        return None, 0
    return comp + b"\x00" * (esize - len(comp)), n


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.join(REPO, "work", "romfs", "archive.fa")
    dst = os.path.join(REPO, "work", "archive_es.fa")
    data = bytearray(open(src, "rb").read())
    arc = FaArchive(src)

    games = [g for g in GAMES if g[1] in sys.argv] or GAMES
    for folder, game in games:
        trans = load_translations(game)
        if not trans:
            continue
        pkb_off, pkb_size = find_file(arc, f"{folder}/data_iz/script/eve.pkb")
        pkh_off, pkh_size = find_file(arc, f"{folder}/data_iz/script/eve.pkh")
        pkb = bytearray(data[pkb_off:pkb_off + pkb_size])
        ents = parse_index(bytes(data[pkh_off:pkh_off + pkh_size]))
        ev_ok = lines = 0
        for eid, eoff, esize in ents:
            if eid not in trans:
                continue
            dec = decompress(bytes(pkb[eoff:eoff + esize]))
            comp, n = reencode_event(dec, trans[eid], esize)
            if not comp or n == 0:
                continue
            pkb[eoff:eoff + esize] = comp
            ev_ok += 1; lines += n
        data[pkb_off:pkb_off + pkb_size] = pkb
        print(f"{game}: {ev_ok} eventos, {lines} lineas ES")

    # parchear fuentes (anadir glifos ES) - mismo tamano, in-place
    for fp in FONTS:
        foff, fsize = find_file(arc, fp)
        ext = os.path.join(REPO, "work", "fa_extract", *fp.split("/"))
        patched = patch_font_bytes(ext)
        assert len(patched) == fsize, f"{fp}: tamano cambio {len(patched)}!={fsize}"
        data[foff:foff + fsize] = patched

    open(dst, "wb").write(data)
    print(f"fuentes parcheadas: {len(FONTS)}")
    print(f"-> {dst} (mismo tamano = {len(data)})")


if __name__ == "__main__":
    main()
