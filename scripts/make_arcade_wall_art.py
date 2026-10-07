"""Generate original, pixel-styled arcade signage as inexpensive vanilla paintings.

Pillow is required. A Japanese system font is used only to rasterize labels; no font
file is distributed. Pass --font for a compatible font on non-Windows systems.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'src/main/resources'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--font', default='C:/Windows/Fonts/BIZ-UDGothicB.ttc')
    args = parser.parse_args()
    font_path = args.font

    def text(draw, xy, value, size, color, anchor='mm'):
        draw.text(xy, value, font=ImageFont.truetype(font_path, size), fill=color, anchor=anchor,
                  stroke_width=0)

    def save(name, image, blocks):
        path = RES / f'assets/japanesearcades/textures/painting/{name}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        variant = RES / f'data/japanesearcades/painting_variant/{name}.json'
        variant.parent.mkdir(parents=True, exist_ok=True)
        variant.write_text(json.dumps({'width': blocks[0], 'height': blocks[1],
                                      'asset_id': f'japanesearcades:{name}'}, indent=2)+'\n')

    image = Image.new('RGB', (64, 320), '#921b2d')
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, 61, 317), fill='#c82740', outline='#ffccb0', width=2)
    draw.rectangle((6, 6, 57, 313), outline='#ef6873', width=1)
    for i, ch in enumerate('ゲームセンター'):
        if ch == 'ー':
            draw.rectangle((30, 10+i*43, 34, 37+i*43), fill='#fff5d8')
        else:
            text(draw, (32, 24 + i*43), ch, 37, '#fff5d8')
    save('arcade_vertical_sign', image, (1, 5))

    image = Image.new('RGB', (320, 64), '#641824')
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, 317, 61), fill='#ac2437', outline='#edaa82', width=2)
    draw.line((8, 51, 311, 51), fill='#e99871', width=1)
    text(draw, (160, 26), 'GAME CENTER', 38, '#fff4d5')
    text(draw, (160, 56), 'PLAY  /  COLLECT  /  RELAX', 8, '#ffceb2')
    save('arcade_game_center', image, (5, 1))

    image = Image.new('RGB', (192, 192), '#202b31')
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, 187, 187), outline='#d69c77', width=3)
    draw.rectangle((10, 10, 181, 181), outline='#506064', width=1)
    alien = ['00100000100', '00010001000', '00111111100', '01101110110',
             '11111111111', '10111111101', '10100000101', '00011011000']
    for y, line in enumerate(alien):
        for x, bit in enumerate(line):
            if bit == '1':
                left, top = 30+x*12, 34+y*12
                draw.rectangle((left-2, top-2, left+13, top+13), fill='#9b3047')
                draw.rectangle((left, top, left+10, top+10), fill='#ffb6ac')
    text(draw, (96, 155), 'ゲーム', 28, '#f1dac0')
    save('arcade_invader', image, (3, 3))

    # Intentionally coarse pixel artwork, enlarged with nearest-neighbor sampling.
    image = Image.new('RGB', (128, 96), '#e2cba6')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 127, 95), outline='#49382d', width=3)
    draw.rectangle((5, 5, 122, 90), outline='#b69375', width=1)
    draw.ellipse((78, 12, 106, 40), fill='#c34c49')
    draw.polygon([(6, 69), (37, 45), (49, 53), (69, 25), (96, 63), (121, 54), (121, 89), (6, 89)], fill='#6e8290')
    draw.polygon([(18, 75), (45, 61), (68, 26), (94, 63), (121, 77), (121, 89), (6, 89)], fill='#2e536d')
    draw.polygon([(53, 49), (68, 26), (81, 45), (75, 42), (72, 47), (66, 40), (61, 48), (59, 44)], fill='#fff0d7')
    draw.polygon([(60, 56), (66, 46), (60, 70), (45, 81)], fill='#456b84')
    for y in (77, 81, 85):
        draw.line((8, y, 119, y), fill='#8298a0')
    draw.line((15, 88, 17, 58, 10, 47, 15, 58, 29, 49, 17, 64), fill='#4a3b3c', width=2)
    for x, y in [(9, 48), (14, 45), (20, 48), (26, 46), (30, 50), (19, 57), (10, 56)]:
        draw.rectangle((x-2, y-2, x+2, y+1), fill='#ca8791')
        draw.point((x, y-1), fill='#f4b6bd')
    save('arcade_fuji', image.resize((256, 192), Image.Resampling.NEAREST), (4, 3))

    tag = RES / 'data/minecraft/tags/painting_variant/placeable.json'
    tag.parent.mkdir(parents=True, exist_ok=True)
    tag.write_text(json.dumps({'replace': False, 'values': [f'japanesearcades:{name}' for name in
                    ['arcade_vertical_sign', 'arcade_game_center', 'arcade_invader', 'arcade_fuji']]}, indent=2)+'\n')
    print('Generated four arcade wall paintings and additive placeable tag.')


if __name__ == '__main__':
    main()
