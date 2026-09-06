"""IE1 keyboard: fcode0/1/2 are 26 x 6 little-endian two-byte cells + CRLF.

Each visible character occupies two equal cells. AAAA switches mode, DDDD
deletes, and ASCII spaces disable a cell. B/C are Japanese diacritic controls.
"""
from dialogue_typography import encode_fullwidth

ROWS=['ABCDEFGHIJ','KLMNÑOPQRS','TUVWXYZÁÉÍ','ÓÚü0123456','789.,!?():','+/=@&;[]  ']


def patch_map(original,mode):
    if len(original)!=314 or original[-2:]!=b'\r\n':
        raise ValueError('unexpected keyboard map')
    out=bytearray(original)
    for y,row in enumerate(ROWS):
        assert len(row)==10
        for x,ch in enumerate(row):
            col=x*2+(x>=5)
            offset=y*52+col*2
            if mode==2 and original[offset:offset+4]==b'    ':continue
            encoded=encode_fullwidth(ch.lower() if mode==1 else ch)
            assert len(encoded)==2
            out[offset:offset+4]=encoded*2
    for y,control in [(1,b'BBBB'),(2,b'CCCC')]:
        if original[y*52+48:y*52+52]!=control:
            raise ValueError('unexpected diacritic control position')
        out[y*52+48:y*52+52]=b'    '
    return bytes(out)


def texture_operations(mode):
    operations=[]
    for y,row in enumerate(ROWS):
        for x,ch in enumerate(row):
            text='ESP' if ch==' ' else (ch.lower() if mode==1 else ch)
            operations.append(dict(box=[x*20,y*16,x*20+20,y*16+16],text=text,size=8 if ch==' ' else 14))
    operations.extend([dict(box=[200,0,224,16],text='abc' if mode==0 else 'ABC',size=10),dict(box=[200,16,224,48],text='',size=10)])
    return operations
