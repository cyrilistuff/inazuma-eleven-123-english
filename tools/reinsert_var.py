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
STRIP_ZONA = {92040800, 92062100}   # objetivo estatua, 正門エリア (fuera del rango cap.1)


def is_strip_event(eid):
    """True si el evento se STRIPea (historia/gameplay): quita furigana, texto completo.
    False = evento PROTEGIDO (apertura/sistema/menu): furigana a mismo tamano (=v25), NO
    se le aplica la traduccion oficial (descuadra el crear-partida). Debe coincidir con
    la decision 'strip' de main()."""
    return eid < 90000000 or eid in STRIP_ZONA or 92010510 <= eid < 92011000
# Ademas se STRIPea el bloque de gameplay del cap.1 [92010510, 92011000): zona
# サークル棟エリア (92010510) y los eventos interactivos siguientes (92010520 "Axel se
# fue", 92010600 torre, 92010640 entreno, 92010730 casa, 92010820, 92010900...). Son
# POST-control (el crear-partida es la apertura 92010100..92010509) -> STRIP seguro,
# arregla el bug #2 (cuelgue al hablar, furigana-especifico) y da texto completo.


def _instr_operands(code, s10):
    """Recorre el stream de instrucciones SSD (desde 0x20) y produce (pos_operando,
    opcode_u32, slot). Formato de instruccion VERIFICADO en el ROM:
        <u16 indice><u16 longitud><u32 opcode><operandos u32...>
    'longitud' (en +2) es el tamano TOTAL de la instruccion en bytes (incluye los 8 de
    cabecera+opcode). Asi se distinguen con PRECISION los operandos de los opcodes/
    cabeceras: clave para no corromper contadores numericos (causa del crash Read32)."""
    i = 0x20
    while i + 8 <= s10:
        ln = struct.unpack_from("<H", code, i + 2)[0]
        if ln < 8 or i + ln > s10:
            return
        op = struct.unpack_from("<I", code, i + 4)[0]
        for slot, opos in enumerate(range(i + 8, i + ln, 4)):
            yield opos, op, slot
        i += ln


def build_string_slots(events):
    """Clasifica que (opcode, slot) son OFFSETS DE STRING (referencias a texto) frente a
    operandos numericos/indice. Criterio data-driven verificado en el ROM: un slot de
    offset apunta SIEMPRE al INICIO de un chunk o vale 0 (nulo); casi NUNCA cae a media
    cadena. Un slot numerico (contador, coordenada, ID, delay) cae a media cadena ~40-80%
    de las veces (valores aleatorios). Devuelve el set de (opcode_u32, slot) de string.

    Solo estos se reubican al crecer el dialogo (offset-fixup). Los demas operandos se
    dejan INTACTOS -> nunca se corrompe un contador (eso convertia un 6 en un offset
    grande y el motor leia un array hasta salirse de la RAM = crash 'unmapped Read32')."""
    from collections import Counter
    tot = Counter(); hit = Counter(); zero = Counter(); mid = Counter()
    for dec in events:
        if dec[:4] != b"SSD\x00":
            continue
        s10 = struct.unpack_from("<I", dec, 0x10)[0]
        code = dec[:s10]; text = dec[s10:]; tlen = len(text)
        starts = set(); r = 0
        for p in text.split(b"\x00"):
            starts.add(r); r += len(p) + 1
        for opos, op, slot in _instr_operands(code, s10):
            v = struct.unpack_from("<I", code, opos)[0]
            key = (op, slot); tot[key] += 1
            if v == 0:
                zero[key] += 1
            elif 16 <= v < tlen:
                if v in starts:
                    hit[key] += 1
                else:
                    mid[key] += 1
    return {k for k in tot
            if tot[k] >= 10 and hit[k] >= 5
            and (hit[k] + zero[k]) / tot[k] >= 0.90 and mid[k] / tot[k] <= 0.03}


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


