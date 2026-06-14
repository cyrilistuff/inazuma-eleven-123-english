#!/usr/bin/env python3
"""Pone los NOMBRES oficiales europeos del roster (Mark Evans, Axel Blaze, Nathan Swift...)
en el unitbase.dat del 3DS, tomandolos del unitbase.dat del DS (lanzamiento ES oficial).

unitbase.dat = tabla de registros FIJOS de 96 bytes (cabecera 0..95, registros desde 96).
Campos de nombre por registro (verificado):
  +0  (16B) nombre completo  (3DS: '円堂　守'      | DS: 'Mark Evans')   -> roster/perfil
  +16 (16B) lectura corta    (3DS: 'えんどう'       | DS: vacio)          -> RECUADRO AZUL del hablante
  +32 (16B) nombre dado      (3DS: 'えんどう　まもる' | DS: 'Mark')          -> nombre corto europeo
  +48..96   stats binarios (NO se tocan).
El motor JAPONES del 3DS pinta en el recuadro azul el campo +16; el DS (motor europeo) usa +32.
Por eso ponemos el nombre DADO del DS (+32) en el +16 del 3DS -> el recuadro muestra 'Mark'.

El .dat del DS tiene MISMO tamano (230400B) y misma estructura -> mapeo por posicion de registro.
Reemplazo IN-PLACE (mismo tamano): no hay que mover offsets del archive.fa.
"""
import os, sys
sys.path.insert(0, "tools")
from ds_official import DS_TABLE, decode_ds
import reinsert as R

REC = 96
HEADER = 96
FIELD = 16

# game -> (carpeta DS, sufijo del unitbase.dat 3DS dentro de archive.fa)
GAMES = {
    "game1": ("ie1_es", "inazuma1/data_iz/logic/unitbase.dat"),
    "game2": ("ie2_es", "inazuma2/data_iz/logic/unitbase.dat"),
}


def _field(ds_bytes, size):
    """Decodifica un campo de nombre del DS y lo re-codifica para la fuente del 3DS
    (acentos via es_encode/griego). Rellena/trunca a 'size' bytes."""
    raw = ds_bytes.split(b"\x00")[0]
    if not raw:
        return None
    s = decode_ds(raw)
    e = R.es_encode(s, size)
    return e + b"\x00" * (size - len(e))


def patch_unitbase(orig, ds):
    """Devuelve un unitbase.dat 3DS (mismo tamano) con los nombres europeos del DS."""
    assert len(orig) == len(ds), f"tamanos distintos {len(orig)} != {len(ds)}"
    out = bytearray(orig)
    nrec = (len(orig) - HEADER) // REC
    changed = 0
    for n in range(nrec):
        rec = HEADER + n * REC
        full = ds[rec:rec + FIELD]                  # 'Mark Evans'
        given = ds[rec + 2 * FIELD:rec + 3 * FIELD]  # 'Mark'
        ef = _field(full, FIELD)
        eg = _field(given, FIELD)
        if ef and orig[rec:rec + FIELD].strip(b"\x00"):
            out[rec:rec + FIELD] = ef                       # nombre completo (roster)
        if eg:
            out[rec + FIELD:rec + 2 * FIELD] = eg            # recuadro azul (lectura) <- nombre dado
            out[rec + 2 * FIELD:rec + 3 * FIELD] = eg        # nombre dado
            changed += 1
    return bytes(out), changed


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from fa_unpack import FaArchive
    arc = FaArchive(os.path.join(R.REPO, "work", "romfs", "archive.fa"))
    data = arc.d
    for game, (dsdir, suf) in GAMES.items():
        if game not in sys.argv and len(sys.argv) > 1:
            continue
        off = nxt = None
        for p, o, s in arc.entries:
            if p.endswith(suf):
                off, sz = o, s
        orig = bytes(data[off:off + sz])
        ds = open(os.path.join(R.REPO, "work", dsdir, "data_iz", "logic", "sp", "unitbase.dat"), "rb").read()
        patched, n = patch_unitbase(orig, ds)
        outdir = os.path.join(R.REPO, "work", "roster")
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, f"{game}_unitbase.dat"), "wb").write(patched)
        print(f"{game}: {n} registros con nombre europeo -> work/roster/{game}_unitbase.dat")


if __name__ == "__main__":
    main()
