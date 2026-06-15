#!/usr/bin/env python3
"""Validacion OFFLINE de la build: revisa TODOS los eventos generados (work/eve_var)
contra el original y avisa de cualquier regresion SIN tener que jugar.

Caza las clases de bug que ya hemos pisado:
  · operandos numericos CORROMPIDOS por el offset-fixup  -> crash 'unmapped Read32'
  · referencias de string que apuntan a media cadena     -> texto basura / cuelgue
  · dialogo que se quedo VACIO                            -> NPC con cuadro vacio
  · estructura SSD invalida (magic, tamano, walk de instrucciones)
  · desbalance marcador<->lectura furigana empeorado      -> bloqueo de controles

Uso:  python tools/validate.py            (game1 + game2)
      python tools/validate.py game1      (solo uno)

Sale con codigo !=0 si hay algun FALLO -> integrable en el pipeline de build.
"""
import os, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, "tools")
from fa_unpack import FaArchive
from pkb_unpack import parse_index, _decode_string
from lz10 import decompress
import reinsert as R
import reinsert_var as V

REPO = R.REPO
SUF = {"game1": "inazuma1", "game2": "inazuma2", "game3": "inazuma3"}


def _events(pkb, idx):
    out = {}
    for eid, o, s in idx:
        ch = pkb[o:o + s]
        try:
            out[eid] = decompress(ch) if ch[:1] == b"\x10" else ch
        except Exception:
            out[eid] = ch
    return out


def _starts(text):
    s = set(); r = 0
    for p in text.split(b"\x00"):
        s.add(r); r += len(p) + 1
    return s


def _dlines(dec):
    if dec[:4] != b"SSD\x00":
        return []
    s10 = struct.unpack_from("<I", dec, 0x10)[0]
    return [(_decode_string(p, "sjis"), p) for p in dec[s10:].split(b"\x00")
            if len(p) >= 3 and p[0] in (1, 2, 4) and R.looks_like_dialogue(_decode_string(p, "sjis"))]


def _imbalance(dec):
    s10 = struct.unpack_from("<I", dec, 0x10)[0]
    parts = dec[s10:].split(b"\x00")
    return (sum(len(R._MK.findall(p)) for p in parts)
            - sum(1 for p in parts if R._is_reading(p)))


