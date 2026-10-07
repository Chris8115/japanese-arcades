"""Prepare the supplied WACCA poster at its original aspect ratio.

First import: python scripts/make_wacca_poster.py --source PATH/TO/WaccaPoster.jpg
Rebuild:       python scripts/make_wacca_poster.py

The JPEG is copied byte-for-byte and retained as an immutable source. The only
image operation is a uniform resize of the entire source to1024pixels wide.
No padding is added, no source border is removed, and no artwork is repainted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/wacca_poster'
ASSETS=ROOT/'src/main/resources/assets/japanesearcades'
SOURCE=ART/'source.jpg'
TEXTURE=ASSETS/'textures/painting/wacca_poster.png'
ITEM_TEXTURE=ASSETS/'textures/item/wacca_poster.png'
ITEM_MODEL=ASSETS/'models/item/wacca_poster.json'
TEXTURE_WIDTH=1024


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,help='Import the original JPEG once, without changing its bytes.')
    args=parser.parse_args()
    ART.mkdir(parents=True,exist_ok=True)
    if args.source:
        if not args.source.is_file(): raise SystemExit('Source image not found: '+str(args.source))
        if SOURCE.exists() and sha256(SOURCE)!=sha256(args.source):
            raise SystemExit('Refusing to replace the immutable WACCA source with a different file.')
        if args.source.resolve()!=SOURCE.resolve(): shutil.copy2(args.source,SOURCE)
        assert SOURCE.read_bytes()==args.source.read_bytes(),'Source copy must be byte-identical'
    if not SOURCE.is_file(): raise SystemExit('Missing art/wacca_poster/source.jpg; first run with --source.')

    original_hash=sha256(SOURCE)
    with Image.open(SOURCE) as original:
        assert original.format=='JPEG','The authored source must remain the supplied JPEG'
        original_size=original.size
        source_mode=original.mode
        source=original.convert('RGB')
    scale=TEXTURE_WIDTH/source.width
    fitted_size=tuple(round(dimension*scale) for dimension in source.size)
    fitted=source.resize(fitted_size,Image.Resampling.LANCZOS)
    TEXTURE.parent.mkdir(parents=True,exist_ok=True)
    fitted.save(TEXTURE)
    # Painting textures belong to a separate atlas. The item needs the same
    # authored pixels under textures/item so the block/item atlas loads them.
    ITEM_TEXTURE.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(TEXTURE,ITEM_TEXTURE)

    # A thin rectangle uses the exact original aspect ratio. A generated
    # item parent would squeeze this non-square source into a square silhouette.
    # The sidewalls sample a black corner of the existing image, adding no art.
    item_height=15
    item_width=item_height*source.width/source.height
    faces={direction:{'texture':'#poster','uv':[0,0,.015625,.015625]}
           for direction in ('east','west','up','down')}
    faces.update({direction:{'texture':'#poster','uv':[0,0,16,16]} for direction in ('north','south')})
    model={
        'ambientocclusion':False,'gui_light':'front',
        'textures':{'poster':'japanesearcades:item/wacca_poster','particle':'japanesearcades:item/wacca_poster'},
        'elements':[{'name':'WACCA original-aspect poster print',
                     'from':[8-item_width/2,.5,7.94],'to':[8+item_width/2,15.5,8.06],'faces':faces}],
        'display':{
            'gui':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1,1,1]},
            'ground':{'translation':[0,3,0],'scale':[.65,.65,.65]},
            'fixed':{'rotation':[0,180,0],'scale':[1,1,1]},
            'thirdperson_righthand':{'rotation':[0,-90,0],'translation':[0,2,1],'scale':[.6,.6,.6]},
            'firstperson_righthand':{'rotation':[0,-20,0],'translation':[1,1,0],'scale':[.7,.7,.7]},
        },
    }
    ITEM_MODEL.parent.mkdir(parents=True,exist_ok=True)
    ITEM_MODEL.write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    metadata={
        'source':{'file':'source.jpg','original_filename':'WaccaPoster.jpg','sha256':original_hash,
                  'bytes':SOURCE.stat().st_size,'dimensions':list(original_size),'mode':source_mode},
        'output':{'texture':'japanesearcades:painting/wacca_poster','file':'src/main/resources/assets/japanesearcades/textures/painting/wacca_poster.png',
                  'sha256':sha256(TEXTURE),'dimensions':list(fitted_size),'mode':'RGB',
                  'item_texture':'japanesearcades:item/wacca_poster',
                  'item_file':'src/main/resources/assets/japanesearcades/textures/item/wacca_poster.png',
                  'item_sha256':sha256(ITEM_TEXTURE)},
        'packing':{'operation':'Uniform resize of the whole original image to1024pixels wide, without added padding',
                   'resampling':'Pillow LANCZOS','uniform_scale':scale,'scaled_dimensions':list(fitted_size),
                   'offset':[0,0],'padding':[0,0,0,0],
                   'integer_size_rounding':'Nearest integer pixel; no crop, stretching, border removal, or artwork changes'},
        'wall_support_grid_blocks':[1,2],
        'visual_dimensions_blocks':[1,source.height/source.width],
        'item':{'model':'japanesearcades:item/wacca_poster','face_dimensions':[item_width,item_height],
                'thickness':.12,'texture_uv':[0,0,16,16]},
    }
    (ART/'source.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')

    # Technical checks compare actual output pixels to the one authorized resize.
    decoded=Image.open(TEXTURE).convert('RGB')
    assert ImageChops.difference(decoded,fitted).getbbox() is None
    assert TEXTURE.read_bytes()==ITEM_TEXTURE.read_bytes(),'Both atlases need identical poster pixels'
    assert sha256(SOURCE)==original_hash,'Original source bytes changed'
    assert fitted_size[0]==TEXTURE_WIDTH
    assert abs(fitted_size[0]/source.width-fitted_size[1]/source.height)<=1/min(original_size)
    element=model['elements'][0]
    assert abs((element['to'][0]-element['from'][0])/(element['to'][1]-element['from'][1])-source.width/source.height)<1e-12
    assert decoded.size==fitted_size
    assert all(face['texture']=='#poster' for face in element['faces'].values())
    assert model['textures']['poster']=='japanesearcades:item/wacca_poster'
    print(json.dumps({'source_sha256':original_hash,'source_dimensions':original_size,
                      'fitted':fitted_size,'visual_blocks':metadata['visual_dimensions_blocks'],
                      'item_dimensions':[item_width,item_height],'pixel_and_aspect_checks':'PASS'},indent=2))


if __name__=='__main__':main()
