"""Import native GUI captures without changing the detailed cabinet models.

Run the isolated native capture utility first, then pass its icons directory.
These are screenshots of our own in-game meshes, not replacement artwork.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/japanesearcades'
IDS = (
    'nostalgia_op3', 'beatstream', 'sound_voltex_valkyrie', 'sound_voltex_nemsys',
    'beatmania_iidx_lightning', 'wacca', 'chunithm', 'ongeki', 'groove_coaster',
    'museca', 'project_diva', 'chrono_circle', 'music_diver', 'popn_music',
    'maimai', 'ddr_supernova', 'taiko', 'initial_d', 'jubeat',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path)
    args = parser.parse_args()
    from PIL import Image
    # Validate the entire set before updating assets.
    for name in IDS:
        with Image.open(args.captures / f'{name}.png') as image:
            if image.size != (256, 256) or image.mode != 'RGBA':
                raise ValueError(f'{name}: expected a 256 x 256 RGBA native capture')
            low, high = image.getchannel('A').getextrema()
            if low != 0 or high != 255:
                raise ValueError(f'{name}: capture must contain both clear and opaque pixels')

    manifest = {}
    for name in IDS:
        texture = ASSETS / f'textures/item/gui/{name}.png'
        model = ASSETS / f'models/item/gui/{name}.json'
        texture.parent.mkdir(parents=True, exist_ok=True)
        model.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.captures / f'{name}.png', texture)
        # A single face avoids item/generated's unnecessary silhouette extrusion.
        data = {
            'ambientocclusion': False,
            'gui_light': 'front',
            'render_type': 'minecraft:cutout',
            'textures': {'icon': f'japanesearcades:item/gui/{name}',
                         'particle': f'japanesearcades:item/gui/{name}'},
            # Native icons can spill outside their 16px slots. Captures cover 24px,
            # so retain the same scale and center rather than clipping or shrinking.
            'elements': [{'from': [-4, -4, 8], 'to': [20, 20, 8], 'shade': False,
                          'faces': {'south': {'uv': [0, 0, 16, 16], 'texture': '#icon'}}}],
        }
        model.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        manifest[name] = {'gui_faces': 1, 'size': [256, 256], 'canvas_gui_pixels': 24,
                          'sha256': hashlib.sha256(texture.read_bytes()).hexdigest()}
    destination = ROOT / 'art/inventory-icons/manifest.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Imported {len(IDS)} native cabinet icons; one GUI face each.')


if __name__ == '__main__':
    main()
