#!/usr/bin/env python3
"""Parser del paquete de scripts de evento Level-5 "PackNum" (eve.pkb + eve.pkh).

FORMATO RESUELTO del indice (.pkh):
  - 16 bytes: cabecera ASCII "PackNum YYYYMMDD"
  - +0x10 u32: tamaño total del .pkh
  - +0x30 en adelante: tabla de entradas de 12 bytes c/u:
        u32 event_id   (p.ej. 10010001 = mapa/capitulo 1001, evento 0001)
        u32 offset      (en el .pkb)
        u32 size
  Los offsets cubren el .pkb completo (verificado).

Cada entrada del .pkb es un SCRIPT DE EVENTO COMPILADO (bytecode) con el texto del
dialogo EMBEBIDO como operandos, usando plantillas tipo printf (`%s`, `\n`, `%2F`,
`$`) y codigos de control de 1 byte entrelazados con el Shift-JIS. Por eso el texto
no se extrae 100% limpio sin un parser del bytecode (PENDIENTE: catalogar los
codigos de control). Este modulo resuelve el INDICE y da un volcado best-effort.

Uso:
    python tools/pkb_unpack.py <pkh> <pkb> --list
    python tools/pkb_unpack.py <pkh> <pkb> --extract-dir work/eve_entries
    python tools/pkb_unpack.py <pkh> <pkb> --text work/eve_text.csv [--enc sjis|nds]
"""
import argparse
import csv
import os
import struct
import sys

sys.path.insert(0, "tools")
try:
    from build_glossary import NDS_DEC
except Exception:
    NDS_DEC = {}


def parse_index(pkh):
    assert pkh[:7] == b"PackNum", "no es un .pkh PackNum"
    n = (len(pkh) - 0x30) // 12
    out = []
    for i in range(n):
        eid, off, size = struct.unpack_from("<III", pkh, 0x30 + i * 12)
        out.append((eid, off, size))
    return out


import re as _re

# Codigos de escape de texto (printf + furigana/ruby) que aparecen como "%XX".
# %s/%d = sustitucion (nombre/numero); %1F/%2F/%3F = marcadores de furigana.
_PCODE = _re.compile(rb"%[0-9A-Za-z]{1,2}")


def dialogue_runs(data, enc="sjis", minhira=3):
    """[BEST-EFFORT] Extrae lineas de dialogo de un script de evento.

    El texto va in-band con codigos de control de longitud variable (0x1C, 0x1F...)
    y escapes %XX entremezclados con el Shift-JIS. Esto tokeniza los %XX como {..},
    ignora separadores suaves (NUL/TAB/LF) y corta en >=2 bytes binarios. Filtra por
    nº de hiragana para descartar basura del bytecode. NO es 100% limpio en bordes:
    para extraccion/​reinsercion exacta falta la tabla de codigos (issue #3).
    """
    lines, cur, binrun, i = [], [], 0, 0

    def pair(j):
        return (j + 1 < len(data)
                and (0x81 <= data[j] <= 0x9F or 0xE0 <= data[j] <= 0xFC)
                and 0x40 <= data[j + 1] <= 0xFC and data[j + 1] != 0x7F)

    def flush():
        s = "".join(cur).strip()
        if enc == "sjis" and sum(1 for c in s if 0x3040 <= ord(c) <= 0x309F) >= minhira:
            lines.append(s)
        elif enc == "nds" and sum(ch.isalpha() for ch in s) >= 6 and s.count(" ") >= 1:
            lines.append(s)

    while i < len(data):
        b = data[i]
        if enc == "sjis" and pair(i):
            cur.append(data[i:i + 2].decode("shift-jis", "replace")); i += 2; binrun = 0; continue
        if b == 0x25 and i + 1 < len(data):
            m = _PCODE.match(data[i:i + 4]); tok = m.group().decode() if m else "%"
            cur.append("{" + tok + "}"); i += len(tok); binrun = 0; continue
        if 0x20 <= b < 0x7F:
            cur.append(NDS_DEC.get(b, chr(b)) if enc == "nds" else chr(b)); i += 1; binrun = 0; continue
        if enc == "nds" and b in NDS_DEC:
            cur.append(NDS_DEC[b]); i += 1; binrun = 0; continue
        if b in (0x00, 0x09, 0x0A):
            i += 1; continue
        binrun += 1; i += 1
        if binrun >= 2:
            flush(); cur = []; binrun = 0
    flush()
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkh"); ap.add_argument("pkb")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--extract-dir")
    ap.add_argument("--text")
    ap.add_argument("--enc", choices=["sjis", "nds"], default="sjis")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    pkh = open(args.pkh, "rb").read()
    pkb = open(args.pkb, "rb").read()
    idx = parse_index(pkh)
    print(f"{os.path.basename(args.pkb)}: {len(idx)} entradas (event scripts), "
          f"pkb={len(pkb)} B")

    if args.list:
        for eid, off, size in idx[:40]:
            print(f"  id={eid:>9}  off={off:>9}  size={size}")
        if len(idx) > 40:
            print(f"  ... (+{len(idx)-40})")

    if args.extract_dir:
        os.makedirs(args.extract_dir, exist_ok=True)
        for eid, off, size in idx:
            open(os.path.join(args.extract_dir, f"{eid}.evt"), "wb").write(pkb[off:off + size])
        print(f"Extraidas {len(idx)} entradas en {args.extract_dir}")

    if args.text:
        rows = []
        for eid, off, size in idx:
            for run in dialogue_runs(pkb[off:off + size], args.enc):
                rows.append([eid, run])
        with open(args.text, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["event_id", "texto_best_effort"]); w.writerows(rows)
        print(f"Volcado best-effort: {len(rows)} fragmentos -> {args.text}")
        print("AVISO: fragmentado por codigos de control (ver issue #3).")


if __name__ == "__main__":
    main()
