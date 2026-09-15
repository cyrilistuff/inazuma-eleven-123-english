"""Emparejado por ID DE CADENA entre el texto NDS (evet.pkb) y los eventos 3DS (eve.pkb, SSD).

El evento 3DS y el texto NDS comparten los MISMOS IDs de cadena dentro de cada evento:
  - NDS evet: u32 tamaño + entradas {id u16, tipo u16, longitud u32 (incluye cabecera)} + cadena
  - 3DS eve : la cabecera SSD apunta (u32@+16) a la sección de datos; 32 B después empiezan
              entradas {id u16, tipo u8, longitud u8 (incluye cabecera)} + cadena
  - tipo 1 = frase; tipos 2..4 = lecturas furigana del mismo id (se ignoran)

Sin E/S.
"""
import difflib
import struct

from ie123kit.nucleo.texto.nds_latin import decode_cadena


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
            clave = decode_cadena(trozo, "sjis") if trozo[:1] == b"\x01" else None
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
