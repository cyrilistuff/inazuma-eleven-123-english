#!/usr/bin/env python3
"""Alinea cadenas de un .STR del 3DS (JP, Shift-JIS) con su equivalente del NDS (ES).

Los .STR de Inazuma son un pool de cadenas separadas por NUL con 32 bytes de cabecera.
El 3DS (heredado de DS) usa Shift-JIS con furigana tipo [kanji/lectura]; el NDS oficial
en castellano usa una codificacion Latin propia (acentos/n con bytes especiales).

OJO: el numero de cadenas puede NO coincidir (p.ej. el NDS intercala nombre+descripcion
y el 3DS solo descripcion) -> el alineado por indice es solo un PUNTO DE PARTIDA. El
alineado exacto requiere el indice del .dat asociado (pendiente).

Salida: CSV (idx, jp, es) en work/ (ignorado por git). NO subir el CSV al repo.

Uso:
    python tools/str_align.py work/fa_extract/inazuma1/data_iz/logic/item.STR \
                              work/ie1_es/data_iz/logic/sp/item.STR -o work/pair_item.csv
"""
import argparse
import csv

# Mapeo PARCIAL de la codificacion Latin propia del NDS ES -> Unicode.
# Inferido por contexto; AMPLIAR a medida que se confirmen mas glifos.
NDS_FIX = {
    "Â": "ñ", "ß": "¡", "º": "é", "Ä": "ó", "²": "á",
}


def read_str(path, enc):
    d = open(path, "rb").read()
    out = []
    for part in d.split(b"\x00"):
        if not part:
            continue
        try:
            out.append(part.decode(enc))
        except Exception:
            out.append("<?>")
    return out


def fix_nds(s):
    for k, v in NDS_FIX.items():
        s = s.replace(k, v)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jp_3ds", help=".STR del 3DS (JP, Shift-JIS)")
    ap.add_argument("es_nds", help=".STR del NDS (ES)")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    jp = read_str(args.jp_3ds, "shift-jis")
    es = [fix_nds(s) for s in read_str(args.es_nds, "latin-1")]

    n = max(len(jp), len(es))
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "jp_3ds", "es_nds_oficial"])
        for i in range(n):
            w.writerow([i, jp[i] if i < len(jp) else "", es[i] if i < len(es) else ""])

    print(f"3DS JP: {len(jp)} cadenas | NDS ES: {len(es)} cadenas")
    print(f"CSV de alineado (revisar manualmente, recuentos pueden diferir): {args.out}")


if __name__ == "__main__":
    main()
