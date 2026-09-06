"""Conservative paired NFTR/BCFNT advance experiment; keep glyphs intact."""
import math
from font_patch import Font, patch_font_bytes
from nftr_metrics import read_metrics


def patch_pair(bcfnt_path, nftr_data):
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
        if gi is None or code not in metrics:
            continue
        off = font.cwdh_entry_off(gi)
        left, glyph_width, advance = font.data[off:off+3]
        if left >= 128 or advance == 0:
            continue
        # Do not reduce the space below the actual quad width plus its bearing.
        target = max(left + glyph_width + 1, math.ceil(advance * 0.82))
        target = min(target, advance)
        nftr_advance = metrics[code][2]
        new_nftr = max(1, math.ceil(nftr_advance * target / advance))
        font.data[off+2] = target
        nftr[offsets[code]+2] = new_nftr
        if target != advance:
            changed.append([hex(code), advance, target, nftr_advance, new_nftr])
    assert len(nftr) == len(nftr_data)
    read_metrics(nftr)
    return bytes(font.data), bytes(nftr), changed
