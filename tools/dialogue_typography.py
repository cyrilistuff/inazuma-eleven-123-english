"""Experimental full-width Latin transport for the NFTR/BCFNT dual renderer.

Keep engine control sequences byte-for-byte. This is an opt-in experiment until
validated in Azahar; the original ASCII encoder remains available.
"""
import re
from font_patch import PLAN

ACCENTS = {ch: chr(cp) for ch, _, _, cp in PLAN}
TOKEN = re.compile(r'(\\[nf]|%[0-9]*[A-Za-z])')


def encode_fullwidth(text):
    parts = TOKEN.split(text)
    result = []
    for part in parts:
        if TOKEN.fullmatch(part):
            result.append(part)
            continue
        for ch in part:
            if ch in ACCENTS:
                result.append(ACCENTS[ch])
            elif ch == ' ':
                result.append('\u3000')
            elif '!' <= ch <= '~':
                result.append(chr(ord(ch) + 0xfee0))
            else:
                result.append(ch)
    # Unsupported glyphs must fail, never silently become question marks.
    return ''.join(result).encode('shift_jis')
