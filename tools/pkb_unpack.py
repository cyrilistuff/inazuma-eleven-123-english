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


def dialogue_runs(data, enc="sjis", minlen=3):
    """Extrae runs de texto best-effort (los codigos de control rompen runs)."""
    runs, cur, i = [], bytearray(), 0
    while i < len(data):
        b = data[i]
        if enc == "sjis" and (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(data):
            cur += data[i:i + 2]; i += 2; continue
        if 0x20 <= b < 0x7F:
            cur.append(b); i += 1; continue
        if len(cur) >= minlen:
            runs.append(_decode(bytes(cur), enc))
        cur = bytearray(); i += 1
    if len(cur) >= minlen:
        runs.append(_decode(bytes(cur), enc))
    return [r for r in runs if r]


def _decode(b, enc):
    if enc == "sjis":
        try:
            s = b.decode("shift-jis")
        except Exception:
            return ""
        return s if any(0x3040 <= ord(c) <= 0x9FFF for c in s) else ""
    out = []
    for c in b:
        if 0x20 <= c < 0x7F:
            out.append(chr(c))
        elif c in NDS_DEC:
            out.append(NDS_DEC[c])
    s = "".join(out)
    return s if sum(ch.isalpha() for ch in s) >= 3 else ""


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
