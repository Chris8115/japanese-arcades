"""Pack original ONGEKI illustrations unchanged and return their occupied UV bounds."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/ongeki'
TEXTURES = ROOT / 'src/main/resources/assets/japanesearcades/textures/block'


def pack_artwork():
    TEXTURES.mkdir(parents=True, exist_ok=True)
    result = {}
    for name in ('display', 'marquee'):
        source = Image.open(ART / f'{name}-artwork-source.png').convert('RGB')
        size = tuple(1 << (value - 1).bit_length() for value in source.size)
        packed = Image.new('RGB', size, (8, 13, 20))
        packed.paste(source, (0, 0))
        packed.save(TEXTURES / f'ongeki_{name}.png')
        result[name] = {
            'source_size': list(source.size),
            'texture_size': list(size),
            'uv': [0, 0, 16 * source.width / size[0], 16 * source.height / size[1]],
        }
    return result


if __name__ == '__main__':
    import json
    print(json.dumps(pack_artwork(), indent=2))
