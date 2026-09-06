"""Read SSZL-wrapped ARCV UI resources from the IE123 original archive."""
import struct


def unwrap(data):
    if data[:4] != b'SSZL':
        return data
    packed, expected = struct.unpack_from('<II', data, 8)
    if packed + 16 != len(data):
        raise ValueError('SSZL size mismatch')
    ring = bytearray(4096)
    cursor, pos, out = 0xfee, 16, bytearray()
    while len(out) < expected:
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) == expected:
                break
            if flags & (1 << bit):
                values = [data[pos]]
                pos += 1
                for value in values:
                    out.append(value);ring[cursor] = value;cursor = (cursor+1)&4095
            else:
                lo, hi = data[pos:pos+2]
                pos += 2
                offset = lo | ((hi & 0xf0) << 4)
                length = (hi & 15)+3
                for k in range(length):
                    if len(out) >= expected:
                        raise ValueError('SSZL output overflow')
                    value = ring[(offset+k)&4095]
                    out.append(value);ring[cursor] = value;cursor = (cursor+1)&4095
    return bytes(out)


def entries(data):
    if data[:4] != b'ARCV':
        raise ValueError('not ARCV')
    count, size = struct.unpack_from('<II', data, 4)
    if size != len(data) or 12+12*count > len(data):
        raise ValueError('invalid ARCV size')
    result = []
    for i in range(count):
        off, size, crc = struct.unpack_from('<III', data, 12+12*i)
        if off < 12+12*count or off+size > len(data):
            raise ValueError('ARCV entry out of range')
        result.append((off,size,crc))
    return result
