#!/usr/bin/env python3
"""Audita el volcado de diálogo NDS -> 3DS emparejando por ID DE CADENA (exacto).

El evento 3DS (eve.pkb, SSD) y el texto NDS (script/sp/evet.pkb) comparten los MISMOS
IDs de cadena dentro de cada evento:
  - NDS evet: u32 tamaño + entradas {id u16, tipo u16, longitud u32 (incluye cabecera)} + cadena
  - 3DS eve : la cabecera SSD apunta (u32@+16) a la sección de datos; 32 B después empiezan
              entradas {id u16, tipo u8, longitud u8 (incluye cabecera)} + cadena
  - tipo 1 = frase; tipos 2..4 = lecturas furigana del mismo id (se ignoran)

`tools/ds_official.py` NO usaba estos IDs: alineaba por orden con difflib, y en eventos sin
frases repetidas eso equivale a emparejar por posición. Una línea de más o de menos en la NDS
desplaza todas las siguientes. Este script mide cuánto de eso llegó a los CSV.

Salida (work/, gitignored: contiene texto oficial):
  work/audit_dialogo/pares_por_id.csv     event_id, string_id, japones, es_nds
  work/audit_dialogo/desalineados.csv     filas de dialogo_oficial.csv que NO coinciden con el id
  work/audit_dialogo/build_vs_nds.csv     filas de dialogo.csv cuyo es_final contradice al id
  work/audit_dialogo/resumen.json

Uso: python tools/audit_dialogo_ids.py
"""
import csv
import collections
import difflib
import json
import os
import re
import struct
import sys

sys.path.insert(0, "tools")
import ds_official as D   # noqa: E402
import reinsert as R      # noqa: E402
import pkb_unpack as P    # noqa: E402

REPO = R.REPO
OUT = os.path.join(REPO, "work", "audit_dialogo")


def tabla_nds(buf):
    """{id: (tipo, bytes)} con la primera entrada de cada id (NDS)."""
    out, p = {}, 4
    while p + 8 <= len(buf):
        sid, typ, ln = struct.unpack_from("<HHI", buf, p)
        if ln < 8 or p + ln > len(buf):
            break
        out.setdefault(sid, (typ, buf[p + 8:p + ln].split(b"\0")[0]))
        p += ln
    return out


def tabla_3ds(buf):
    """{id: (tipo, bytes, clave_antigua)} con la primera entrada de cada id (3DS).

    La cadena de entradas empieza 32 B después del puntero de la cabecera SSD. En el 3DS
    las lecturas furigana repiten el id de su frase: nos quedamos con la primera entrada.
    `clave_antigua` reproduce la clave que usaba ds_official.py: partía el evento por NUL y
    decodificaba el trozo ENTERO (byte de tipo + byte de longitud + texto)."""
    if buf[:4] != b"SSD\0":
        return None
    off = struct.unpack_from("<I", buf, 16)[0]
    p = off + 32
    out = {}
    while p + 4 <= len(buf):
        sid, typ, ln = struct.unpack_from("<HBB", buf, p)
        if ln < 4 or p + ln > len(buf):
            break
        if sid not in out:
            frase = buf[p + 4:p + ln].split(b"\0")[0]
            ini = buf.rfind(b"\0", 0, p + 2) + 1
            fin = buf.find(b"\0", p + 4)
            trozo = buf[ini:fin if fin >= 0 else len(buf)]
            clave = P._decode_string(trozo, "sjis") if trozo[:1] == b"\x01" else None
            out[sid] = (typ, frase, clave)
        p += ln
    return out


def emparejar(a, b):
    """Empareja ids 3DS -> ids NDS. Los ids son posiciones en el bytecode: la NDS puede
    llevar instrucciones de más que desplazan los ids siguientes, pero el PATRÓN DE SALTOS
    entre ids consecutivos se conserva. Se alinea esa secuencia de saltos con difflib y se
    valida con anclas ASCII (nombres de archivo, variables) que deben ser idénticas."""
    ia, ib = sorted(a), sorted(b)
    if not ia or not ib:
        return {}, 0, 0
    ga = [ia[0]] + [y - x for x, y in zip(ia, ia[1:])]
    gb = [ib[0]] + [y - x for x, y in zip(ib, ib[1:])]
    sm = difflib.SequenceMatcher(None, ga, gb, autojunk=False)
    m = {}
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            m[ia[i + k]] = ib[j + k]
    # un bloque de saltos iguales también fija el id anterior al primer salto
    for i, j, n in sm.get_matching_blocks():
        if n and i > 0 and j > 0:
            m.setdefault(ia[i - 1], ib[j - 1])
    anclas_ok = anclas_mal = 0
    for s3, sn in m.items():
        t3, b3 = a[s3][0], a[s3][1]
        tn, bn = b[sn]
        if b3 and all(32 <= c < 127 for c in b3) and b3 == bn:
            anclas_ok += 1
        elif b3 and all(32 <= c < 127 for c in b3) and all(32 <= c < 127 for c in bn) and b3 != bn:
            anclas_mal += 1
    return m, anclas_ok, anclas_mal


