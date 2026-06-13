#!/usr/bin/env python3
"""[Etapa 5] Construye la tabla de traduccion editable del juego 1.

Lee el alineado (work/dialogue/game1_aligned.json de align_events.py) y genera
translation/game1/dialogo.csv. Reusa el espanol oficial del NDS al maximo:

  estado:
    oficial   -> evento con nº de lineas JP=ES (emparejado posicional, alta conf.)
    revisar   -> emparejado por Needleman-Wunsch (candidato oficial, revisar a mano)
    auto-dup  -> linea sin par propio, pero IDENTICA a otra ya traducida (reuso)
    pendiente -> sin equivalente oficial -> traducir a mano

El CSV (texto de traduccion) SI se versiona. El japones pendiente en bruto se queda
ademas en work/ (regenerable). Ver LEGAL.md.
"""
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    game = sys.argv[1] if len(sys.argv) > 1 else "game1"
    data = json.load(open(os.path.join(REPO, "work", "dialogue", f"{game}_aligned.json"),
                          encoding="utf-8"))

    # 1) mapa global JP->ES (preferir 'exacto' sobre 'nw')
    gmap = {}
    for ev in data:
        for jp, es in ev["pairs"]:
            if jp not in gmap or ev["conf"] == "exacto":
                gmap[jp] = es

    # 2) filas
    rows = []
    cnt = {"oficial": 0, "revisar": 0, "auto-dup": 0, "pendiente": 0}
    for ev in sorted(data, key=lambda e: e["event_id"]):
        eid = ev["event_id"]
        for jp, es in ev["pairs"]:
            st = "oficial" if ev["conf"] == "exacto" else "revisar"
            rows.append([eid, jp, es, st]); cnt[st] += 1
        for jp in ev["jp_only"]:
            if jp in gmap:
                rows.append([eid, jp, gmap[jp], "auto-dup"]); cnt["auto-dup"] += 1
            else:
                rows.append([eid, jp, "", "pendiente"]); cnt["pendiente"] += 1

    out = os.path.join(REPO, "translation", game, "dialogo.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "japones", "es_final", "estado"])
        w.writerows(rows)

    total = len(rows)
    con_es = total - cnt["pendiente"]
    print(f"-> {out}  ({total} lineas)")
    for k in ("oficial", "revisar", "auto-dup", "pendiente"):
        print(f"  {k:10}: {cnt[k]:6} ({100*cnt[k]/total:.1f}%)")
    print(f"COBERTURA con ES (oficial+revisar+auto-dup): {con_es} = {100*con_es/total:.1f}%")


if __name__ == "__main__":
    main()
