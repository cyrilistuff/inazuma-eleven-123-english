#!/usr/bin/env python3
"""[Etapa 6] Anade glifos del espanol a una fuente BCFNT reusando glifos Griegos.

El espanol no usa Griego, y su rango (U+0391..) esta en la CMAP de la fuente y es
alcanzable desde Shift-JIS (0x839F..). Estrategia SIN cambiar tamano:
  - sobrescribir la TEXTURA de ciertos glifos griegos con los caracteres ES
    (compuestos: letra base + acento), y copiar su CWDH del caracter base.
  - el re-encoder emite los codigos SJIS griegos para esos caracteres ES.

Mapeo ES -> codepoint griego reutilizado (y su byte SJIS, ver reinsert.py):
"""
import struct
import sys

sys.path.insert(0, "tools")
from bcfnt import BCFNT

# ES char -> (caracter base existente, tipo de acento, CODEPOINT UNICODE del glifo portador)
#
# CLAVE (bug de los acentos resuelto, verificado renderizando los glifos): la fuente
# guarda cada griega en DOS sitios con glifos DISTINTOS: el rango UNICODE (0x0391..) y el
# rango SJIS (0x839F..). El re-encoder emite bytes SJIS, pero el MOTOR los convierte a
# UNICODE y busca el glifo por el codepoint UNICODE (comprobado: el glifo que pinta para
# 'é'=0x83A0 es el del codepoint Unicode 0x0392, no el del SJIS). -> hay que pintar el
# glifo del codepoint UNICODE. Los 15 griegos MAYUSCULOS Unicode (0x0391-0x039F) estan
# TODOS en el cmap de las 3 fuentes, asi que cubren los 15 acentos (1:1).
PLAN = [
    ("á", "a", "acute", 0x0391), ("é", "e", "acute", 0x0392),
    ("í", "i", "acute", 0x0393), ("ó", "o", "acute", 0x0394),
    ("ú", "u", "acute", 0x0395), ("ü", "u", "diaer", 0x0396),
    ("ñ", "n", "tilde", 0x0397), ("Á", "A", "acute", 0x0398),
    ("É", "E", "acute", 0x0399), ("Í", "I", "acute", 0x039A),
    ("Ó", "O", "acute", 0x039B), ("Ú", "U", "acute", 0x039C),
    ("Ñ", "N", "tilde", 0x039D), ("¡", "!", "vflip", 0x039E),
    ("¿", "?", "vflip", 0x039F),
]


def morton8(x, y):
    d = 0
    for i in range(3):
        d |= ((x >> i) & 1) << (2 * i)
        d |= ((y >> i) & 1) << (2 * i + 1)
    return d