FURI = re.compile(r"%[123]F")


def limpio(s):
    """Normaliza para comparar: sin marcas de furigana ni espacios sobrantes."""
    return re.sub(r"\s+", " ", FURI.sub("", s)).strip()


def parecido(a, b):
    return difflib.SequenceMatcher(None, limpio(a), limpio(b), autojunk=False).ratio()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    t3 = D.load_3ds_events("game1")
    ds = D.load_ds_events("game1")
    comunes = sorted(set(t3) & set(ds))

    pares = {}                     # (eid, sid) -> (jp, es)
    por_jp = collections.defaultdict(set)   # (eid, jp) -> {es posibles por id}
    sin_parse = []
    solo_3ds = 0
    anclas = [0, 0]
    desplazados = 0
    ph_mal = 0
    for eid in comunes:
        a = tabla_3ds(t3[eid])
        if a is None:
            sin_parse.append(eid)
            continue
        b = tabla_nds(ds[eid])
        m, ok_a, mal_a = emparejar(a, b)
        anclas[0] += ok_a
        anclas[1] += mal_a
        if any(sn != s3 for s3, sn in m.items()):
            desplazados += 1
        for sid, (typ, jb, clave) in a.items():
            jp = jb.decode("cp932", "replace")
            if not R.looks_like_dialogue(jp):
                continue
            sn = m.get(sid)
            if sn is None or b[sn][0] != 1:
                solo_3ds += 1
                continue
            es = D.decode_ds(b[sn][1])
            if (jp.count("%s"), jp.count("%d")) != (es.count("%s"), es.count("%d")):
                ph_mal += 1
            pares[(eid, sid)] = (jp, es)
            for k in {jp, P._decode_string(jb, "sjis"), clave}:
                if k:
                    por_jp[(eid, k)].add(es)

    with open(os.path.join(OUT, "pares_por_id.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "string_id", "japones", "es_nds"])
        for (eid, sid), (jp, es) in sorted(pares.items()):
            w.writerow([eid, sid, jp, es])

    # 1) dialogo_oficial.csv frente al emparejado exacto
    of_total = of_ok = of_mal = of_ambiguo = of_sin_ref = 0
    malos = []
    with open(os.path.join(REPO, "translation", "game1", "dialogo_oficial.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            of_total += 1
            key = (int(row["event_id"]), row["japones"])
            cand = por_jp.get(key)
            if not cand:
                of_sin_ref += 1
                continue
            if row["es_oficial"] in cand:
                if len(cand) > 1:
                    of_ambiguo += 1
                of_ok += 1
            else:
                of_mal += 1
                correcto = sorted(cand)[0]
                malos.append([row["event_id"], row["japones"], row["es_oficial"], correcto,
                              round(parecido(row["es_oficial"], correcto), 2)])
    with open(os.path.join(OUT, "desalineados.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "japones", "es_en_csv", "es_correcto_por_id", "parecido"])
        w.writerows(malos)

    # 2) dialogo.csv (lo que usa la build) frente al emparejado exacto
    b_total = b_con_ref = b_igual = b_editado = b_contradice = 0
    contradice = []
    with open(os.path.join(REPO, "translation", "game1", "dialogo.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            b_total += 1
            cand = por_jp.get((int(row["event_id"]), row["japones"]))
            if not cand:
                continue
            b_con_ref += 1
            fin = row["es_final"]
            mejor = max(cand, key=lambda c: parecido(fin, c))
            r = parecido(fin, mejor)
            if limpio(fin) == limpio(mejor):
                b_igual += 1
            elif r >= 0.55:
                b_editado += 1
            else:
                b_contradice += 1
                contradice.append([row["event_id"], row["japones"], fin, mejor, round(r, 2),
                                   row.get("estado", "")])
    contradice.sort(key=lambda x: x[4])
    with open(os.path.join(OUT, "build_vs_nds.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "japones", "es_en_build", "es_nds_por_id", "parecido", "estado"])
        w.writerows(contradice)

    resumen = {
        "eventos_comunes": len(comunes),
        "eventos_sin_parsear": len(sin_parse),
        "pares_exactos_por_id": len(pares),
        "frases_3ds_sin_equivalente_nds": solo_3ds,
        "eventos_con_ids_desplazados": desplazados,
        "anclas_ascii_identicas": anclas[0],
        "anclas_ascii_distintas": anclas[1],
        "pares_con_placeholders_distintos": ph_mal,
        "dialogo_oficial_csv": {"filas": of_total, "coinciden_con_id": of_ok,
                                "NO_coinciden_desalineadas": of_mal,
                                "sin_referencia": of_sin_ref, "ambiguas_mismo_jp": of_ambiguo},
        "dialogo_csv_build": {"filas": of_total and b_total, "con_referencia_nds": b_con_ref,
                              "identicas_a_nds": b_igual, "editadas_parecidas": b_editado,
                              "contradicen_a_nds": b_contradice},
    }
    json.dump(resumen, open(os.path.join(OUT, "resumen.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    if sin_parse:
        print("eventos sin parsear (primeros):", sin_parse[:10])


if __name__ == "__main__":
    main()
