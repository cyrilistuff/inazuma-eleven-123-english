#!/usr/bin/env python3
"""[Etapa 5] Construye la tabla de traduccion editable del juego 1 a partir del
alineado por event_id (work/dialogue/game1_aligned.json de align_events.py).

Salida: translation/game1/dialogo.csv con columnas
    event_id, idx, japones, es_oficial, es_final, estado
- estado="oficial": el evento tiene mismo nº de lineas JP=ES -> es_final = ES oficial
- estado="pendiente": el alineado 1:1 no es seguro -> es_final vacio (a traducir)

Pipeline:
    pkb_unpack/align_events (extraen, requieren ROMs en work/) -> este script.
El CSV resultante SI se versiona (es el producto de traduccion; ver LEGAL.md).
"""
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    src = os.path.join(REPO, "work", "dialogue", "game1_aligned.json")
    data = json.load(open(src, encoding="utf-8"))
    out_dir = os.path.join(REPO, "translation", "game1")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "dialogo.csv")

    rows = []          # traducidas -> se versionan en translation/
    pending = []       # solo JP -> se quedan en work/ (regenerable, no a git)
    ev_ofi = 0
    for ev in sorted(data, key=lambda e: e["event_id"]):
        jp, es = ev["jp"], ev["es_oficial"]
        if jp and len(jp) == len(es):
            ev_ofi += 1
            for i, (j, e) in enumerate(zip(jp, es)):
                rows.append([ev["event_id"], i, j, e, "oficial"])
        else:
            for i, j in enumerate(jp):
                pending.append([ev["event_id"], i, j])

    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "idx", "japones", "es_final", "estado"])
        w.writerows(rows)

    pend_path = os.path.join(REPO, "work", "dialogue", "game1_pending.csv")
    with open(pend_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "idx", "japones"])
        w.writerows(pending)

    ev_total = len({r["event_id"] for r in data if r["jp"]})
    print(f"-> {out}  ({len(rows)} lineas traducidas, {ev_ofi} eventos)")
    print(f"-> {pend_path}  ({len(pending)} lineas JP pendientes, no versionadas)")
    print(f"cobertura: {ev_ofi}/{ev_total} eventos con texto = {100*ev_ofi/ev_total:.1f}%")


if __name__ == "__main__":
    main()
