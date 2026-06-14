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
# Para longitud variable usamos compresion "store" (todo literales): O(n), instantanea.
# El tamano no importa (el contenedor se reconstruye); la velocidad si (~4000 eventos).
from lz10 import compress_store as compress, decompress
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


def _furigana_var(orig_body, es):
    """Cuerpo furigana de longitud VARIABLE (sin relleno): marcadores por pagina
    (ancho completo) + texto ES completo. Devuelve bytes o None si las paginas no
    casan. NO asigna relleno (a diferencia de _furigana_body_bytes con budget enorme)."""
    orig_pages = orig_body.split(b"\\f")
    es_pages = es.split("\\f")
    if len(es_pages) != len(orig_pages):
        return None
    out = []
    for i, esp in enumerate(es_pages):
        mk = [m.group().decode() for m in R._MK.finditer(orig_pages[i])]
        prefix = "".join(m + "　" * int(m[1]) for m in mk)   # marcador + N espacios ancho completo
        out.append(R.es_encode(prefix + esp, 1 << 20))           # 1MB tope = sin cortar, sin alloc enorme
    return b"\\f".join(out)


def reencode_var(dec, trans):
    """Redimensiona el dialogo a longitud COMPLETA y actualiza las referencias del
    bytecode (offset-fixup) para que sigan apuntando a las cadenas movidas.

    El bytecode guarda offsets (rel a la seccion de texto s10) que apuntan a cadenas
    repartidas por TODA la seccion (incluido el dialogo). Al agrandar un chunk, todo
    lo que va detras se desplaza; hay que sumar ese delta a cada offset del codigo que
    apunte a una posicion movida. Devuelve (nuevo_dec, n_lineas)."""
    if dec[:4] != b"SSD\x00":
        return dec, 0
    s10 = struct.unpack_from("<I", dec, 0x10)[0]
    head = bytearray(dec[:s10])               # cabecera + codigo (mutable para el fixup)
    text = dec[s10:]
    tlen = len(text)
    out = bytearray()
    n = 0
    parts = text.split(b"\x00")
    rel = 0
    old_starts = set()                        # posiciones de inicio de chunk (referencias reales)
    # mapa de desplazamiento: old_pos -> delta acumulado en esa posicion del original
    shift = []                                # lista (old_start, delta_acumulado_a_partir_de_ahi)
    cum = 0
    for k, part in enumerate(parts):
        old_starts.add(rel)
        new = part
        if len(part) >= 3 and part[0] in (1, 2, 4):
            marks = R._MK.findall(part)
            clean = _decode_string(part, "sjis")
            if R.looks_like_dialogue(clean):
                es = trans.get(clean)
                if es:
                    es = _re.sub(r"%[1-9]F", "", es)
                    if marks:
                        body = _furigana_var(part[2:], es)
                        if body is not None:
                            new = bytes(part[:2]) + body; n += 1
                    else:
                        new = bytes(part[:2]) + R.es_encode(es, 1 << 20); n += 1
        out += new
        d = len(new) - len(part)
        if d:
            # a partir del FINAL de este chunk en el original, todo se desplaza +d
            cum += d
            shift.append((rel + len(part), cum))
        rel += len(part) + 1
        if k != len(parts) - 1:
            out += b"\x00"

    def new_pos(old):
        """posicion nueva de un offset del texto tras los desplazamientos."""
        delta = 0
        for start, c in shift:
            if old >= start:
                delta = c
            else:
                break
        return old + delta

    # offset-fixup: recorrer el codigo en u32 alineados; los que apuntan a una posicion
    # del texto que se movio, recolocarlos. Solo se tocan offsets que cambian (los que
    # apuntan a cadenas anteriores al primer cambio quedan igual -> operandos numericos
    # pequenos no se tocan salvo que apunten justo a una posicion desplazada).
    if shift:
        first_change = shift[0][0]
        for i in range(0, len(head) - 3, 4):
            v = struct.unpack_from("<I", head, i)[0]
            # SOLO offsets que apuntan a un INICIO de chunk (referencias reales);
            # los operandos numericos coincidentes apuntan a mitad de cadena -> no tocar.
            if first_change <= v < tlen and v in old_starts:
                np = new_pos(v)
                if np != v:
                    struct.pack_into("<I", head, i, np)

    new_dec = bytearray(bytes(head) + bytes(out))
    struct.pack_into("<I", new_dec, 0x08, len(new_dec))       # tamano total
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
