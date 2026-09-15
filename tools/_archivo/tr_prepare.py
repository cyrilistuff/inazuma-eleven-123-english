"""Prepara la traduccion masiva de pendientes (game1):
- dedup de japones pendientes -> lotes JSON en work/tr_in/NNN.json (lista de strings JP)
- glosario curado (nombres oficiales que SI aparecen en los pendientes) -> work/tr_glossary.txt
Uso: python tools/tr_prepare.py [game1] [batch_size]"""
import csv, json, os, sys, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
game = sys.argv[1] if len(sys.argv) > 1 else "game1"
BS = int(sys.argv[2]) if len(sys.argv) > 2 else 80
gdir = "glossary" if game == "game1" else os.path.join(game, "glossary")

rows = list(csv.DictReader(open(os.path.join(REPO, "translation", game, "dialogo.csv"), encoding="utf-8")))
pend = [r for r in rows if r["estado"] == "pendiente" or not r["es_final"]]
uniq = sorted(set(r["japones"] for r in pend))

in_dir = os.path.join(REPO, "work", "tr_in")
out_dir = os.path.join(REPO, "work", "tr_out")
for d in (in_dir, out_dir):
    os.makedirs(d, exist_ok=True)
for f in os.listdir(in_dir):
    os.remove(os.path.join(in_dir, f))

nb = 0
for i in range(0, len(uniq), BS):
    json.dump(uniq[i:i + BS], open(os.path.join(in_dir, f"{nb:03d}.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    nb += 1

# glosario curado: nombres del glosario que aparecen en los pendientes, por frecuencia
blob = "\n".join(uniq)
gloss = []
def load(name):
    p = os.path.join(REPO, "translation", gdir, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []
pairs = []
for fn in ("jugadores.csv", "titulos_equipo.csv"):
    for r in load(fn):
        jp = (r.get("japones") or "").strip()
        es = (r.get("espanol_oficial") or "").strip()
        if jp and es:
            pairs.append((jp, es))
seen = set()
ranked = []
for jp, es in pairs:
    if jp in seen or len(jp) < 2:
        continue
    seen.add(jp)
    # contar tambien la forma sin espacio (apellido+nombre) y solo apellido
    c = blob.count(jp) + blob.count(jp.replace("　", "")) + blob.count(jp.split("　")[0])
    if c > 0:
        ranked.append((c, jp, es))
ranked.sort(reverse=True)
lines = [f"{jp} = {es}" for _c, jp, es in ranked[:80]]
open(os.path.join(REPO, "work", "tr_glossary.txt"), "w", encoding="utf-8").write("\n".join(lines))

print(f"{game}: {len(pend)} pendientes, {len(uniq)} unicos -> {nb} lotes de {BS}")
print(f"glosario curado: {len(lines)} nombres (de {len(pairs)} del glosario)")
