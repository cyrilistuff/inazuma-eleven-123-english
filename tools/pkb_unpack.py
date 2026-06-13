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


def lz10_decompress(data):
    """Descompresion LZ10 estandar de Nintendo (cabecera 0x10 + tamaño 24-bit LE).

    Cada entrada del .pkb va comprimida asi (descubierto via Kuriimu/GBAtemp). Tras
    descomprimir, el contenido son cadenas Shift-JIS separadas por NUL (dialogo +
    lecturas furigana), con escapes %s/%d y marcadores furigana %1F/%2F/%3F.
    """
    if not data or data[0] != 0x10:
        return data  # no comprimido
    size = data[1] | (data[2] << 8) | (data[3] << 16)
    out = bytearray()
    p = 4
    while len(out) < size and p < len(data):
        flags = data[p]; p += 1
        for bit in range(8):
            if len(out) >= size or p >= len(data):
                break
            if flags & (0x80 >> bit):
                b1, b2 = data[p], data[p + 1]; p += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[p]); p += 1
    return bytes(out)


def entry_data(pkb, off, size):
    """Devuelve el contenido descomprimido de una entrada del .pkb."""
    return lz10_decompress(pkb[off:off + size])


def _decode_string(part, enc):
    """Decodifica una cadena (entre NUL) ya descomprimida, limpiando controles."""
    if enc == "sjis":
        s = part.decode("shift-jis", "replace")
        # quitar controles sueltos (<0x20) salvo nada; conservar texto, %codes, \n literal
        s = "".join(c for c in s if ord(c) >= 0x20 or c == "\n")
        return s.strip()
    out = []
    for c in part:
        if c == 0x0A:
            out.append(" ")
        elif 0x20 <= c < 0x7F:
            out.append(chr(c))
        elif c in NDS_DEC:
            out.append(NDS_DEC[c])
    return " ".join("".join(out).split()).strip()


def is_furigana(s):
    """Una lectura furigana = cadena corta solo de hiragana/katakana."""
    core = [c for c in s if c not in " 　"]
    return bool(core) and all(0x3040 <= ord(c) <= 0x30FF for c in core)


def dialogue_runs(data, enc="sjis"):
    """Extrae las lineas de texto de un script de evento (descomprime LZ10 primero).

    Tras descomprimir, el contenido son cadenas separadas por NUL. Se devuelven las
    que contienen texto real (Shift-JIS con kana/kanji, o ES con letras). Las lecturas
    furigana (solo hiragana, cortas) se incluyen pero pueden filtrarse con is_furigana.
    """
    data = lz10_decompress(data)
    out = []
    for part in data.split(b"\x00"):
        if len(part) < 2:
            continue
        s = _decode_string(part, enc)
        if not s or s.count("�") > len(s) * 0.2:
            continue
        if enc == "sjis":
            # texto real: >=2 kana/kanji de ancho completo (descarta basura binaria)
            jp = sum(1 for c in s if 0x3040 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF)
            if jp >= 2:
                out.append(s)
        else:
            if sum(ch.isalpha() for ch in s) >= 3 and " " in s.strip():
                out.append(s)
    return out


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
