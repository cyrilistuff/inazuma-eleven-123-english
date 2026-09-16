"""Tablas de registros de tamaño fijo (.dat) y pools de cadenas (.STR y ranuras de 32 B).

Las primitivas de escritura NUNCA truncan: si el texto codificado no cabe con su
terminador, lanzan ValueError. El codificador se inyecta; aquí no se elige tipografía.
"""


def names_from_dat(path, stride, dec, width=16):
    with open(path, "rb") as fh:
        d = fh.read()
    return [dec(d[i * stride:i * stride + width]) for i in range(len(d) // stride)]


def strings_from_str(path, dec):
    with open(path, "rb") as fh:
        d = fh.read()
    return [dec(p) for p in d.split(b"\x00") if len(p) >= 1]


def escribir_campo(data, offset, size, codificado, texto):
    """Escribe ``codificado`` en un campo fijo de ``size`` bytes y rellena con ceros.

    Exige sitio para el terminador; nunca trunca.
    """
    if len(codificado) >= size:
        raise ValueError('name exceeds field including terminator: ' + texto)
    data[offset:offset + size] = codificado + bytes(size - len(codificado))


def parchear_pool_32(source, translations, codificar):
    """Sustituye cadenas Shift-JIS alojadas en ranuras de 32 B; ``codificar(texto) -> bytes``.

    Devuelve ``(bytes_resultado, posiciones_cambiadas)``.
    """
    result = bytearray(source); pos = 0; changed = []
    for part in source.split(b'\0'):
        if part:
            text = part.decode('shift_jis').strip()
            if text in translations:
                capacity = ((len(part) + 1 + 31) // 32) * 32
                if pos % 32 or any(source[pos + len(part):pos + capacity]):
                    raise ValueError('not a padded 32-byte string slot')
                nuevo = translations[text]
                escribir_campo(result, pos, capacity, codificar(nuevo), nuevo)
                changed.append(pos)
        pos += len(part) + 1
    return bytes(result), changed
