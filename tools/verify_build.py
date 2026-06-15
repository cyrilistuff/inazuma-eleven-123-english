#!/usr/bin/env python3
"""Verificacion ESTATICA de la build NO_BLANK/SAME_SIZE (sin parches), para validar los
artefactos ANTES de probar en emulador (ahorra ~15 min por test fallido). Comprueba:

  1. CRO  : work/romfs/cro/ina_main1.cro  ==  .orig   (SKIP_CRO -> sin parche de relocacion)
  2. SISTEMA (SYS_ORIG, eid>=90000000 o DONT_TOUCH): bytes COMPRIMIDOS byte-identicos al ROM
     -> crear-partida/intro fisicamente no puede crashear (es el original).
  3. SAME_SIZE: por cada evento traducido, textSize (@0x14) NO cambia + SSD valido.
  4. NO_BLANK: las lecturas furigana (chunks _is_reading) son byte-identicas al original
     (no se vaciaron) -> no se dispara la ruby 0xABFCC0.
  5. Español presente: hay lineas latinas nuevas (la traduccion entro de verdad).

Uso: python tools/verify_build.py [game1]
"""
import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import reinsert as R
from fa_unpack import FaArchive
from pkb_unpack import parse_index, _decode_string
from lz10 import decompress
import ssd_reinsert
import reinsert_var as RV

REPO = R.REPO
GAME = sys.argv[1] if len(sys.argv) > 1 else "game1"
FOLDER = dict((g, f) for f, g in R.GAMES)[GAME]


def text_chunks(dec):
    """(textSize, [chunks]) del SSD descomprimido."""
    if dec[:4] != b"SSD\x00":
        return None, []
    ts = ssd_reinsert._text_start(dec)
    return struct.unpack_from("<I", dec, 0x14)[0], dec[ts:].split(b"\x00")


def has_latin(chunks):
    for c in chunks:
        if len(c) < 3:
            continue
        s = _decode_string(c, "sjis") if len(c) >= 2 else ""
        if sum(1 for ch in s if "a" <= ch.lower() <= "z") >= 4:
            return True
    return False


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    fails, warns = [], []

    # 1) CRO == .orig
    cro = os.path.join(REPO, "work", "romfs", "cro", "ina_main1.cro")
    orig = cro + ".orig"
    if not os.path.exists(orig):
        warns.append("no existe ina_main1.cro.orig (no puedo comparar el CRO)")
    else:
        a = open(cro, "rb").read(); b = open(orig, "rb").read()
        if a == b:
            print(f"[ OK  ] 1. CRO byte-identico al original ({len(a)} B) -> sin parche de relocacion")
        else:
            d = sum(1 for x, y in zip(a, b) if x != y)
            fails.append(f"CRO DIFIERE del original ({d} bytes / {len(a)}) -> hay parche -> crash 0xAD9E1C")

    # cargar pkb ORIGINAL (de archive.fa restaurado) y NUEVO (eve_var)
    arc = FaArchive(os.path.join(REPO, "work", "romfs", "archive.fa"))
    data = arc.d
    po, ps = R.find_file(arc, f"{FOLDER}/data_iz/script/eve.pkb")
    ho, hs = R.find_file(arc, f"{FOLDER}/data_iz/script/eve.pkh")
    opkb = bytes(data[po:po + ps])
    oidx = {e: (o, s) for e, o, s in parse_index(bytes(data[ho:ho + hs]))}

    npkb = open(os.path.join(REPO, "work", "eve_var", f"{GAME}.pkb"), "rb").read()
    nidx = {e: (o, s) for e, o, s in parse_index(open(os.path.join(REPO, "work", "eve_var", f"{GAME}.pkh"), "rb").read())}

    # 2-5) por evento
    n_sys = sys_bad = 0
    n_tr = ts_bad = struct_bad = read_bad = 0
    n_es = 0
    DONT = RV.DONT_TOUCH
    for eid, (no, ns) in nidx.items():
        if eid not in oidx:
            warns.append(f"eid {eid} nuevo (no estaba en el original)"); continue
        oo, os_ = oidx[eid]
        ocomp = opkb[oo:oo + os_]; ncomp = npkb[no:no + ns]
        is_sys = eid >= 90000000 or eid in DONT
        if is_sys:
            n_sys += 1
            if ocomp != ncomp:
                sys_bad += 1
                if sys_bad <= 5:
                    fails.append(f"SISTEMA eid {eid} NO byte-identico ({len(ocomp)}->{len(ncomp)} comp) -> riesgo crear-partida")
            continue
        # evento de gameplay: si el comprimido difiere, fue traducido -> validar a fondo
        if ocomp == ncomp:
            continue
        n_tr += 1
        odec = decompress(ocomp); ndec = decompress(ncomp)
        ots, ochunks = text_chunks(odec); nts, nchunks = text_chunks(ndec)
        if nts is None:
            struct_bad += 1; fails.append(f"eid {eid}: SSD invalido (sin magic)"); continue
        ok, msg = ssd_reinsert._validate(ndec)
        if not ok:
            struct_bad += 1
            if struct_bad <= 5:
                fails.append(f"eid {eid}: SSD invalido ({msg})")
        if ots != nts:
            ts_bad += 1
            if ts_bad <= 5:
                fails.append(f"eid {eid}: textSize CAMBIO {ots}->{nts} (SAME_SIZE roto)")
        # NO_BLANK: cada lectura del original debe seguir igual en el nuevo (mismo indice)
        if len(ochunks) == len(nchunks):
            for oc, nc in zip(ochunks, nchunks):
                if R._is_reading(oc) and oc != nc:
                    read_bad += 1
                    break
        else:
            warns.append(f"eid {eid}: nº de chunks cambio {len(ochunks)}->{len(nchunks)}")
        if has_latin(nchunks):
            n_es += 1

    print(f"[{'OK ' if sys_bad == 0 else 'FAIL'}] 2. SISTEMA/SYS_ORIG: {n_sys} eventos, {sys_bad} NO byte-identicos")
    print(f"[{'OK ' if ts_bad == 0 else 'FAIL'}] 3. SAME_SIZE (textSize intacto): {n_tr} traducidos, {ts_bad} con textSize cambiado")
    print(f"[{'OK ' if struct_bad == 0 else 'FAIL'}] 3b. SSD estructura valida: {struct_bad} invalidos")
    print(f"[{'OK ' if read_bad == 0 else 'FAIL'}] 4. NO_BLANK (lecturas furigana intactas): {read_bad} eventos con lectura modificada")
    print(f"[{'OK ' if n_es > 0 else 'WARN'}] 5. Español presente: {n_es}/{n_tr} eventos traducidos con texto latino")

    print()
    if fails:
        print("❌ FALLOS:")
        for f in fails[:30]:
            print("   -", f)
    if warns:
        print(f"⚠️  {len(warns)} avisos (primeros 8):")
        for w in warns[:8]:
            print("   -", w)
    print("\nRESULTADO:", "❌ REVISAR (no probar aun)" if fails else "✅ TODO OK — listo para probar en emulador")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
