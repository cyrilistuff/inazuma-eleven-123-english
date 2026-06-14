#!/usr/bin/env python3
"""Mapea el DIALOGO OFICIAL en espanol del DS (Inazuma Eleven NDS, lanzamiento ES) a los
eventos del 3DS, por event ID + alineacion de orden de lineas.

El DS y el 3DS comparten el MISMO formato de eventos (eve.pkb/eve.pkh, SSD) y los MISMOS
event IDs (1289/1293 de game1 coinciden). El DS separa la logica (script/eve.pkb) del
TEXTO (script/sp/evet.pkb = espanol oficial). Aqui:
  1. Parseamos evet.pkb (ES oficial) y el eve.pkb del 3DS (japones inline).
  2. Extraemos las lineas de DIALOGO de cada evento, en orden.
  3. Alineamos JP(3DS) <-> ES(DS) por el PATRON DE REPETICIONES (independiente del idioma)
     con difflib, y verificamos cada par por placeholders (%s/%d deben cuadrar).
  4. Volcamos translation/gameN/dialogo_oficial.csv: (event_id, japones, es_oficial).

NO sube nada con copyright: los volcados van a work/ (gitignored). El dialogo_oficial.csv
contiene texto oficial -> tratarlo como el dialogo.csv (glosario/refs, no ROM).

Uso:  python tools/ds_official.py game1   (DS = work/ie1_es)
      python tools/ds_official.py game2   (DS = work/ie2_es)
"""
import csv, difflib, os, re, struct, sys
sys.path.insert(0, "tools")
from lz10 import decompress
from pkb_unpack import parse_index, _decode_string
from fa_unpack import FaArchive
import reinsert as R

REPO = R.REPO

# Tabla de codificacion del DS espanol -> Unicode (bytes >=0x80). Inferida del contexto
# (cada byte verificado en frases reales del DS, minus/mayus distintas).
DS_TABLE = {
    # minusculas acentuadas
    0xB2: "á", 0xBA: "é", 0xBE: "í", 0xC4: "ó", 0xCA: "ú", 0xC2: "ñ", 0xCC: "ü",
    # mayusculas acentuadas
    0xD1: "Á", 0xD9: "É", 0xA6: "Í", 0xAB: "Ó", 0xA2: "Ú", 0xA9: "Ñ",
    # signos de apertura
    0xDF: "¡", 0xA5: "¿",
}

# game -> (carpeta DS extraida, sufijo del eve.pkb/pkh del 3DS dentro de archive.fa)
DS_DIR = {"game1": "ie1_es", "game2": "ie2_es"}
T3_SUF = {"game1": "inazuma1", "game2": "inazuma2"}

_CONF = re.compile(rb"^[A-Za-z][A-Za-z0-9]*=%[ds]")     # HikinukiX=%d (config var DS)


def decode_ds(b, unmapped=None):
    out = []
    for c in b:
        if c < 0x80:
            out.append(chr(c))
        elif c in DS_TABLE:
            out.append(DS_TABLE[c])
        else:
            if unmapped is not None:
                unmapped[c] = unmapped.get(c, 0) + 1
            out.append("?")
    return "".join(out)


def ds_lines(dec, unmapped=None):
    """Lineas de DIALOGO espanol de un evento DS (evet.pkb) en orden. Excluye config
    (HikinukiX=%d), nombres de archivo (.SAD/modelos) y comentarios SJIS japoneses."""
    out = []
    for p in dec.split(b"\x00"):
        if len(p) < 4 or b" " not in p or _CONF.match(p):
            continue
        if any(0x81 <= c <= 0x9f or 0xe0 <= c <= 0xff for c in p):  # SJIS = debug JP
            continue
        if sum(0x41 <= c <= 0x7a for c in p) < 3:                   # poca letra latina
            continue
        out.append(decode_ds(p, unmapped))
    return out


def jp_lines(dec):
    """Lineas de DIALOGO japones de un evento 3DS (eve.pkb) en orden."""
    return [_decode_string(p, "sjis") for p in dec.split(b"\x00")
            if len(p) >= 3 and p[0] == 1 and R.looks_like_dialogue(_decode_string(p, "sjis"))]


def _labels(seq):
    """Patron de repeticiones: cada linea -> indice de su 1a aparicion (idioma-agnostico)."""
    seen, out = {}, []
    for x in seq:
        seen.setdefault(x, len(seen))
        out.append(seen[x])
    return out


def _ph(s):
    return (s.count("%s"), s.count("%d"))


def align(jl, dl):
    """Devuelve dict {japones: es_oficial} para un evento, alineando por patron de
    repeticiones (difflib) y verificando placeholders. Solo pares de confianza."""
    out = {}
    if not jl or not dl:
        return out
    sm = difflib.SequenceMatcher(None, _labels(jl), _labels(dl), autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            j, e = jl[a + k], dl[b + k]
            if _ph(j) == _ph(e):                # placeholders deben cuadrar
                # si ya estaba mapeado a algo distinto, es ambiguo -> descartar
                if j in out and out[j] != e:
                    out[j] = None
                elif j not in out:
                    out[j] = e
    return {j: e for j, e in out.items() if e is not None}


def load_ds_events(game):
    base = os.path.join(REPO, "work", DS_DIR[game], "data_iz", "script", "sp")
    pkb = open(os.path.join(base, "evet.pkb"), "rb").read()
    idx = parse_index(open(os.path.join(base, "evet.pkh"), "rb").read())
    ev = {}
    for eid, o, s in idx:
        ch = pkb[o:o + s]
        ev[eid] = decompress(ch) if ch[:1] == b"\x10" else ch
    return ev


def load_3ds_events(game):
    arc = FaArchive(os.path.join(REPO, "work", "romfs", "archive.fa"))
    data = arc.d

    def find(suf):
        for p, o, s in arc.entries:
            if p.endswith(suf):
                return o, s
    po, ps = find(f"{T3_SUF[game]}/data_iz/script/eve.pkb")
    ho, hs = find(f"{T3_SUF[game]}/data_iz/script/eve.pkh")
    idx = parse_index(data[ho:ho + hs])
    return {eid: decompress(data[po + o:po + o + s]) for eid, o, s in idx
            if data[po + o:po + o + 1]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    game = next((a for a in sys.argv[1:] if a in DS_DIR), "game1")
    print(f"== {game} : mapeando dialogo OFICIAL del DS ==")
    ds = load_ds_events(game)
    t3 = load_3ds_events(game)
    common = sorted(set(ds) & set(t3))
    print(f"eventos: DS={len(ds)}  3DS={len(t3)}  comunes={len(common)}")

    unmapped = {}
    mapping = {}     # (eid, japones) -> es_oficial
    ev_ok = 0
    for eid in common:
        jl = jp_lines(t3[eid])
        dl = ds_lines(ds[eid], unmapped)
        m = align(jl, dl)
        if m:
            ev_ok += 1
            for j, e in m.items():
                mapping[(eid, j)] = e

    print(f"eventos con mapeo: {ev_ok} | pares (eid,jp)->ES oficiales: {len(mapping)}")
    if unmapped:
        print("bytes DS sin mapear (anadir a DS_TABLE):",
              {hex(k): v for k, v in sorted(unmapped.items(), key=lambda x: -x[1])[:12]})

    out_csv = os.path.join(REPO, "translation", game, "dialogo_oficial.csv")
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "japones", "es_oficial"])
        for (eid, j), e in sorted(mapping.items()):
            w.writerow([eid, j, e])
    print(f"-> {out_csv} ({len(mapping)} lineas oficiales)")


if __name__ == "__main__":
    main()
