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


def paint_condensed(image, operation, font_path):
    """Draw text (with outline and shadow) at a readable size, squeeze it only
    horizontally to the available width, and paste it left-aligned.

    With crisp=True the alpha is thresholded for 1-bit alpha atlases, which keeps
    letters whole where a tiny crisp font size would break them.
    """
    from PIL import Image
    x0, y0, x1, y1 = operation['box']
    right = operation.get('text_right', x1)
    stroke = operation.get('stroke_width', 0)
    size = operation.get('size', 13)
    font = ImageFont.truetype(font_path, size)
    text = operation['text']
    b = font.getbbox(text, stroke_width=stroke)
    sx, sy, shade = operation['shadow'] if operation.get('shadow') else (0, 0, None)
    width, height = b[2] - b[0] + abs(sx), b[3] - b[1] + abs(sy)
    temp = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp)
    if shade:
        draw.text((-b[0] + sx, -b[1] + sy), text, font=font, fill=tuple(shade),
                  stroke_width=stroke, stroke_fill=tuple(shade))
    draw.text((-b[0], -b[1]), text, font=font, fill=tuple(operation.get('color', [255, 255, 255, 255])),
              stroke_width=stroke, stroke_fill=tuple(operation.get('stroke_fill', [0, 0, 0, 255])))
    left = x0 + operation.get('indent', 0)
    available = right - left
    if height > y1 - y0 or available <= 0:
        raise ValueError('text does not fit: ' + text)
    if width > available:
        temp = temp.resize((available, height), Image.Resampling.LANCZOS)
    if operation.get('crisp'):
        pixels = temp.load()
        for yy in range(temp.height):
            for xx in range(temp.width):
                r, g, bl, a = pixels[xx, yy]
                pixels[xx, yy] = (r, g, bl, 255) if a >= 128 else (0, 0, 0, 0)
    top = y0 + (y1 - y0 - height) // 2
    image.paste(temp, (left, top), temp)
    return size


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
        dx, dy = operation.get('offset', [0, 0])
        left = x0 + (x1-x0-insert.width)//2 + dx
        top = y0 + (y1-y0-insert.height)//2 + dy
        if not (x0 <= left and y0 <= top and left+insert.width <= x1 and top+insert.height <= y1):
            raise ValueError('image offset exceeds its atlas rectangle')
        image.alpha_composite(insert, (left, top))
        return 0
    if operation.get('erase') == 'row_sample':
        sample_x = operation['sample_x']
        if not 0 <= sample_x < image.width or x0 <= sample_x < x1:
            raise ValueError('background sample must be outside the text rectangle')
        for y in range(y0, y1):
            draw.line((x0, y, x1-1, y), fill=image.getpixel((sample_x, y)))
    elif operation.get('erase') == 'bright':
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
    elif operation.get('erase') == 'none':
        # Previous operations already restored the background inside this box.
        pass
    else:
        draw.rectangle((x0,y0,x1-1,y1-1), fill=tuple(operation.get('background',[0,0,0,0])))
    if operation.get('condense'):
        return paint_condensed(image, operation, font_path)
    if operation.get('crisp'):
        # 1-bit alpha atlases threshold antialiased edges into broken glyphs.
        draw.fontmode = '1'
    lines = operation['text'].split('\n')
    padding = operation.get('padding', 1)
    if padding < 0:
        raise ValueError('negative text padding')
    size = operation.get('size',13)
    while size >= 7:
        font = ImageFont.truetype(font_path,size)
        boxes = [font.getbbox(line, stroke_width=operation.get('stroke_width', 0)) for line in lines]
        step = operation.get('step',size+2)
        dx, dy = (abs(operation['shadow'][0]), abs(operation['shadow'][1])) if operation.get('shadow') else (0, 0)
        # Optional slack for renderers that overshoot their bbox (crisp glyphs + shadow).
        dx, dy = dx + operation.get('fit_margin', 0), dy + operation.get('fit_margin', 0)
        if max(b[2]-b[0] for b in boxes)+dx <= x1-x0-2*padding and step*(len(lines)-1)+max(b[3]-b[1] for b in boxes)+dy <= y1-y0-2*padding:
            break
        size -= 1
    else:
        raise ValueError('text does not fit: '+operation['text'])
    total = step*(len(lines)-1)+max(b[3]-b[1] for b in boxes)
    top = y0+(y1-y0-total)//2
    shadow = operation.get('shadow')
    for i,(line,b) in enumerate(zip(lines,boxes)):
        if operation.get('align') == 'left':
            # Match atlases whose original labels start at the rectangle edge.
            left = x0+operation.get('indent', padding)-b[0]
        else:
            left = x0+(x1-x0-(b[2]-b[0]))//2-b[0]
        if shadow:
            # Drop shadow drawn first, same glyph and outline, offset by (dx, dy).
            sx, sy, shade = shadow
            draw.text((left+sx,top+i*step-b[1]+sy), line, font=font, fill=tuple(shade),
                      stroke_width=operation.get('stroke_width', 0), stroke_fill=tuple(shade))
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
