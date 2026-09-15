#!/usr/bin/env python3
"""Volcado de cadenas de los ficheros de texto de Inazuma Eleven NDS (referencia ES).

Saca runs de texto imprimible de archivos .STR/.dat/.pkb extraidos de las ROMs NDS
oficiales (carpetas data_iz/logic/sp/ y data_iz/script/sp/). Sirve para construir
el glosario de terminologia oficial en castellano (tecnicas, objetos, jugadores).

OJO codificacion: el texto base es ASCII/Latin, pero las vocales acentuadas, la 'ñ'
y los codigos de control (color, nombre, salto) usan BYTES PROPIOS del juego. Este
volcado deja esos bytes como '?'/marcadores; la tabla exacta se mapeara en la fase
de glosario. El contenido extraido tiene copyright -> usar solo como referencia,
no subir los volcados al repo (van a work/, ignorado por git).

Uso:
    python tools/nds_str_dump.py work/ie1/fuentes/nds_es/data_iz/logic/sp/command.STR
    python tools/nds_str_dump.py work/ie1/fuentes/nds_es/data_iz/logic/sp/command.STR -o work/glos/cmd.txt
"""
import argparse
import sys

# bytes Latin-1 imprimibles + acentos comunes que SI aparecen tal cual
PRINTABLE = set(range(0x20, 0x7F))


def extract_strings(data, minlen=3):
    out, cur = [], bytearray()
    for b in data:
        if b in PRINTABLE:
            cur.append(b)
        else:
            if len(cur) >= minlen:
                out.append(cur.decode("latin-1"))
            cur = bytearray()
    if len(cur) >= minlen:
        out.append(cur.decode("latin-1"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("-o", "--out")
    ap.add_argument("--minlen", type=int, default=3)
    args = ap.parse_args()

    data = open(args.file, "rb").read()
    strings = extract_strings(data, args.minlen)
    text = "\n".join(strings)

    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"{len(strings)} cadenas -> {args.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
