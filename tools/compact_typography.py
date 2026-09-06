"""Paired NFTR/BCFNT advance edits for the full-width Latin transport.

The game transports Spanish through the Shift-JIS full-width Latin range.  Its
glyph drawings already match the regular Latin glyphs, but their advances were
made for Japanese monospace text.  ``mode='native'`` gives those transported
glyphs the regular Latin metrics while keeping all texture sheets and maps intact.
"""
import math
from font_patch import Font, patch_font_bytes
from nftr_metrics import read_metrics


def patch_pair(bcfnt_path, nftr_data, mode='conservative'):
    if mode not in ('conservative', 'native'):
        raise ValueError('unknown typography mode: ' + mode)
    font = Font(bcfnt_path)
    font.data[:] = patch_font_bytes(bcfnt_path, fullwidth=True)
    metrics, offsets = read_metrics(nftr_data, with_offsets=True)
    nftr = bytearray(nftr_data)
    changed = []
    for codepoint in range(0xff01, 0xff5f):
        ch = chr(codepoint)
        try:
            code = int.from_bytes(ch.encode('shift_jis'), 'big')
        except UnicodeEncodeError:
            continue
        gi = font.cmap.get(codepoint)
        regular_gi = font.cmap.get(codepoint - 0xfee0)
        if gi is None or regular_gi is None or code not in metrics:
            continue
        off = font.cwdh_entry_off(gi)
        regular_off = font.cwdh_entry_off(regular_gi)
        raw_left, glyph_width, advance = font.data[off:off+3]
        raw_regular_left, regular_width, regular_advance = font.data[regular_off:regular_off+3]
        left = raw_left - 256 if raw_left >= 128 else raw_left
        regular_left = raw_regular_left - 256 if raw_regular_left >= 128 else raw_regular_left
        if advance == 0:
            continue
        old_nftr = metrics[code]
        if mode == 'native':
            # The two BCFNT glyph rasters occupy the same cells. Copying the
            # regular Latin metrics gives the visible text its intended kerning.
            font.data[off:off+3] = font.data[regular_off:regular_off+3]
            scale = old_nftr[1] / glyph_width if glyph_width else 1
            new_left = round(regular_left * scale)
            new_width = max(1, round(regular_width * scale))
            new_advance = max(new_left + new_width,
                              round(old_nftr[2] * regular_advance / advance))
            nftr[offsets[code]:offsets[code]+3] = bytes((new_left & 0xff, new_width, new_advance))
            target = regular_advance
            new_nftr = new_advance
        else:
            # Kept for comparison with old candidates.
            target = max(left + glyph_width + 1, math.ceil(advance * 0.82))
            target = min(target, advance)
            new_nftr = max(1, math.ceil(old_nftr[2] * target / advance))
            font.data[off+2] = target
            nftr[offsets[code]+2] = new_nftr
        if target != advance or new_nftr != old_nftr[2]:
            changed.append([hex(code), advance, target, old_nftr[2], new_nftr])
    assert len(nftr) == len(nftr_data)
    read_metrics(nftr)
    return bytes(font.data), bytes(nftr), changed
