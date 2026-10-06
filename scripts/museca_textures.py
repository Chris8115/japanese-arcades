"""Native manufactured textures for MÚSECA's white geometric cabinet.

Display and character-marquee artwork are independent source PNGs and are never
opened or modified here. The three hardware atlases are opaque and deterministic.
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from chunithm_textures import PALETTE as BASE_PALETTE
from chunithm_textures import _label, _material_atlas as _base_material_atlas


# Keep the existing sixteen-slot atlas layout: purple -> amber at slot 11,
# green -> red at slot 14. All other material names and indices stay unchanged.
PALETTE = {
    ('amber' if name == 'purple' else 'red' if name == 'green' else name):
    ((244, 174, 65) if name == 'purple' else (192, 37, 53) if name == 'green' else color)
    for name, color in BASE_PALETTE.items()
}
KEYS = list(PALETTE)


def _materials():
    atlas = _base_material_atlas()
    rng = random.Random(1138)
    for name in ('amber', 'red'):
        index = KEYS.index(name)
        tile = Image.new('RGB', (64, 64), PALETTE[name])
        draw = ImageDraw.Draw(tile)
        for y in range(0, 64, 4):
            for x in range(0, 64, 4):
                variation = rng.choice((-2, 0, 0, 2))
                color = tuple(max(0, min(255, c + variation)) for c in PALETTE[name])
                draw.rectangle((x, y, x + 3, y + 3), fill=color)
        atlas.paste(tile, ((index % 4) * 64, (index // 4) * 64))
    return atlas


def _faceted_print(size, kind):
    """Sparse asymmetrical white/silver print from the unlit cabinet photos."""
    image = Image.new('RGB', size, (225, 227, 223))
    draw = ImageDraw.Draw(image)
    w, h = size

    def points(values):
        return [(round(x * (w - 1)), round(y * (h - 1))) for x, y in values]

    def polygon(values, color):
        draw.polygon(points(values), fill=color)

    def line(values, color=(66, 68, 74), width=2):
        draw.line(points(values), fill=color, width=width)

    if kind == 'bezel':
        polygon(((0, 0), (.19, 0), (.08, .54)), (35, 36, 42))
        polygon(((.79, 1), (1, .70), (1, 1)), (43, 43, 48))
        polygon(((.02, .70), (.64, .85), (.20, 1)), (198, 203, 203))
        polygon(((.68, 0), (1, 0), (.93, .22)), (208, 212, 209))
        line(((0, .26), (.92, .02), (.72, .53)))
        line(((0, .64), (.89, .88), (1, .59)))
        line(((.02, 1), (.21, .76), (.57, 1)), (108, 111, 114), 1)
        line(((.61, 0), (.76, .21), (1, .12)), (153, 155, 157), 1)
    elif kind == 'deck':
        # The real deck is predominantly plain white/light silver. Its few
        # large black corner triangles and fine wires sit beneath five spinners.
        polygon(((0, 0), (.40, 0), (.24, .15)), (32, 33, 38))
        polygon(((.77, .16), (1, .02), (1, .34)), (37, 37, 42))
        polygon(((.65, 1), (1, .70), (1, 1)), (23, 25, 31))
        polygon(((.06, .74), (.24, .56), (.36, .93)), (200, 205, 204))
        polygon(((.45, .18), (.62, .04), (.80, .39)), (202, 207, 206))
        for path in (
            ((0, .31), (.30, .05), (.58, .19), (.79, 0)),
            ((0, .66), (.18, .49), (.75, .82), (1, .61)),
            ((.04, .98), (.25, .80), (.51, .98), (.76, .74)),
            ((.24, 0), (.53, .29), (.80, .12), (1, .24)),
            ((.50, .15), (.45, .66), (.76, 1)),
        ):
            line(path)
        line(((.01, .14), (.31, .39), (.88, .03)), (143, 145, 148), 1)
        line(((.17, 1), (.87, .54), (.98, .84)), (124, 128, 130), 1)
    else:
        polygon(((0, 0), (.29, 0), (.18, .58)), (42, 43, 49))
        polygon(((.61, 0), (.94, 0), (.81, .68)), (26, 28, 33))
        polygon(((.30, 1), (.56, .13), (.72, 1)), (198, 203, 202))
        polygon(((.90, 1), (1, .15), (1, 1)), (45, 45, 50))
        line(((0, .08), (.45, .90), (.72, .08), (1, .48)), width=2)
        line(((.09, 1), (.35, .07), (.90, 1)), (103, 108, 110), 1)
    return image


def _speaker():
    speaker = Image.new('RGB', (128, 128), (21, 23, 28))
    draw = ImageDraw.Draw(speaker)
    draw.ellipse((18, 18, 109, 109), fill=(35, 39, 44), outline=(72, 78, 83), width=2)
    for y in range(21, 108, 5):
        offset = 2 if (y // 5) % 2 else 0
        for x in range(21 + offset, 108, 5):
            if (x - 63.5) ** 2 + (y - 63.5) ** 2 <= 42 ** 2:
                draw.rectangle((x, y, x + 1, y + 1), fill=(8, 11, 17))
    for path in (((8, 8), (25, 120), (120, 99)),
                 ((8, 77), (120, 26), (95, 8)), ((38, 8), (119, 120))):
        draw.line(path, fill=(180, 185, 188), width=1)
    draw.polygon(((63, 54), (66, 61), (63, 69), (62, 60)), fill=(188, 192, 193))
    return speaker


def _details():
    details = Image.new('RGB', (512, 512), PALETTE['black'])
    details.paste(_faceted_print((256, 256), 'bezel'), (0, 0))
    details.paste(_faceted_print((256, 256), 'deck'), (256, 0))
    details.paste(_faceted_print((512, 128), 'fascia'), (0, 256))
    details.paste(_speaker(), (0, 384))
    draw = ImageDraw.Draw(details)
    # Optional compact front service reader/LCD (128..256,384..512).
    draw.rectangle((136, 392, 247, 503), fill=(224, 227, 222))
    draw.rectangle((143, 402, 240, 484), fill=(34, 43, 47))
    draw.rectangle((149, 409, 234, 478), fill=(52, 102, 102))
    draw.line((158, 419, 225, 419), fill=(116, 178, 166), width=2)
    _label(details, (192, 439), 'CARD', 11, (166, 214, 195), True)
    _label(details, (192, 457), 'TOUCH', 9, (129, 186, 175))
    draw.rectangle((182, 491, 202, 494), fill=(167, 190, 186))
    # Small manufacturer plate, with a clean 8px regional guard.
    draw.rectangle((264, 392, 375, 503), fill=(219, 222, 214))
    _label(details, (320, 410), 'KONAMI', 12, (151, 39, 56), True)
    _label(details, (320, 432), 'MUSECA', 12, (39, 43, 47), True)
    _label(details, (320, 454), 'SERVICE', 9, (67, 73, 74))
    _label(details, (320, 474), 'BEMANI', 10, (58, 63, 65), True)
    # Optional pedal/service caution sticker, not the physical pedal engraving.
    draw.rectangle((392, 392, 503, 503), fill=(228, 228, 217))
    draw.rectangle((400, 400, 495, 417), fill=(218, 185, 75))
    _label(details, (448, 409), 'CAUTION', 10, (37, 37, 33), True)
    draw.polygon(((418, 446), (430, 424), (442, 446)), outline=(54, 56, 54))
    draw.line((430, 431, 430, 438), fill=(54, 56, 54), width=2)
    draw.point((430, 441), fill=(54, 56, 54))
    _label(details, (448, 468), 'FOOT PEDAL', 9, (64, 66, 60), True)
    draw.line((405, 486, 490, 486), fill=(135, 137, 127), width=1)
    return details


def _branding():
    """The thin polygonal wordmark, with the small authentic maker labels."""
    branding = Image.new('RGB', (1024, 256), (232, 233, 226))
    draw = ImageDraw.Draw(branding)
    # Logical sign crop: x8..1016,y8..208, UV [.125,.5,15.875,13].
    _label(branding, (93, 35), 'KONAMI', 22, (162, 38, 58), True)
    paths = {
        'M': [[(0, 1), (0, 0), (.5, .53), (1, 0), (1, 1)]],
        'U': [[(0, 0), (0, .76), (.24, 1), (.76, 1), (1, .76), (1, 0)],
              [(.53, -.19), (.77, -.45)]],
        'S': [[(1, 0), (0, 0), (1, 1), (0, 1)]],
        'E': [[(1, 0), (0, 0), (0, 1), (1, 1)], [(.10, .61), (.55, .28)]],
        'C': [[(1, .02), (.35, .02), (0, .29), (0, .76), (.30, 1), (.92, 1), (1, .91)]],
        'A': [[(0, 1), (1, 0), (1, 1), (.20, .17), (.20, .77)]],
    }
    glyph_width, glyph_height, gap = 100, 86, 28
    total = 6 * glyph_width + 5 * gap
    start = (1024 - total) / 2
    for index, letter in enumerate('MUSECA'):
        x0 = start + index * (glyph_width + gap)
        for path in paths[letter]:
            draw.line([(round(x0 + x * glyph_width), round(79 + y * glyph_height))
                       for x, y in path], fill=(36, 38, 43), width=3)
    draw.rectangle((824, 178, 959, 200), outline=(76, 77, 74), width=1)
    _label(branding, (892, 189), 'BEMANI', 17, (65, 68, 67), True)
    # Fine diagonal is part of the printed sign rather than extra typography.
    draw.line((963, 54, 998, 37, 998, 79), fill=(95, 96, 93), width=1)
    return branding


def build_textures(textures):
    """Write materials256², details512², branding1024x256 and return palette."""
    textures = Path(textures)
    textures.mkdir(parents=True, exist_ok=True)
    _materials().save(textures / 'museca_materials.png')
    _details().save(textures / 'museca_details.png')
    _branding().save(textures / 'museca_branding.png')
    return dict(PALETTE), list(KEYS)
