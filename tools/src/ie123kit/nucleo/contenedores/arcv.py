"""Read SSZL-wrapped ARCV UI resources from the IE123 original archive."""
import struct


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
