"""Read texture rectangles from QNA 051 parts without changing layout data."""
import struct


def regions(data):
    if data[:8] != b' QNA 051':
        raise ValueError('unsupported QNA version')
    textures, _, parts = struct.unpack_from('<III', data, 8)
    names_offset, _, parts_offset = struct.unpack_from('<III', data, 36)
    if names_offset + textures * 32 > len(data) or parts_offset + parts * 128 > len(data):
        raise ValueError('QNA table outside file')
    names = [data[names_offset+i*32:names_offset+(i+1)*32].split(b'\0')[0].decode('ascii')
             for i in range(textures)]
    result = set()
    for i in range(parts):
        offset = parts_offset + i * 128
        texture = struct.unpack_from('<I', data, offset+88)[0]
        # Untextured colour parts (for example the emblem-name background).
        if texture == 0xffffffff:
            continue
        if texture >= textures:
            raise ValueError('QNA texture index outside table')
        box = struct.unpack_from('<4f', data, offset)
        if not all(value.is_integer() for value in box):
            raise ValueError('fractional QNA region')
        result.add((names[texture], tuple(map(int, box))))
    return sorted(result)
