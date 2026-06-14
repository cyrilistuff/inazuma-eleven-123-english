"""Fusiona las traducciones del workflow (work/tr_out/NNN.json, arrays ordenados)
en translation/<game>/dialogo.csv: rellena es_final de las filas pendientes cuyo
japones coincida, marcando estado='auto-ia'. Valida formato y reporta problemas.
Uso: python tools/tr_merge.py [game1]"""
import csv, json, os, sys, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
game = sys.argv[1] if len(sys.argv) > 1 else "game1"
in_dir = os.path.join(REPO, "work", "tr_in")
out_dir = os.path.join(REPO, "work", "tr_out")
MK = re.compile(r"%[1-9]F")

jp2es = {}
nb = len([f for f in os.listdir(in_dir) if f.endswith(".json")])
bad_batches, len_mismatch, mk_left, ff_mismatch = [], 0, 0, 0
for i in range(nb):
    N = f"{i:03d}.json"
    pin = os.path.join(in_dir, N); pout = os.path.join(out_dir, N)
    if not os.path.exists(pout):
        bad_batches.append(N + " (sin salida)"); continue
    src = json.load(open(pin, encoding="utf-8"))
    try:
        dst = json.load(open(pout, encoding="utf-8"))
    except Exception as e:
        bad_batches.append(f"{N} (JSON invalido: {e})"); continue
    # admite array posicional (mismo largo) o dict indexado {"0":"es",...}
    pairs_iter = []
    if isinstance(dst, dict):
        for k, es in dst.items():
            try:
                idx = int(k)
            except Exception:
                continue
            if 0 <= idx < len(src):
                pairs_iter.append((src[idx], es))
    elif isinstance(dst, list) and len(dst) == len(src):
        pairs_iter = list(zip(src, dst))
    else:
        bad_batches.append(f"{N} (longitud {len(dst) if isinstance(dst,(list,dict)) else '?'} != {len(src)})")
        len_mismatch += 1; continue
    for jp, es in pairs_iter:
        if not isinstance(es, str) or not es.strip():
            continue
        if MK.search(es):
            mk_left += 1
            es = MK.sub("", es)            # quitar furigana residual (el pipeline la reinyecta)
        if jp.count("\\f") != es.count("\\f"):
            ff_mismatch += 1
        jp2es[jp] = es.strip()

# volcar al CSV
path = os.path.join(REPO, "translation", game, "dialogo.csv")
rows = list(csv.DictReader(open(path, encoding="utf-8")))
cols = rows[0].keys()
filled = 0
for r in rows:
    if (r["estado"] == "pendiente" or not r["es_final"]) and r["japones"] in jp2es:
        r["es_final"] = jp2es[r["japones"]]
        r["estado"] = "auto-ia"
        filled += 1
w = csv.DictWriter(open(path, "w", encoding="utf-8", newline=""), fieldnames=list(cols))
w.writeheader(); w.writerows(rows)

print(f"lotes={nb}  con_traduccion={len(jp2es)} japones unicos")
print(f"FILAS rellenadas en CSV: {filled}")
print(f"avisos: marcadores %NF sin quitar={mk_left}  \\f descuadrado={ff_mismatch}  long_mismatch={len_mismatch}")
if bad_batches:
    print(f"LOTES con problemas ({len(bad_batches)}):")
    for b in bad_batches[:30]:
        print("   " + b)
