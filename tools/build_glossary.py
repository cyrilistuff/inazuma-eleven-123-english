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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(REPO, "work", "fa_extract", "inazuma1", "data_iz", "logic")   # 3DS JP
ES = os.path.join(REPO, "work", "ie1_es", "data_iz", "logic", "sp")             # NDS ES
OUT = os.path.join(REPO, "translation", "glossary")

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
    print("Generando glosario juego 1 (JP 3DS <-> ES NDS oficial)...")
    total = 0
    total += pair_dat("unitbase.dat", 96, 96, "jugadores.csv",
                      ["idx", "japones", "espanol_oficial"])
    total += pair_dat("teamtitle.dat", 16, 16, "titulos_equipo.csv",
                      ["idx", "japones", "espanol_oficial"])
    # NOTA: objetos (item.dat) y tecnicas (command.STR) PENDIENTES: el orden de
    # registros NO coincide 1:1 entre 3DS y NDS (estructura/recuento distintos).
    # Requieren parsear el indice real antes de emparejar de forma fiable.
    # Menus: games.STR por indice
    jp = strings_from_str(os.path.join(DS, "games.STR"), dec_jp)
    es = strings_from_str(os.path.join(ES, "games.STR"), dec_es)
    if len(jp) == len(es):
        rows = [[i, jp[i], es[i]] for i in range(len(jp)) if clean(es[i])]
        write_csv("menus.csv", ["idx", "japones", "espanol_oficial"], rows)
        total += len(rows)
    else:
        print(f"  menus.csv: OMITIDO (recuentos distintos {len(jp)} vs {len(es)})")
    print(f"TOTAL: {total} parejas exactas")


if __name__ == "__main__":
    main()