class Font:
    def __init__(self, path):
        self.path = path
        self.b = BCFNT(open(path, "rb").read())
        self.data = bytearray(self.b.d)
        self.t = self.b.tglp()
        self.cmap = {}
        for c in self.b.cmaps():
            self.cmap.update(c["entries"])
        self.PER = self.t["ncols"] * self.t["nrows"]
        self.doff = self.t["sheet_data"]
        # stride real de celda en la hoja (1px de margen): 256/15=17, 128/7=18
        self.sx = self.t["sheet_w"] // self.t["ncols"]
        self.sy = self.t["sheet_h"] // self.t["nrows"]

    def _poff(self, gi, x, y):
        t = self.t
        sheet = gi // self.PER
        cell = gi % self.PER
        ox = (cell % t["ncols"]) * self.sx
        oy = (cell // t["ncols"]) * self.sy
        X, Y = ox + x, oy + y
        tw = t["sheet_w"] // 8
        tile = (Y // 8) * tw + (X // 8)
        return self.doff + sheet * t["sheet_size"] + tile * 64 + morton8(X % 8, Y % 8)

    def read_cell(self, gi):
        t = self.t
        return [[self.data[self._poff(gi, x, y)] for x in range(t["cell_w"])]
                for y in range(t["cell_h"])]

    def write_cell(self, gi, grid):
        t = self.t
        for y in range(t["cell_h"]):
            for x in range(t["cell_w"]):
                self.data[self._poff(gi, x, y)] = grid[y][x]

    def ascii_art(self, gi):
        for row in self.read_cell(gi):
            print("".join("#" if (v & 0xF) >= 8 else "." if (v & 0xF) >= 3 else " " for v in row))

    def cwdh_entry_off(self, gi):
        """Offset absoluto de la entrada CWDH (3 bytes) del glifo gi, o None."""
        o = self.b.cwdh_off
        while o:
            s = o - 8
            start, end = struct.unpack_from("<HH", self.data, s + 8)
            nxt = struct.unpack_from("<I", self.data, s + 12)[0]
            if start <= gi <= end:
                return s + 16 + (gi - start) * 3
            o = nxt
        return None

    def copy_width(self, base_gi, tgt_gi):
        bo = self.cwdh_entry_off(base_gi)
        to = self.cwdh_entry_off(tgt_gi)
        if bo is not None and to is not None:
            self.data[to:to + 3] = self.data[bo:bo + 3]


def ink_bbox(grid):
    ys = [y for y, row in enumerate(grid) for v in row if (v & 0xF) >= 4]
    xs = [x for row in grid for x, v in enumerate(row) if (v & 0xF) >= 4]
    if not xs:
        return 0, 0, len(grid[0]) - 1, len(grid) - 1
    return min(xs), min(ys), max(xs), max(ys)


def add_acute(grid):
    x0, y0, x1, y1 = ink_bbox(grid)
    cx = (x0 + x1) // 2
    top = max(0, y0 - 4)
    for i, (dx, dy) in enumerate([(1, 0), (0, 1), (-1, 2)]):
        gx, gy = cx + dx, top + dy
        if 0 <= gy < len(grid) and 0 <= gx < len(grid[0]):
            grid[gy][gx] = 0xFF
            if gx + 1 < len(grid[0]):
                grid[gy][gx + 1] = 0xFF
    return grid


def add_diaer(grid):
    x0, y0, x1, y1 = ink_bbox(grid)
    top = max(0, y0 - 3)
    for gx in (x0 + 1, x1 - 1):
        if 0 <= top < len(grid):
            grid[top][gx] = 0xFF
    return grid


def add_tilde(grid):
    x0, y0, x1, y1 = ink_bbox(grid)
    top = max(0, y0 - 4)
    pts = [(x0, 1), (x0 + 1, 0), (x0 + 2, 0), (x1 - 2, 1), (x1 - 1, 1), (x1, 0)]
    for dx, dy in pts:
        gy = top + dy
        if 0 <= gy < len(grid) and 0 <= dx < len(grid[0]):
            grid[gy][dx] = 0xFF
    return grid


def vflip(grid):
    return [row[:] for row in grid[::-1]]


def patch_font(path, out):
    f = Font(path)
    base_cw = {}
    cwdh = {}
    for blk in f.b.cwdhs():
        cwdh.update(blk["widths"])
    applied = 0
    for ch, base, acc, cp in PLAN:
        if ord(base) not in f.cmap or cp not in f.cmap:
            print(f"  saltado {ch} (base o cp no en cmap)")
            continue
        bgi = f.cmap[ord(base)]
        tgi = f.cmap[cp]
        grid = f.read_cell(bgi)
        if acc == "acute":
            grid = add_acute(grid)
        elif acc == "diaer":
            grid = add_diaer(grid)
        elif acc == "tilde":
            grid = add_tilde(grid)
        elif acc == "vflip":
            grid = vflip(f.read_cell(bgi))
        f.write_cell(tgi, grid)
        f.copy_width(bgi, tgi)        # ancho del caracter base
        applied += 1
    if out:
        open(out, "wb").write(f.data)
    print(f"{path}: {applied} glifos ES escritos (tamano {len(f.data)})")
    return f


def patch_font_bytes(path):
    """Devuelve los bytes de la fuente con los glifos ES anadidos (mismo tamano)."""
    return bytes(patch_font(path, None).data)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    src = r"work\fa_extract\font\FONT12T.bcfnt"
    out = r"work\FONT12T_es.bcfnt"
    f = patch_font(src, out)
    # verificar: re-leer los glifos griegos reusados
    f2 = Font(out)
    for ch, base, acc, cp in [("á","a","",0x0391), ("ñ","n","",0x0397), ("ü","u","",0x0396), ("¡","!","",0x039E)]:
        print(f"\n=== '{ch}' (glifo griego {cp:#06x}) ===")
        f2.ascii_art(f2.cmap[cp])
