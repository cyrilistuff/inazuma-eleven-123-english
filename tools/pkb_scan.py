#!/usr/bin/env python3
"""[WIP / diagnostico] Escaneo de los paquetes de scripts de evento (.pkb).

El dialogo/historia de Inazuma Eleven vive en `eve.pkb`/`mch.pkb` (cuerpo) +
`*.pkh` (indice), un paquete Level-5 "PackNum". El TEXTO va EMBEBIDO dentro de
SCRIPTS DE EVENTO COMPILADOS (bytecode), entrelazado con operandos binarios, por
lo que NO se puede extraer limpio separando por NUL: las frases salen partidas.

Este script solo SCANEA y muestra fragmentos (para investigar el formato). El
extractor real (parsear el bytecode / la tabla de mensajes) esta PENDIENTE -> ver
issue #3 en GitHub.

  3DS: Shift-JIS    |    NDS (ES): codificacion Latin propia (ver build_glossary.NDS_DEC)

Uso:
    python tools/pkb_scan.py work/fa_extract/inazuma1/data_iz/script/eve.pkb --enc sjis
    python tools/pkb_scan.py work/ie1/fuentes/nds_es/data_iz/script/sp/evet.pkb --enc nds
"""
import argparse
import sys

sys.path.insert(0, "tools")
try:
    from build_glossary import NDS_DEC
except Exception:
    NDS_DEC = {}


def dec_sjis(part):
    try:
        s = part.decode("shift-jis")
    except Exception:
        return ""
    return "".join(c for c in s if ord(c) >= 0x20).strip()


def dec_nds(part):
    out = []
    for c in part:
        if c == 0:
            break
        if 0x20 <= c < 0x7F:
            out.append(chr(c))
        elif c in NDS_DEC:
            out.append(NDS_DEC[c])
    return "".join(out).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkb")
    ap.add_argument("--enc", choices=["sjis", "nds"], default="sjis")
    ap.add_argument("--n", type=int, default=25)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    d = open(args.pkb, "rb").read()
    dec = dec_sjis if args.enc == "sjis" else dec_nds
    print(f"{args.pkb}: {len(d)} bytes (enc={args.enc})")
    print("AVISO: fragmentos sin limpiar; el dialogo va en bytecode (ver issue #3)\n")
    shown = 0
    for part in d.split(b"\x00"):
        if len(part) < 6:
            continue
        s = dec(part)
        if args.enc == "sjis":
            ok = sum(1 for c in s if 0x3040 <= ord(c) <= 0x9FFF) >= 4
        else:
            ok = s.count(" ") >= 2 and sum(c.isalpha() for c in s) >= 8
        if ok:
            print("  |", s[:70])
            shown += 1
            if shown >= args.n:
                break


if __name__ == "__main__":
    main()
