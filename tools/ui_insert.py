#!/usr/bin/env python3
"""[Etapa UI] Inserta el glosario (menus, jugadores, equipos) en la ROM.

Parchea, dentro de work/archive_es.fa (el que ya tiene eventos+fuentes), los
ficheros de UI - IN-PLACE, mismo tamano - con el espanol oficial:
  - data_iz/logic/games.STR    : menus (cadenas NUL Shift-JIS)  <- menus.csv
  - data_iz/logic/unitbase.dat : nombres jugador (reg 96B, @+0 16B) <- jugadores.csv
  - data_iz/logic/teamtitle.dat: titulos equipo (reg 16B, @+0)    <- titulos_equipo.csv

Acentos via mapeo griego->SJIS (la fuente ya tiene los glifos). Mismo tamano de
campo (relleno/recorte) -> no cambia offsets. Aplica a inazuma1 e inazuma2.
"""
import csv
import os
import struct
import sys

sys.path.insert(0, "tools")
from fa_unpack import FaArchive
from reinsert import es_encode, GREEK
from lz10 import decompress, compress

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARC = os.path.join(REPO, "work", "archive_es.fa")
GAMES = [("inazuma1", "game1"), ("inazuma2", "game2")]


def load_csv(game, name):
    """Devuelve filas (idx, japones, es) del glosario, o []."""
    # el glosario actual (jugadores/menus/equipos) es del juego 1, en glossary/
    if game == "game1":
        p = os.path.join(REPO, "translation", "glossary", name)
    else:
        p = os.path.join(REPO, "translation", game, "glossary", name)
    if not os.path.exists(p):
        return []
    out = []
    for r in csv.DictReader(open(p, encoding="utf-8")):
        es = r.get("espanol_oficial") or r.get("es_final") or ""
        out.append((int(r["idx"]), r["japones"], es))
    return out


def get_raw(data, off, size):
    """Contenido (descomprime si es LZ10) y flag de si estaba comprimido."""
    blk = bytes(data[off:off + size])
    if blk[:1] == b"\x10":
        return bytearray(decompress(blk)), True
    return bytearray(blk), False


def put_raw(data, off, size, content, was_comp):
    if was_comp:
        comp = compress(bytes(content))
        if len(comp) > size:
            return False
        data[off:off + size] = comp + b"\x00" * (size - len(comp))
    else:
        if len(content) != size:
            return False
        data[off:off + size] = content
    return True


def patch_str(data, off, size, pairs):
    """games.STR: reemplaza cadenas NUL por su ES (match por japones), mismo tamano."""
    content, wc = get_raw(data, off, size)
    es_by_jp = {jp: es for _, jp, es in pairs if es}
    parts = content.split(b"\x00")
    n = 0
    for i, part in enumerate(parts):
        if len(part) < 2:
            continue
        # mismo transform que build_glossary.strings_from_str (dec_jp): strip()
        jp = part.decode("shift-jis", "replace").strip()
        es = es_by_jp.get(jp)
        if not es:
            continue
        body = es_encode(es, len(part))
        parts[i] = body + b" " * (len(part) - len(body))
        n += 1
    if n:
        put_raw(data, off, size, b"\x00".join(parts), wc)
    return n


def patch_records(data, off, size, pairs, stride, namelen):
    """unitbase/teamtitle: nombre inline @+0, mismo tamano de campo, por indice."""
    content, wc = get_raw(data, off, size)
    n = 0
    for idx, jp, es in pairs:
        if not es:
            continue
        rec = idx * stride
        if rec + namelen > len(content):
            continue
        cur = bytes(content[rec:rec + namelen]).split(b"\x00")[0].decode("shift-jis", "replace")
        if cur != jp:                      # seguridad: el registro debe coincidir
            continue
        body = es_encode(es, namelen)
        content[rec:rec + namelen] = body + b"\x00" * (namelen - len(body))
        n += 1
    if n:
        put_raw(data, off, size, content, wc)
    return n


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = bytearray(open(ARC, "rb").read())
    arc = FaArchive(os.path.join(REPO, "work", "romfs", "archive.fa"))
    idx = {p: (o, s) for p, o, s in arc.entries}

    def find(folder, rel):
        key = f"{folder}/data_iz/logic/{rel}"
        for p, (o, s) in idx.items():
            if p.endswith(key):
                return o, s
        return None

    # menus: el juego 1 tiene el set canonico; se aplica a ambos por match de japones
    menus_g1 = load_csv("game1", "menus.csv")
    for folder, game in GAMES:
        menus = load_csv(game, "menus.csv") or menus_g1
        jug = load_csv(game, "jugadores.csv")
        teams = load_csv(game, "titulos_equipo.csv")
        res = []
        f = find(folder, "games.STR")
        if f and menus:
            res.append(("menus", patch_str(data, f[0], f[1], menus)))
        f = find(folder, "unitbase.dat")
        if f and jug:
            res.append(("jugadores", patch_records(data, f[0], f[1], jug, 96, 16)))
        f = find(folder, "teamtitle.dat")
        if f and teams:
            res.append(("equipos", patch_records(data, f[0], f[1], teams, 16, 16)))
        if res:
            print(f"{game}: " + ", ".join(f"{k}={v}" for k, v in res))

    open(ARC, "wb").write(data)
    print(f"-> {ARC} (UI insertada, mismo tamano = {len(data)})")


if __name__ == "__main__":
    main()
