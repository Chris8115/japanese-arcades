"""Pack original IIDX illustrations losslessly into power-of-two textures."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/beatmania-iidx-lightning'
TEXTURES=ROOT/'src/main/resources/assets/japanesearcades/textures/block'

def pack_artwork():
    TEXTURES.mkdir(parents=True,exist_ok=True);result={}
    for name in ('display','marquee','banners'):
        path=ART/(name+'-artwork-source.png')
        if not path.exists():raise SystemExit('Original IIDX artwork not ready: '+str(path))
        source=Image.open(path).convert('RGB')
        size=tuple(1<<(n-1).bit_length() for n in source.size)
        packed=Image.new('RGB',size,(15,12,24));packed.paste(source,(0,0))
        packed.save(TEXTURES/('beatmania_iidx_lightning_'+name+'.png'))
        result[name]={'source_size':list(source.size),'texture_size':list(size),
                      'uv':[0,0,16*source.width/size[0],16*source.height/size[1]]}
    return result

if __name__=='__main__':
    import json
    print(json.dumps(pack_artwork(),indent=2))
