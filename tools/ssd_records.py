"""IE1 inline SSD text records: u16 instruction, u8 argument, u8 byte size.

The byte size includes the four-byte header, terminator and four-byte alignment.
Do not split this table on NUL: headers and padding contain zero bytes too.
"""
from dataclasses import dataclass
import struct


@dataclass(frozen=True)
class TextRecord:
    instruction: int
    argument: int
    raw: bytes

    @property
    def body(self):
        return self.raw[4:].split(b"\0", 1)[0]


def parse(data):
    if len(data) < 32 or data[:4] != b"SSD\0":
        raise ValueError("not an SSD")
    _, _, size, count, texts, code_size, text_size, _, _ = struct.unpack_from("<4sIIHHIIII", data)
    if size != len(data) or 32 + code_size + text_size != size:
        raise ValueError("inconsistent SSD section sizes")
    end = 32 + code_size
    pos = 32
    instructions = {}
    refs = []
    for _ in range(count):
        if pos + 8 > end:
            raise ValueError("truncated instruction")
        ident, length, opcode, argc, unk = struct.unpack_from("<HHHBB", data, pos)
        types_size = 4 * ((argc + 7) // 8)
        if length != 8 + types_size + 4 * argc or pos + length > end:
            raise ValueError("invalid instruction length")
        if ident in instructions:
            raise ValueError("duplicate instruction ID")
        instructions[ident] = opcode
        for arg in range(argc):
            kind = (data[pos + 8 + arg // 2] >> (4 * (arg % 2))) & 15
            if kind == 3:
                index = struct.unpack_from("<I", data, pos + 8 + types_size + 4 * arg)[0]
                refs.append((ident, arg + 1, index))
        pos += length
    if pos != end:
        raise ValueError("instruction count/size mismatch")
    records = []
    for _ in range(texts):
        if pos + 4 > len(data):
            raise ValueError("truncated text record")
        ident, argument, length = struct.unpack_from("<HBB", data, pos)
        if length < 8 or length % 4 or pos + length > len(data):
            raise ValueError(f"invalid text record size at {pos:#x}: {length}")
        raw = data[pos:pos + length]
        if b"\0" not in raw[4:]:
            raise ValueError("unterminated text")
        body, _, padding = raw[4:].partition(b"\0")
        if any(padding):
            raise ValueError("nonzero text padding")
        records.append(TextRecord(ident, argument, raw))
        pos += length
    if pos != len(data):
        raise ValueError("text count/size mismatch")
    for ident, argument, index in refs:
        if index >= len(records):
            raise ValueError("string index out of range")
        # Original scripts reuse text indices across instructions. The record's
        # owner identifies its first occurrence, not every valid reference.
    return end, instructions, records


def replace(data, replacements):
    """Replace bodies by text-table index; unchanged records stay byte-identical.

    Reject overlength text; never silently cut a sentence or wrap a length byte.
    """
    end, _, records = parse(data)
    if any(not isinstance(i, int) or not 0 <= i < len(records) for i in replacements):
        raise ValueError("unknown replacement index")
    table = bytearray()
    for i, r in enumerate(records):
        if i not in replacements or replacements[i] == r.body:
            table.extend(r.raw)
            continue
        body = replacements[i]
        if b"\0" in body:
            raise ValueError("embedded NUL")
        length = (4 + len(body) + 1 + 3) & ~3
        if length > 252:
            raise ValueError(f"text record {i} exceeds 247 payload bytes")
        table.extend(struct.pack("<HBB", r.instruction, r.argument, length))
        table.extend(body)
        table.extend(bytes(length - 4 - len(body)))
    result = bytearray(data[:end]) + table
    struct.pack_into("<I", result, 8, len(result))
    struct.pack_into("<I", result, 20, len(table))
    parse(result)
    return bytes(result)
