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

# Eventos de ZONA (nombre de area + diálogos de NPC) que, aun siendo de sistema
# (eid>=90000000), se STRIPean: sufren el bug #2 (cuelgue al hablar con NPC, especifico
# del furigana). Son gameplay post-intro, no afectan al crear-partida. Detectados por
# tener nombre-de-zona tipo0x03 + diálogos con marcadores entre los eventos protegidos.
STRIP_ZONA = {92010510, 92040800, 92062100}   # サークル棟エリア, objetivo estatua, 正門エリア


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


def _is_ref_target(part):
    """True si un chunk es un destino VALIDO de referencia del bytecode: una cadena
    TIPADA (lectura furigana / string de debug / control: part[0] en 0x01..0x1f) o un
    BYTE-ID (1 byte alto >=0x80 que precede a esas cadenas). NO lo son los chunks
    vacios (NUL consecutivos) ni el DIALOGO (consumido secuencialmente, nunca por
    offset). Filtrar asi evita corromper operandos numericos (p.ej. 1000) que por
    casualidad coinciden con un inicio de chunk -> esa era la causa del cuelgue."""
    if not part:
        return False
    if 0x01 <= part[0] <= 0x1f:
        return True
    if len(part) == 1 and part[0] >= 0x80:
        return True
    return False


def reencode_var(dec, trans, strip=False):
    """Redimensiona el dialogo a longitud COMPLETA y actualiza las referencias del
    bytecode (offset-fixup) para que sigan apuntando a las cadenas movidas.

    El bytecode guarda offsets (rel a la seccion de texto s10) que apuntan a cadenas
    repartidas por TODA la seccion (lecturas furigana, archivos .SAD...). Al agrandar
    un chunk de dialogo, todo lo que va detras se desplaza; hay que sumar ese delta a
    cada offset del codigo que apunte a una posicion movida. SOLO se actualizan los
    offsets que apuntan a un destino VALIDO (_is_ref_target): asi no se tocan los
    operandos numericos que coinciden con una posicion. Devuelve (nuevo_dec, n_lineas).

    strip=True (eventos de HISTORIA): QUITA el furigana (marcadores %NF) y crece el
    texto a longitud completa, vaciando las N lecturas siguientes. Asi se ve TODO el
    texto ES sin cortes y sin el ruby japones (inutil en espanol). El furigana solo se
    conserva (strip=False) en eventos de sistema/intro (eid>=90000000), donde quitarlo
    descuadra el crear-partida (ver FURIGANA_LECCIONES ❌#1). En esos se mantiene a
    MISMO TAMANO (= v25 INPLACE), porque hacer crecer lineas con furigana cuelga el
    motor de ruby al avanzar (❌#8)."""
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
    pending = 0                               # nº de lecturas a vaciar tras un dialogo STRIP
    ref_targets = set()                       # posiciones de destinos de referencia VALIDOS
    # mapa de desplazamiento: old_pos -> delta acumulado en esa posicion del original
    shift = []                                # lista (old_start, delta_acumulado_a_partir_de_ahi)
    cum = 0
    for k, part in enumerate(parts):
        if _is_ref_target(part):
            ref_targets.add(rel)
        new = part
        if strip and pending > 0 and R._is_reading(part):
            # vaciar la lectura kana que pertenece a un dialogo que acabamos de traducir
            # (1 por marcador). Mismo tamano (espacios) -> no desplaza.
            new = bytes(part[:2]) + b" " * (len(part) - 2)
            pending -= 1
        elif len(part) >= 3 and part[0] in (1, 2, 4):
            marks = R._MK.findall(part)
            clean = _decode_string(part, "sjis")
            if R.looks_like_dialogue(clean):
                # NUEVA LINEA de dialogo: cortar el arrastre del vaciado de la linea
                # anterior. Si un dialogo tenia mas marcadores que lecturas reales, el
                # 'pending' sobrante NO debe vaciar las lecturas de ESTA linea (eso
                # desincronizaba el furigana de lineas sin traducir -> texto vacio/cuelgue).
                pending = 0
                es = trans.get(clean)
                if es:
                    es = _re.sub(r"%[1-9]F", "", es)
                    if not strip:
                        # SISTEMA/INTRO: MISMO TAMANO en TODAS las lineas (= v25 INPLACE),
                        # con o sin furigana. NO crecer NINGUNA: crecer una linea con
                        # furigana cuelga (runtime de ruby, ❌#8) y crecer una linea PLANA
                        # del evento DESPLAZA las lineas de furigana -> reubicarlas tambien
                        # rompe el ruby. Asi el evento queda byte-identico en tamano (=v25)
                        # y no se reubica nada. (Coste: las planas del sistema tambien se
                        # truncan; son pocas y es la zona protegida.)
                        budget = len(part) - 2
                        if marks:
                            body = R._furigana_body_bytes(part[2:], es, budget)
                            if body is not None:
                                new = bytes(part[:2]) + body; n += 1   # mismo tamano
                        else:
                            b = R.es_encode(es, budget)
                            new = bytes(part[:2]) + b + b" " * (budget - len(b)); n += 1
                    else:
                        # HISTORIA (strip): crece a texto COMPLETO, sin furigana (es ya
                        # viene sin %NF). Si tenia marcadores, marcar sus lecturas para
                        # vaciarlas (mantiene el balance del motor).
                        new = bytes(part[:2]) + R.es_encode(es, 1 << 20); n += 1
                        if marks:
                            pending += len(marks)
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
            # SOLO offsets que apuntan a un destino VALIDO (lectura/debug/byte-id);
            # los operandos numericos coincidentes (p.ej. 1000) apuntan a chunk vacio
            # o a dialogo -> NO se tocan (eso corrompia el evento y colgaba el juego).
            if first_change <= v < tlen and v in ref_targets:
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
                # STRIP (quitar furigana, texto completo) en HISTORIA; conservar furigana
                # (INPLACE mismo-tamano) en sistema/intro (eid>=90000000) para no romper
                # el crear-partida. Ver FURIGANA_LECCIONES ❌#1.
                # EXCEPCION: eventos de ZONA (NPCs por area) que aun siendo >=90000000
                # sufren el bug #2 (cuelgue al hablar con NPC, furigana-especifico). Son
                # gameplay POST-intro (no afectan al crear-partida) -> se STRIPean para
                # quitarles el furigana (lo arregla) y dar texto completo. Ver LECCIONES #2.
                strip = eid < 90000000 or eid in STRIP_ZONA
                new_dec, n = reencode_var(dec, trans[eid], strip=strip)
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
