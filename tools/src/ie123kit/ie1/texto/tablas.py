"""Editores conservadores de campos de nombre fijos y ranuras de cadena de 32 B de IE1.

Regla de item.dat: registros de 32 B; el nombre ocupa 19 B; u16 descripción/32 en +30;
las descripciones van en ranuras de 32 B del pool. Nunca se trunca: si no cabe, ValueError.
"""
import struct

from ie123kit.nucleo.registros.tabla_fija import escribir_campo, parchear_pool_32
from ie123kit.nucleo.texto.ancho_completo import encode_fullwidth


def write_field(data, offset, size, text):
    escribir_campo(data, offset, size, encode_fullwidth(text), text)


def patch_string_pool(source, translations):
    return parchear_pool_32(source, translations, encode_fullwidth)


def patch_items(table, pool, replacements):
    """IE1 item.dat: 32-byte records, 19-byte name, u16 description/32 at +30.

    Append descriptions instead of shifting existing strings. Stats and all
    unselected entries remain byte-identical. Each requested source name must match.
    """
    result=bytearray(table);strings=bytearray(pool)
    if len(table)%32:raise ValueError('invalid item table size')
    for index,row in replacements.items():
        offset=int(index)*32
        if offset<0 or offset+32>len(table):raise ValueError('item index out of range')
        source=table[offset:offset+19].split(b'\0')[0].decode('shift_jis')
        if source!=row['source']:raise ValueError('item source mismatch')
        write_field(result,offset,19,row['name'])
        if row.get('description'):
            strings.extend(bytes((-len(strings))%32))
            pointer=len(strings)//32
            if pointer>65535:raise ValueError('description pointer overflow')
            body=encode_fullwidth(row['description'])
            strings.extend(body+b'\0')
            struct.pack_into('<H',result,offset+30,pointer)
    strings.extend(bytes((-len(strings))%32))
    return bytes(result),bytes(strings)
