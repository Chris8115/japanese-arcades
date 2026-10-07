"""Pack original NEMSYS art unchanged and report occupied UV bounds."""
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/sound-voltex-nemsys'
TEXTURES=ROOT/'src/main/resources/assets/funpackcustom/textures/block'

def pack_artwork():
    TEXTURES.mkdir(parents=True,exist_ok=True)
    result={}
    for name in ('display','marquee'):
        path=ART/(name+'-artwork-source.png')
        if not path.exists():
            raise SystemExit('Prepare original NEMSYS '+name+' artwork before export: '+str(path))
        source=Image.open(path).convert('RGB')
        size=tuple(1<<(n-1).bit_length() for n in source.size)
        packed=Image.new('RGB',size,(11,13,20));packed.paste(source,(0,0))
        packed.save(TEXTURES/('sound_voltex_nemsys_'+name+'.png'))
        result[name]={'source_size':list(source.size),'texture_size':list(size),
                      'uv':[0,0,16*source.width/size[0],16*source.height/size[1]]}
    return result

if __name__=='__main__':
    import json
    print(json.dumps(pack_artwork(),indent=2))
