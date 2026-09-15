"""Apply a local, reviewable JSON translation manifest to ARCV/CTPK atlases.

Manifest and recovered artwork stay in work/. No texture coordinates or archive
entry lengths change. Re-open every encoded texture before accepting the output.
"""
import argparse
import json
from pathlib import Path

from PIL import ImageDraw, ImageFont

from ie123kit.nucleo.compresion.sszl import unwrap
from ie123kit.nucleo.contenedores.arcv import entries
from ie123kit.nucleo.graficos.ctpk import decode, encode, metadata
from ie123kit.nucleo.graficos.pintado import paint, paint_condensed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--base',type=Path,help='Current candidate resources; preserve all previous edits outside the manifest')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--previews',type=Path,required=True)
    parser.add_argument('--font',default='C:/Windows/Fonts/arialbd.ttf')
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    reports=[]
    for path, textures in manifest.items():
        source=args.source/path
        if not source.exists(): source=source.with_suffix('.unpacked')
        raw=unwrap(source.read_bytes())
        if args.base:
            base=unwrap((args.base/path).read_bytes())
            if entries(base)!=entries(raw) or len(base)!=len(raw):
                raise ValueError('candidate archive structure differs: '+path)
            raw=base
        output=bytearray(raw)
        found=set()
        for off,length,_ in entries(raw):
            original=raw[off:off+length]
            if original[:4] != b'CTPK': continue
            name=metadata(original)[0]
            if name not in textures: continue
            found.add(name)
            image=decode(original)
            if encode(original,image) != original: raise ValueError('codec roundtrip failed: '+name)
            sizes=[]
            for op in textures[name]:
                before=image.copy()
                sizes.append(paint(image,op,args.font))
                # Reject drawing outside the declared edit area, including strokes.
                from PIL import ImageChops
                outside=ImageChops.difference(before,image)
                ImageDraw.Draw(outside).rectangle((op['box'][0],op['box'][1],op['box'][2]-1,op['box'][3]-1),fill=(0,0,0,0))
                if any(channel.getbbox() for channel in outside.split()):
                    raise ValueError('painting escaped rectangle: '+name)
            replacement=encode(original,image)
            assert len(replacement)==length
            assert metadata(replacement)==metadata(original)
            assert encode(replacement,decode(replacement))==replacement
            output[off:off+length]=replacement
            preview_dir=args.previews/Path(path).stem
            preview_dir.mkdir(parents=True,exist_ok=True)
            decode(replacement).save(preview_dir/(Path(name).stem+'.png'))
            reports.append({'archive':path,'texture':name,'font_sizes':sizes})
        if found != set(textures): raise ValueError('textures missing: '+str(set(textures)-found))
        assert entries(output)==entries(raw)
        destination=args.output/path
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(output)
    (args.previews/'report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print('Translated',len(reports),'textures in',len(manifest),'archives')


if __name__=='__main__':
    main()
