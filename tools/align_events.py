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
    n_jp = n_es = 0
    for eid in common:
        j, e = jp[eid], es[eid]
        if not j and not e:
            continue
        n_jp += len(j); n_es += len(e)
        data.append({"event_id": eid, "jp": j, "es_oficial": e})
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(data, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"eventos con texto: {len(data)}  lineas JP={n_jp} ES={n_es}")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
