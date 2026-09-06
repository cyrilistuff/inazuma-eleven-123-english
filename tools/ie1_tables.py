"""Conservative editors for IE1 fixed name fields and 32-byte string slots."""
from dialogue_typography import encode_fullwidth
import struct


def write_field(data, offset, size, text):
    encoded=encode_fullwidth(text)
    if len(encoded)>=size:
        raise ValueError('name exceeds field including terminator: '+text)
    data[offset:offset+size]=encoded+bytes(size-len(encoded))


def patch_string_pool(source, translations):
    result=bytearray(source);pos=0;changed=[]
    for part in source.split(b'\0'):
        if part:
            text=part.decode('shift_jis').strip()
            if text in translations:
                capacity=((len(part)+1+31)//32)*32
                if pos%32 or any(source[pos+len(part):pos+capacity]):
                    raise ValueError('not a padded 32-byte string slot')
                write_field(result,pos,capacity,translations[text])
                changed.append(pos)
        pos+=len(part)+1
    return bytes(result),changed


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