def reencode_var(dec, trans, strip=False, string_slots=frozenset()):
    """Redimensiona el dialogo a longitud COMPLETA y reubica SOLO las referencias de
    string del bytecode (offset-fixup PRECISO via 'string_slots'), dejando INTACTOS los
    operandos numericos/indice. Devuelve (nuevo_dec, n_lineas).

    'string_slots' = set de (opcode, slot) que son offsets de string (build_string_slots,
    criterio: el operando apunta SIEMPRE a inicio de chunk o vale 0, casi nunca a media
    cadena). Solo esos operandos se reubican al crecer el texto; cualquier otro u32 que
    por azar coincida con una posicion de chunk se IGNORA. Asi NUNCA se corrompe un
    contador/indice (eso convertia p.ej. un 6 en un offset grande y un handler leia un
    array hasta salirse de la RAM = crash 'unmapped Read32 ... PC 0x001C8D68').

    strip=True (HISTORIA): QUITA el furigana (marcadores %NF) y crece el texto a longitud
    completa, vaciando las N lecturas siguientes (mismo tamano). strip=False (sistema/
    intro): furigana a MISMO TAMANO (=v25 INPLACE) para no romper el crear-partida
    (FURIGANA_LECCIONES ❌#1) ni el runtime de ruby al crecer (❌#8)."""
    if dec[:4] != b"SSD\x00":
        return dec, 0
    s10 = struct.unpack_from("<I", dec, 0x10)[0]
    head = bytearray(dec[:s10])               # cabecera + codigo (mutable para el fixup)
    text = dec[s10:]
    tlen = len(text)
    parts = text.split(b"\x00")
    old_starts = set(); _r = 0                 # inicios de chunk en el texto ORIGINAL
    for _p in parts:
        old_starts.add(_r); _r += len(_p) + 1

    # 1) Decidir el contenido nuevo de cada chunk (bytes) o ELIMINARLO (None).
    #    CLAVE del bug del bloqueo (controles bloqueados al hablar con NPC): el motor
    #    consume 1 LECTURA furigana por cada MARCADOR %NF. Al traducir (STRIP) quitamos
    #    los marcadores -> 0 marcadores; si dejamos las lecturas como chunks, quedan
    #    lecturas HUERFANAS (sin marcador que las consuma) que el motor lee como lineas
    #    vacias / se descuadra -> no cierra el dialogo. Solucion: ELIMINAR las lecturas
    #    de las lineas traducidas (no vaciarlas) -> marcadores y lecturas balanceados.
    new_content = []                          # contenido nuevo por chunk (None = eliminar)
    n = 0
    drop_readings = False                      # ¿eliminar las lecturas que siguen? (linea STRIP)
    for part in parts:
        content = part
        if strip and drop_readings and R._is_reading(part):
            # La linea traducida quedo SIN marcadores -> consume 0 lecturas -> eliminar
            # TODAS sus lecturas (hasta la siguiente linea de dialogo). Asi marcadores y
            # lecturas quedan balanceados como en el original (clave del bloqueo de NPCs).
            content = None
        elif len(part) >= 3 and part[0] in (1, 2, 4):
            marks = R._MK.findall(part)
            clean = _decode_string(part, "sjis")
            if R.looks_like_dialogue(clean):
                drop_readings = False         # reset: nueva linea de dialogo
                es = trans.get(clean)
                if es:
                    es = _re.sub(r"%[1-9]F", "", es)
                    if not strip:
                        # SISTEMA/INTRO: MISMO TAMANO (= v25 INPLACE): crecer una linea con
                        # furigana cuelga (ruby ❌#8); plana mas larga desplaza el furigana.
                        budget = len(part) - 2
                        if marks:
                            body = R._furigana_body_bytes(part[2:], es, budget)
                            if body is not None:
                                content = bytes(part[:2]) + body; n += 1   # mismo tamano
                        else:
                            b = R.es_encode(es, budget)
                            content = bytes(part[:2]) + b + b" " * (budget - len(b)); n += 1
                    else:
                        # HISTORIA (strip): crece a texto COMPLETO, sin furigana, y se
                        # ELIMINAN sus lecturas (no tiene marcadores -> 0 lecturas).
                        content = bytes(part[:2]) + R.es_encode(es, 1 << 20); n += 1
                        drop_readings = True
        new_content.append(content)

    # 2) Construir el texto nuevo y el mapa old_start -> new_start (None si se elimino).
    out = bytearray()
    pos_map = {}
    rel = 0
    first = True
    for part, content in zip(parts, new_content):
        if content is None:
            pos_map[rel] = None               # chunk eliminado
        else:
            if not first:
                out += b"\x00"                # separador antes de cada chunk salvo el 1º
            pos_map[rel] = len(out)
            out += content
            first = False
        rel += len(part) + 1
    new_text = bytes(out)

    # 3) FIXUP PRECISO: reubicar SOLO operandos de slots-string que apuntan a un inicio de
    #    chunk movido. Si alguno apunta a un chunk ELIMINADO, no es honrable -> revertir el
    #    evento a japones (seguro). Los operandos numericos/indice NO se tocan.
    relocated = []
    for opos, op, slot in _instr_operands(head, s10):
        if (op, slot) not in string_slots:
            continue
        v = struct.unpack_from("<I", head, opos)[0]
        if v in old_starts:                   # es una referencia a un inicio de chunk
            np = pos_map[v]
            if np is None:
                return dec, 0                 # apunta a chunk eliminado -> revertir
            if np != v:
                struct.pack_into("<I", head, opos, np)
                relocated.append(opos)
    # VALIDACION: cada operando reubicado debe caer EXACTO en un inicio de chunk nuevo.
    if relocated:
        new_starts = set(); _r = 0
        for _p in new_text.split(b"\x00"):
            new_starts.add(_r); _r += len(_p) + 1
        for opos in relocated:
            if struct.unpack_from("<I", head, opos)[0] not in new_starts:
                return dec, 0                 # shift descuadrado -> revertir (seguro)

    if n == 0:
        return dec, 0                         # nada traducido -> dejar original
    new_dec = bytearray(bytes(head) + new_text)
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
        # Pre-descomprimir TODOS los eventos para clasificar los slots-string (que
        # (opcode,slot) del bytecode son offsets de texto) -> fixup preciso, sin corromper
        # operandos numericos. Es la diferencia entre arreglar las referencias y crashear.
        decs = {eid: decompress(bytes(pkb[eoff:eoff + esize])) for eid, eoff, esize in ents}
        string_slots = build_string_slots(decs.values())
        print(f"{game}: {len(string_slots)} slots-string detectados (offset-fixup preciso)")
        new_pkb = bytearray()
        new_index = []                                       # (eid, new_off, new_size)
        ev_ok = lines = grew = reverted = 0
        for eid, eoff, esize in ents:
            comp_orig = bytes(pkb[eoff:eoff + esize])
            if eid in trans:
                dec = decs[eid]
                # STRIP (quitar furigana, texto completo) en HISTORIA; conservar furigana
                # (INPLACE mismo-tamano) en sistema/intro (eid>=90000000) para no romper
                # el crear-partida. Ver FURIGANA_LECCIONES ❌#1.
                # EXCEPCION: eventos de ZONA (NPCs por area) que aun siendo >=90000000
                # sufren el bug #2 (cuelgue al hablar con NPC, furigana-especifico). Son
                # gameplay POST-intro (no afectan al crear-partida) -> se STRIPean para
                # quitarles el furigana (lo arregla) y dar texto completo. Ver LECCIONES #2.
                strip = is_strip_event(eid)
                new_dec, n = reencode_var(dec, trans[eid], strip=strip,
                                          string_slots=string_slots)
                if n:
                    comp = compress(new_dec)
                    ev_ok += 1; lines += n
                    if len(comp) > esize:
                        grew += 1
                else:
                    comp = comp_orig
                    if eid in trans:
                        reverted += 1
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
              f"(+{len(new_pkb)-pkb_size}); {grew} crecieron; {reverted} revertidos (validacion)")


if __name__ == "__main__":
    main()
