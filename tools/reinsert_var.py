#!/usr/bin/env python3
"""[Longitud VARIABLE] Redimensiona los eventos del eve.pkb para meter el espanol
SIN cortes. Clave (verificada en work/find_refs.py): los chunks de DIALOGO se
consumen SECUENCIALMENTE (no se referencian por offset), asi que se pueden agrandar;
solo las cadenas de debug del inicio se referencian por offset rel_s10 -> esas NO se
tocan (y al ir ANTES del dialogo, no se mueven al agrandar el dialogo).

Salida: work/eve_var/<game>.pkb + .pkh reempaquetados (eventos de tamano variable,
indice pkh con offsets nuevos). Luego fa_repack.py mete el pkb en archive.fa.

Reusa helpers de reinsert.py (glosario, es_encode, furigana INPLACE).
"""
import csv, os, struct, sys
import re as _re
sys.path.insert(0, "tools")
from fa_unpack import FaArchive
from lz10 import compress, decompress
from pkb_unpack import parse_index, _decode_string
import reinsert as R

REPO = R.REPO
GAMES = R.GAMES


def referenced_offsets(d, s10):
    """offsets rel_s10 que el codigo (d[:s10]) referencia como u32 y apuntan a inicio
    de chunk en la seccion de texto -> NO redimensionar esos chunks."""
    code = d[:s10]
    text = d[s10:]
    refs = set()
    # posiciones de inicio de chunk (tras NUL) en la seccion de texto
    starts = {0}
    for i, b in enumerate(text):
        if b == 0:
            starts.add(i + 1)
    for rel in sorted(starts):
        if rel >= 16 and code.count(struct.pack("<I", rel)) > 0:
            refs.add(rel)
    return refs


def reencode_var(dec, trans):
    """Redimensiona: traduce dialogo a longitud completa (sin cortar), conserva
    marcadores furigana (INPLACE, ancho completo) + lecturas. Salta chunks
    referenciados por offset. Devuelve (nuevo_dec, n_lineas) o (dec, 0)."""
    if dec[:4] != b"SSD\x00":
        return dec, 0
    s10 = struct.unpack_from("<I", dec, 0x10)[0]
    refs = referenced_offsets(dec, s10)
    head = dec[:s10]                      # cabecera + codigo + cadenas debug (intactas)
    text = dec[s10:]
    # recorrer chunks de la seccion de texto; redimensionar solo dialogo no referenciado
    out = bytearray()
    pos = 0
    n = 0
    parts = text.split(b"\x00")
    rel = 0
    for k, part in enumerate(parts):
        new = part
        if len(part) >= 3 and part[0] in (1, 2, 4) and rel not in refs:
            marks = R._MK.findall(part)
            clean = _decode_string(part, "sjis")
            if R.looks_like_dialogue(clean):
                es = trans.get(clean)
                if es:
                    es = _re.sub(r"%[1-9]F", "", es)
                    if marks:
                        # INPLACE sin limite de presupuesto (texto completo)
                        body = R._furigana_body_bytes(part[2:], es, 1 << 30)
                        if body is not None:
                            body = body.rstrip(b" ")          # sin relleno (longitud variable)
                            new = bytes(part[:2]) + body
                            n += 1
                    else:
                        new = bytes(part[:2]) + R.es_encode(es, 1 << 30)
                        n += 1
        out += new
        rel += len(part) + 1
        if k != len(parts) - 1:
            out += b"\x00"
    new_text = bytes(out)
    new_dec = bytearray(head + new_text)
    struct.pack_into("<I", new_dec, 0x08, len(new_dec))       # actualizar tamano total
    return bytes(new_dec), n


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.join(REPO, "work", "romfs", "archive.fa")
    data = open(src, "rb").read()
    arc = FaArchive(src)
    outdir = os.path.join(REPO, "work", "eve_var")
    os.makedirs(outdir, exist_ok=True)

    games = [g for g in GAMES if g[1] in sys.argv] or GAMES
    for folder, game in games:
        trans = R.load_translations(game)
        if not trans:
            continue
        pkb_off, pkb_size = R.find_file(arc, f"{folder}/data_iz/script/eve.pkb")
        pkh_off, pkh_size = R.find_file(arc, f"{folder}/data_iz/script/eve.pkh")
        pkh = bytes(data[pkh_off:pkh_off + pkh_size])
        pkb = data[pkb_off:pkb_off + pkb_size]
        ents = parse_index(pkh)
        new_pkb = bytearray()
        new_index = []                                       # (eid, new_off, new_size)
        ev_ok = lines = grew = 0
        for eid, eoff, esize in ents:
            comp_orig = bytes(pkb[eoff:eoff + esize])
            if eid in trans:
                dec = decompress(comp_orig)
                new_dec, n = reencode_var(dec, trans[eid])
                if n:
                    comp = compress(new_dec)
                    ev_ok += 1; lines += n
                    if len(comp) > esize:
                        grew += 1
                else:
                    comp = comp_orig
            else:
                comp = comp_orig
            off = len(new_pkb)
            new_pkb += comp
            new_index.append((eid, off, len(comp)))
            while len(new_pkb) % 4:                            # alineacion 4 (como el original)
                new_pkb += b"\x00"
        # reconstruir pkh: cabecera 0x30 igual, tabla de 12B con offsets nuevos
        new_pkh = bytearray(pkh[:0x30])
        for eid, off, size in new_index:
            new_pkh += struct.pack("<III", eid, off, size)
        struct.pack_into("<I", new_pkh, 0x10, len(new_pkh))   # +0x10 = tamano del pkh
        open(os.path.join(outdir, f"{game}.pkb"), "wb").write(new_pkb)
        open(os.path.join(outdir, f"{game}.pkh"), "wb").write(new_pkh)
        print(f"{game}: {ev_ok} eventos, {lines} lineas ES | pkb {pkb_size} -> {len(new_pkb)} "
              f"(+{len(new_pkb)-pkb_size}); {grew} eventos crecieron")


if __name__ == "__main__":
    main()
