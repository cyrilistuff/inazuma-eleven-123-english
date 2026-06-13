#!/usr/bin/env python3
"""Parser del formato de fuente BCFNT (CFNT v3) de Nintendo 3DS.

Lee cabecera + bloques FINF / TGLP / CWDH / CMAP. Sirve para inspeccionar la
fuente del juego (FONT12T.bcfnt) y, despues, anadir glifos del espanol (etapa 6).
Los offsets internos apuntan al CUERPO del bloque (block_start + 8).
"""
import struct
import sys


class BCFNT:
    def __init__(self, data):
        self.d = data
        assert data[:4] == b"CFNT", "no es CFNT: " + repr(data[:4])
        (self.bom, self.hdr_size, self.version, self.file_size,
         self.nblocks) = struct.unpack_from("<HHIII", data, 4)
        self.finf_off = 0x14
        self._parse_finf()

    def u(self, fmt, off):
        return struct.unpack_from(fmt, self.d, off)

    def _parse_finf(self):
        d = self.d
        o = self.finf_off
        assert d[o:o + 4] == b"FINF", d[o:o + 4]
        self.finf_size = self.u("<I", o + 4)[0]
        self.font_type = d[o + 8]
        self.line_feed = d[o + 9]
        self.alter_char = self.u("<H", o + 10)[0]
        self.def_left, self.def_glyph_w, self.def_char_w = d[o + 12], d[o + 13], d[o + 14]
        self.encoding = d[o + 15]
        self.tglp_off, self.cwdh_off, self.cmap_off = self.u("<III", o + 16)
        self.height, self.width, self.ascent = d[o + 28], d[o + 29], d[o + 30]

    def tglp(self):
        o = self.tglp_off - 8           # volver al inicio del bloque
        d = self.d
        assert d[o:o + 4] == b"TGLP", d[o:o + 4]
        cell_w, cell_h, baseline, max_w = d[o + 8], d[o + 9], d[o + 10], d[o + 11]
        sheet_size = self.u("<I", o + 12)[0]
        nsheets, fmt = self.u("<HH", o + 16)
        ncols, nrows, sw, sh = self.u("<HHHH", o + 20)
        sheet_data = self.u("<I", o + 28)[0]
        return dict(cell_w=cell_w, cell_h=cell_h, baseline=baseline, max_w=max_w,
                    sheet_size=sheet_size, nsheets=nsheets, fmt=fmt, ncols=ncols,
                    nrows=nrows, sheet_w=sw, sheet_h=sh, sheet_data=sheet_data)

    def cmaps(self):
        out = []
        o = self.cmap_off
        while o:
            s = o - 8
            d = self.d
            assert d[s:s + 4] == b"CMAP", d[s:s + 4]
            cbeg, cend, method, _r = self.u("<HHHH", s + 8)
            nxt = self.u("<I", s + 16)[0]
            body = s + 20
            entries = {}
            if method == 0:      # direct
                offset = self.u("<H", body)[0]
                for c in range(cbeg, cend + 1):
                    gi = c - cbeg + offset
                    if gi != 0xFFFF:
                        entries[c] = gi
            elif method == 1:    # table
                for i, c in enumerate(range(cbeg, cend + 1)):
                    gi = self.u("<H", body + i * 2)[0]
                    if gi != 0xFFFF:
                        entries[c] = gi
            elif method == 2:    # scan
                n = self.u("<H", body)[0]
                for i in range(n):
                    code, gi = self.u("<HH", body + 2 + i * 4)
                    if gi != 0xFFFF:
                        entries[code] = gi
            out.append(dict(begin=cbeg, end=cend, method=method, n=len(entries),
                            entries=entries))
            o = nxt
        return out

    def cwdhs(self):
        out = []
        o = self.cwdh_off
        while o:
            s = o - 8
            d = self.d
            assert d[s:s + 4] == b"CWDH", d[s:s + 4]
            start, end = self.u("<HH", s + 8)
            nxt = self.u("<I", s + 12)[0]
            widths = {}
            for i in range(end - start + 1):
                left, gw, cw = struct.unpack_from("<bBB", d, s + 16 + i * 3)
                widths[start + i] = (left, gw, cw)
            out.append(dict(start=start, end=end, widths=widths))
            o = nxt
        return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    f = sys.argv[1] if len(sys.argv) > 1 else r"work\fa_extract\font\FONT12T.bcfnt"
    b = BCFNT(open(f, "rb").read())
    print(f"{f}: version=0x{b.version:08X} file_size={b.file_size} blocks={b.nblocks}")
    print(f"FINF: type={b.font_type} line_feed={b.line_feed} alter={b.alter_char} "
          f"enc={b.encoding} height={b.height} width={b.width} ascent={b.ascent}")
    t = b.tglp()
    print(f"TGLP: cell={t['cell_w']}x{t['cell_h']} baseline={t['baseline']} maxw={t['max_w']} "
          f"sheets={t['nsheets']} fmt={t['fmt']} grid={t['ncols']}x{t['nrows']} "
          f"sheet={t['sheet_w']}x{t['sheet_h']} sheet_size={t['sheet_size']} data@{t['sheet_data']}")
    cms = b.cmaps()
    total = sum(c["n"] for c in cms)
    print(f"CMAP: {len(cms)} bloques, {total} codepoints mapeados")
    for c in cms[:8]:
        print(f"   begin=0x{c['begin']:04X} end=0x{c['end']:04X} method={c['method']} n={c['n']}")
    if len(cms) > 8:
        print(f"   ... (+{len(cms)-8} bloques)")
    # comprobar acentos latinos y signos
    allmap = {}
    for c in cms:
        allmap.update(c["entries"])
    print("\nGlifos para caracteres del espanol (codepoint Unicode):")
    for ch in "ñÑáéíóúüÁÉÍÓÚ¡¿":
        cp = ord(ch)
        print(f"   {ch} U+{cp:04X}: {'SI glifo='+str(allmap[cp]) if cp in allmap else 'NO'}")
    print(f"\nrango total de codepoints: 0x{min(allmap):04X}..0x{max(allmap):04X}")


if __name__ == "__main__":
    main()