def validate(game):
    suf = SUF[game]
    arc = FaArchive(os.path.join(REPO, "work", "romfs", "archive.fa"))
    data = arc.d

    def find(s):
        for p, o, sz in arc.entries:
            if p.endswith(s):
                return o, sz
        return None

    r = find(f"{suf}/data_iz/script/eve.pkb")
    if not r:
        print(f"[{game}] sin eve.pkb"); return True
    po, ps = r
    ho, hs = find(f"{suf}/data_iz/script/eve.pkh")
    odecs = _events(bytes(data[po:po + ps]), parse_index(bytes(data[ho:ho + hs])))
    ss = V.build_string_slots(odecs.values())

    npkb = open(os.path.join(REPO, "work", "eve_var", f"{game}.pkb"), "rb").read()
    npkh = open(os.path.join(REPO, "work", "eve_var", f"{game}.pkh"), "rb").read()
    ndecs = _events(npkb, parse_index(npkh))

    n_mod = 0
    bad_operand = bad_midref = bad_empty = bad_struct = bad_growfg = worse_imb = 0
    ex = {"operand": [], "midref": [], "empty": [], "struct": [], "growfg": [], "imb": []}

    for eid in odecs:
        od = odecs[eid]; nd = ndecs.get(eid)
        if nd is None or od == nd:
            continue
        n_mod += 1
        # 1) estructura SSD
        if od[:4] == b"SSD\x00" and nd[:4] != b"SSD\x00":
            bad_struct += 1; ex["struct"].append(eid); continue
        if nd[:4] != b"SSD\x00":
            continue
        s10 = struct.unpack_from("<I", nd, 0x10)[0]
        if struct.unpack_from("<I", od, 0x10)[0] != s10:
            bad_struct += 1; ex["struct"].append(eid); continue
        ncode, ntext = nd[:s10], nd[s10:]
        ocode = od[:s10]
        nstarts = _starts(ntext); ostarts = _starts(od[s10:])
        strpos = {opos for opos, op, slot in V._instr_operands(ncode, s10) if (op, slot) in ss}

        # 2) ningun operando NO-string del codigo cambio (salvo +0x08 = tamano total)
        for i in range(0, len(ocode) - 3, 4):
            if i == 0x08 or i in strpos:
                continue
            if ocode[i:i + 4] != ncode[i:i + 4]:
                bad_operand += 1
                if len(ex["operand"]) < 8:
                    ex["operand"].append((eid, hex(i)))
                break

        # 3) referencias de string NUEVAS que caen a media cadena
        for opos, op, slot in V._instr_operands(ncode, s10):
            if (op, slot) not in ss:
                continue
            nv = struct.unpack_from("<I", ncode, opos)[0]
            ov = struct.unpack_from("<I", ocode, opos)[0]
            new_mid = 16 <= nv < len(ntext) and nv not in nstarts
            old_ok = ov == 0 or ov in ostarts or ov >= len(od) - s10
            if new_mid and old_ok:
                bad_midref += 1
                if len(ex["midref"]) < 8:
                    ex["midref"].append((eid, hex(opos)))
                break

        # 4) dialogo que estaba con texto -> quedo VACIO
        for (oc, op), (nc, npart) in zip(_dlines(od), _dlines(nd)):
            if len(oc) >= 4 and len(npart[2:].split(b"\x00")[0].strip(b" ")) == 0:
                bad_empty += 1
                if len(ex["empty"]) < 8:
                    ex["empty"].append((eid, oc[:18]))
                break

        # 5) FURIGANA que CRECIO -> ❌#9: el runtime de ruby del motor cuelga al AVANZAR
        #    (confirmado en emulador con GROW_INTRO). El dato esta perfecto pero el motor de
        #    ruby se descuadra con el dialogo mas largo. NO crecer lineas con %NF. Robusto:
        #    sumar el tamano de los chunks CON marcadores (en limpio solo se quitan o se
        #    mantienen marcadores -> nuevo<=viejo; si nuevo>viejo, algun chunk con %NF crecio).
        old_fg = sum(len(p) for p in od[s10:].split(b"\x00") if R._MK.search(p))
        new_fg = sum(len(p) for p in ntext.split(b"\x00") if R._MK.search(p))
        if new_fg > old_fg:
            bad_growfg += 1
            if len(ex["growfg"]) < 8:
                ex["growfg"].append(eid)

        # 6) desbalance furigana EMPEORADO (mas marcadores huerfanos que el original)
        oi, ni = _imbalance(od), _imbalance(nd)
        if ni > oi and ni > 0:
            worse_imb += 1
            if len(ex["imb"]) < 8:
                ex["imb"].append((eid, oi, ni))

    fails = bad_operand + bad_midref + bad_empty + bad_struct + bad_growfg
    print(f"== {game} == {n_mod} eventos modificados")
    print(f"   [{'FALLO' if bad_operand else ' OK  '}] operandos numericos corrompidos: {bad_operand}"
          + (f"  {ex['operand']}" if ex['operand'] else ""))
    print(f"   [{'FALLO' if bad_midref else ' OK  '}] refs string a media cadena (nuevas): {bad_midref}"
          + (f"  {ex['midref']}" if ex['midref'] else ""))
    print(f"   [{'FALLO' if bad_empty else ' OK  '}] dialogo con texto -> VACIO: {bad_empty}"
          + (f"  {ex['empty']}" if ex['empty'] else ""))
    print(f"   [{'FALLO' if bad_struct else ' OK  '}] estructura SSD invalida: {bad_struct}"
          + (f"  {ex['struct']}" if ex['struct'] else ""))
    print(f"   [{'FALLO' if bad_growfg else ' OK  '}] lineas de furigana que crecieron (❌#9 cuelga al avanzar): {bad_growfg}"
          + (f"  {ex['growfg']}" if ex['growfg'] else ""))
    print(f"   [{'aviso' if worse_imb else ' OK  '}] furigana mas desbalanceado que el original: {worse_imb}"
          + (f"  {ex['imb']}" if ex['imb'] else ""))
    return fails == 0


def run(games=("game1", "game2")):
    """Valida los juegos dados. Devuelve True si TODO OK. Llamable desde el build."""
    ok = True
    for g in games:
        if not os.path.exists(os.path.join(REPO, "work", "eve_var", f"{g}.pkb")):
            print(f"== {g} == (sin work/eve_var/{g}.pkb, salta)"); continue
        ok = validate(g) and ok
    print()
    print("RESULTADO:", "TODO OK ✅" if ok else "HAY FALLOS ❌")
    return ok


def main():
    games = [g for g in SUF if g in sys.argv] or ["game1", "game2"]
    sys.exit(0 if run(games) else 1)


if __name__ == "__main__":
    main()
