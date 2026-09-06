"""Apply a local, reviewable JSON translation manifest to ARCV/CTPK atlases.

Manifest and recovered artwork stay in work/. No texture coordinates or archive
entry lengths change. Re-open every encoded texture before accepting the output.
"""
import argparse
import json
from pathlib import Path

from PIL import ImageDraw, ImageFont
from ui_archive import entries, unwrap
from ctpk_ui import decode, encode, metadata


def paint(image, operation, font_path):
    x0, y0, x1, y1 = operation['box']
    if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
        raise ValueError('invalid text rectangle')
    draw = ImageDraw.Draw(image)
    if operation.get('rotate'):
        from PIL import Image
        angle=operation['rotate']
        if angle not in (90,270):raise ValueError('only quarter-turn text rotation supported')
        temp=Image.new('RGBA',(y1-y0,x1-x0))
        nested={k:v for k,v in operation.items() if k!='rotate'}
        nested['box']=[0,0,temp.width,temp.height]
        size=paint(temp,nested,font_path)
        image.paste(temp.rotate(angle,expand=True),(x0,y0))
        return size
    if 'image' in operation:
        from PIL import Image, ImageOps
        import cv2
        import numpy as np
        insert = Image.open(operation['image']).convert('RGBA')
        key = operation.get('edge_background')
        if key:
            pixels = np.array(insert)
            rgb = pixels[:,:,:3]
            allowed = (rgb.max(axis=2)<32) if key=='black' else ((rgb.min(axis=2)>200)&((rgb.max(axis=2).astype(int)-rgb.min(axis=2))<25))
            count, labels = cv2.connectedComponents(allowed.astype(np.uint8),connectivity=4)
            border = np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
            border = border[border!=0]
            pixels[:,:,3][np.isin(labels,border)] = 0
            insert = Image.fromarray(pixels)
        if 'source_box' in operation: insert=insert.crop(tuple(operation['source_box']))
        # BOX integrates source pixels at native resolution; texture encoding then
        # applies the original console's channel depth and alpha precision.
        scale = operation.get('scale', 1)
        if not 0 < scale <= 1:
            raise ValueError('image scale must be in (0, 1]')
        insert=ImageOps.contain(insert,(round((x1-x0)*scale),round((y1-y0)*scale)),Image.Resampling.BOX)
        draw.rectangle((x0,y0,x1-1,y1-1),fill=tuple(operation.get('background',[0,0,0,0])))
        image.alpha_composite(insert,(x0+(x1-x0-insert.width)//2,y0+(y1-y0-insert.height)//2))
        return 0
    if operation.get('erase') == 'bright':
        # Interpolate only the old bright lettering over the existing background.
        # Keep the frame, icons and all pixels outside this explicit rectangle.
        import cv2
        import numpy as np
        pixels = np.array(image)
        mask = np.zeros((image.height,image.width),dtype=np.uint8)
        crop = pixels[y0:y1,x0:x1,:3]
        mask[y0:y1,x0:x1] = (crop.min(axis=2) >= 90).astype(np.uint8)*255
        mask = cv2.dilate(mask,np.ones((3,3),dtype=np.uint8))
        limit = np.zeros_like(mask)
        limit[y0:y1,x0:x1] = 255
        mask &= limit
        pixels[:,:,:3] = cv2.inpaint(pixels[:,:,:3],mask,3,cv2.INPAINT_TELEA)
        from PIL import Image
        image.paste(Image.fromarray(pixels))
    else:
        draw.rectangle((x0,y0,x1-1,y1-1), fill=tuple(operation.get('background',[0,0,0,0])))
    lines = operation['text'].split('\n')
    size = operation.get('size',13)
    while size >= 7:
        font = ImageFont.truetype(font_path,size)
        boxes = [font.getbbox(line) for line in lines]
        step = operation.get('step',size+2)
        if max(b[2]-b[0] for b in boxes) <= x1-x0-2 and step*(len(lines)-1)+max(b[3]-b[1] for b in boxes) <= y1-y0-2:
            break
        size -= 1
    else:
        raise ValueError('text does not fit: '+operation['text'])
    total = step*(len(lines)-1)+max(b[3]-b[1] for b in boxes)
    top = y0+(y1-y0-total)//2
    for i,(line,b) in enumerate(zip(lines,boxes)):
        left = x0+(x1-x0-(b[2]-b[0]))//2-b[0]
        draw.text(
            (left,top+i*step-b[1]), line, font=font,
            fill=tuple(operation.get('color',[255,255,255,255])),
            stroke_width=operation.get('stroke_width', 0),
            stroke_fill=tuple(operation.get('stroke_fill',[0,0,0,255])),
        )
    return size


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--source',type=Path,required=True)
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
            sizes=[paint(image,op,args.font) for op in textures[name]]
            replacement=encode(original,image)
            assert len(replacement)==length
            assert metadata(replacement)==metadata(original)
            assert encode(replacement,decode(replacement))==replacement
            output[off:off+length]=replacement
            args.previews.mkdir(parents=True,exist_ok=True)
            decode(replacement).save(args.previews/(Path(name).stem+'.png'))
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
