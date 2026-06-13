#!/usr/bin/env python3
"""[Etapa 4] Alinea por event_id el dialogo JP (3DS) con el ES oficial (NDS).

Usa el indice PackNum (event_id) para casar cada evento del 3DS `eve.pkb` con el
del NDS `evet.pkb` (1289 ids comunes). Vuelca, por evento, las lineas JP y las ES
oficiales lado a lado como PUNTO DE PARTIDA para traducir/revisar.

OJO: la extraccion de lineas es best-effort (ver pkb_unpack / issue #3): hay ruido
en los bordes y los recuentos JP/ES por evento no casan 1:1. Esto NO es todavia un
fichero listo para reinsertar; es material de trabajo para el traductor. Sale a
work/ (ignorado por git) porque contiene texto extraido (copyright).

Uso:
    python tools/align_events.py \
        work/fa_extract/inazuma1/data_iz/script/eve.pkh  work/fa_extract/inazuma1/data_iz/script/eve.pkb \
        work/ie1_es/data_iz/script/sp/evet.pkh           work/ie1_es/data_iz/script/sp/evet.pkb \
        -o work/dialogue/game1_aligned.json
"""
import argparse
import json
import os
import struct
import sys

sys.path.insert(0, "tools")
from pkb_unpack import parse_index, dialogue_runs, is_furigana


def _dedup(seq):
    out = []
    for x in seq:
        if not out or out[-1] != x:
            out.append(x)
    return out


def load(pkh_path, pkb_path, enc, drop_furigana=True):
    pkh = open(pkh_path, "rb").read()
    pkb = open(pkb_path, "rb").read()
    out = {}
    for eid, off, size in parse_index(pkh):
        lines = dialogue_runs(pkb[off:off + size], enc)
        if drop_furigana:
            lines = [l for l in lines if not is_furigana(l)]
        out[eid] = _dedup(lines)
    return out


import re as _re

_PC = _re.compile(r"%[0-9A-Za-z]{1,2}")


def _fmt(s):
    return (s.count("%s"), s.count("%d") + s.count("%n"))


def _vlen(s):
    """Longitud 'visual' (sin %codes, \\n ni espacios)."""
    s = _PC.sub("", s).replace("\\n", "")
    return len([c for c in s if c not in " 　"])


def _sim(j, e):
    """Similitud JP-ES (independiente del idioma). None = incompatible.

    Señales: (1) mismo nº de %s/%d (obligatorio); (2) longitud correlacionada
    (ES ~1.6x el JP); (3) nº de saltos \\n parecido.
    """
    if _fmt(j) != _fmt(e):
        return None
    jl, el = _vlen(j), _vlen(e)
    if jl == 0 or el == 0:
        len_score = 1.0 if jl == el else 0.0
    else:
        r = el / jl
        len_score = max(0.0, 1.5 - abs(r - 1.6))     # ~1.5 si r≈1.6
    nl_pen = 0.5 * abs(j.count("\\n") - e.count("\\n"))
    return 0.2 + len_score - nl_pen


def align_lines(jp, es):
    """Needleman-Wunsch: empareja lineas preservando el orden. Devuelve
    (pairs[(jp,es)], jp_only[]). Las JP sin equivalente fiable van a jp_only."""
    n, m = len(jp), len(es)
    GAP, MISS = -1.0, -4.0
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * GAP
    for k in range(1, m + 1):
        dp[0][k] = k * GAP
    for i in range(1, n + 1):
        for k in range(1, m + 1):
            s = _sim(jp[i - 1], es[k - 1])
            diag = dp[i - 1][k - 1] + (s if s is not None else MISS)
            dp[i][k] = max(diag, dp[i - 1][k] + GAP, dp[i][k - 1] + GAP)
    pairs, jp_only = [], []
    i, k = n, m
    while i > 0 and k > 0:
        s = _sim(jp[i - 1], es[k - 1])
        if dp[i][k] == dp[i - 1][k - 1] + (s if s is not None else MISS) and s is not None:
            pairs.append((jp[i - 1], es[k - 1])); i -= 1; k -= 1
        elif dp[i][k] == dp[i - 1][k] + GAP:
            jp_only.append(jp[i - 1]); i -= 1
        else:
            k -= 1
    while i > 0:
        jp_only.append(jp[i - 1]); i -= 1
    pairs.reverse(); jp_only.reverse()
    return pairs, jp_only


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jp_pkh"); ap.add_argument("jp_pkb")
    ap.add_argument("es_pkh"); ap.add_argument("es_pkb")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    jp = load(args.jp_pkh, args.jp_pkb, "sjis")
    es = load(args.es_pkh, args.es_pkb, "nds")
    common = sorted(set(jp) & set(es))
    print(f"eventos: JP={len(jp)} ES={len(es)} comunes={len(common)}")

    data = []
    n_exact = n_nw = n_only = 0
    for eid in common:
        j, e = jp[eid], es[eid]
        if not j:
            continue
        if e and len(j) == len(e):
            pairs = list(zip(j, e)); jp_only = []; conf = "exacto"
            n_exact += len(pairs)
        else:
            pairs, jp_only = align_lines(j, e); conf = "nw"
            n_nw += len(pairs)
        n_only += len(jp_only)
        data.append({"event_id": eid, "conf": conf,
                     "pairs": [[a, b] for a, b in pairs],
                     "jp_only": jp_only})
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(data, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = n_exact + n_nw + n_only
    print(f"eventos con texto: {len(data)}")
    print(f"lineas JP: {tot}")
    print(f"  emparejadas EXACTO (alta confianza): {n_exact} ({100*n_exact/tot:.1f}%)")
    print(f"  emparejadas NW    (revisar):         {n_nw} ({100*n_nw/tot:.1f}%)")
    print(f"  sin equivalente (a traducir):        {n_only} ({100*n_only/tot:.1f}%)")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
