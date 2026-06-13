#!/usr/bin/env python3
"""Genera el glosario JP(3DS)<->ES(NDS oficial) del juego 1 de Inazuma Eleven.

Empareja por INDICE DE REGISTRO los ficheros de datos del 3DS (japones) con los
del NDS europeo en castellano, que comparten el mismo orden de entidades:

  - Jugadores:  data_iz/logic/unitbase.dat   (registro 96 B, nombre@+0, 16 B)  [ambas plataformas]
  - Objetos:    data_iz/logic/item.dat       (3DS: 16 B/reg, NDS: 48 B/reg, nombre@+0)
  - Equipos:    data_iz/logic/teamtitle.dat  (registro 16 B, nombre@+0)         [ambas]
  - Menus:      data_iz/logic/games.STR      (mismo nº de cadenas, empareja por indice)

El 3DS usa Shift-JIS; el NDS una codificacion Latin propia (ver NDS_DEC).

Uso (rutas por defecto a work/, ignorado por git):
    python tools/build_glossary.py
Salida: CSV en translation/glossary/ (solo nombres/terminos, sin descripciones).
"""
import csv
import os
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# valores por defecto (juego 1); main() los reasigna segun el juego
DS = os.path.join(REPO, "work", "fa_extract", "inazuma1", "data_iz", "logic")   # 3DS JP
ES = os.path.join(REPO, "work", "ie1_es", "data_iz", "logic", "sp")             # NDS ES
OUT = os.path.join(REPO, "translation", "glossary")

# config por juego: (carpeta 3DS, carpeta NDS ES, salida glosario)
GAME_CFG = {
    "game1": ("inazuma1", os.path.join("ie1_es", "data_iz", "logic", "sp"),
              os.path.join("translation", "glossary")),
    "game2": ("inazuma2", os.path.join("ie2_es", "data_iz", "logic", "sp"),
              os.path.join("translation", "game2", "glossary")),
}

# Codificacion Latin propia del NDS ES (inferida por contexto; ampliable)
NDS_DEC = {0xB2: "á", 0xBA: "é", 0xBE: "í", 0xC4: "ó", 0xCA: "ú",
           0xC2: "ñ", 0xCC: "ü", 0xB5: "ä", 0xA5: "¿", 0xDF: "¡", 0xD9: "Í"}


def dec_es(b):
    out = []
    for c in b:
        if c == 0:
            break
        if c in (0x0A, 0x0D):      # salto de linea -> espacio
            out.append(" ")
        elif 0x20 <= c < 0x7F:
            out.append(chr(c))
        elif c in NDS_DEC:
            out.append(NDS_DEC[c])
        else:
            out.append("?")
    return " ".join("".join(out).split()).strip()


def dec_jp(b):
    return b.split(b"\x00")[0].decode("shift-jis", "replace").strip()


def names_from_dat(path, stride, dec, width=16):
    d = open(path, "rb").read()
    return [dec(d[i * stride:i * stride + width]) for i in range(len(d) // stride)]


def strings_from_str(path, dec):
    d = open(path, "rb").read()
    return [dec(p) for p in d.split(b"\x00") if len(p) >= 1]


DUMMY = {"ダミー", "Dummy", "dummy", "-", "ー", "なし"}


def clean(s):
    return (s and any(ch.isalpha() for ch in s)
            and "<" not in s and "?" not in s and s not in DUMMY)


def write_csv(fname, header, rows):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, fname)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {fname}: {len(rows)} entradas -> {p}")


def pair_dat(name, jp_stride, es_stride, fname, header):
    jp = names_from_dat(os.path.join(DS, name), jp_stride, dec_jp)
    es = names_from_dat(os.path.join(ES, name), es_stride, dec_es)
    n = min(len(jp), len(es))
    rows = [[i, jp[i], es[i]] for i in range(n) if clean(jp[i]) and clean(es[i])]
    write_csv(fname, header, rows)
    return len(rows)


def main():
    global DS, ES, OUT
    game = sys.argv[1] if len(sys.argv) > 1 else "game1"
    folder, es_rel, out_rel = GAME_CFG[game]
    DS = os.path.join(REPO, "work", "fa_extract", folder, "data_iz", "logic")
    ES = os.path.join(REPO, "work", *es_rel.split(os.sep))
    OUT = os.path.join(REPO, out_rel)
    print(f"Generando glosario {game} (JP 3DS <-> ES NDS oficial)...")
    total = 0
    total += pair_dat("unitbase.dat", 96, 96, "jugadores.csv",
                      ["idx", "japones", "espanol_oficial"])
    total += pair_dat("teamtitle.dat", 16, 16, "titulos_equipo.csv",
                      ["idx", "japones", "espanol_oficial"])
    # Menus: games.STR por indice (NDS puede tenerlo en sp/ o en logic/)
    es_games = os.path.join(ES, "games.STR")
    if not os.path.exists(es_games):
        es_games = os.path.join(os.path.dirname(ES), "games.STR")
    jp = strings_from_str(os.path.join(DS, "games.STR"), dec_jp)
    es = strings_from_str(es_games, dec_es) if os.path.exists(es_games) else []
    if es and len(jp) == len(es):
        rows = [[i, jp[i], es[i]] for i in range(len(jp)) if clean(es[i])]
        write_csv("menus.csv", ["idx", "japones", "espanol_oficial"], rows)
        total += len(rows)
    else:
        print(f"  menus.csv: OMITIDO (jp={len(jp)} vs es={len(es)})")
    print(f"TOTAL: {total} parejas")


if __name__ == "__main__":
    main()
