"""Procedural manufactured textures for the classic Groove Coaster cabinet.

The portrait gameplay source is generated separately and never opened here.
Hardware faces sample the documented atlas regions with an eight-pixel inset.
Only the clear top-deck print uses transparent pixels; all other regions are
opaque. Printed and luminous lines use hard pixel edges without alpha haze.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

from chunithm_textures import KEYS, PALETTE, _label, _material_atlas


_LETTERS = {
    'G': ('01110', '10001', '10000', '10111', '10001', '10001', '01110'),
    'R': ('11110', '10001', '10001', '11110', '10100', '10010', '10001'),
    'O': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    'V': ('10001', '10001', '10001', '10001', '10001', '01010', '00100'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'C': ('01111', '10000', '10000', '10000', '10000', '10000', '01111'),
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'S': ('01111', '10000', '10000', '01110', '00001', '00001', '11110'),
    'T': ('11111', '00100', '00100', '00100', '00100', '00100', '00100'),
}


def _invader(draw, centre, color, scale=2):
    bitmap = ('00100000100', '00010001000', '00111111100', '01101110110',
              '11111111111', '10111111101', '10100000101', '00011011000')
    x0 = round(centre[0] - 11 * scale / 2)
    y0 = round(centre[1] - 8 * scale / 2)
    for row, bits in enumerate(bitmap):
        for column, bit in enumerate(bits):
            if bit == '1':
                x, y = x0 + column * scale, y0 + row * scale
                draw.rectangle((x, y, x + scale - 1, y + scale - 1), fill=color)


def _branding_atlas():
    branding = Image.new('RGB', (1024, 256), PALETTE['black'])
    draw = ImageDraw.Draw(branding)
    draw.rectangle((0, 0, 767, 127), fill=(23, 26, 46))
    # Smoked blue sign with thin clipped-corner acrylic edge lighting. The
    # 752x112 inset is deliberately close to the model's 6.68:1 sign proportion.
    outline = ((24, 10), (741, 10), (757, 26), (757, 101),
               (742, 117), (25, 117), (10, 101), (10, 25), (24, 10))
    draw.line(outline, fill=(124, 77, 207), width=3)
    draw.line(((27, 14), (739, 14), (752, 27)), fill=(135, 171, 238), width=1)
    draw.line(((25, 113), (740, 113), (753, 100)), fill=(94, 73, 166), width=1)
    _invader(draw, (384, 29), (163, 193, 251), scale=2)

    text = 'GROOVE COASTER'
    columns = sum(3 if char == ' ' else 6 for char in text) - 1
    pitch_x, pitch_y = 8, 5
    x0 = round((768 - (columns - 1) * pitch_x) / 2)
    cursor = 0
    for char in text:
        if char == ' ':
            cursor += 3
            continue
        for row, bits in enumerate(_LETTERS[char]):
            for column, bit in enumerate(bits):
                x, y = x0 + (cursor + column) * pitch_x, 49 + row * pitch_y
                if bit == '1':
                    # A low-contrast surrounding pixel and a square bright core
                    # give the physical dot lamps depth without blurry glow.
                    draw.rectangle((x - 2, y - 2, x + 2, y + 2), fill=(76, 57, 118))
                    color = (176, 150, 239) if row > 2 else (151, 190, 247)
                    draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=color)
                else:
                    draw.point((x, y), fill=(37, 37, 62))
        cursor += 6
    _label(branding, (384, 101), 'TAITO', 11, (155, 191, 232), True)
    return branding


def _details_atlas():
    details = Image.new('RGB', (512, 512), PALETTE['black'])
    draw = ImageDraw.Draw(details)
    # Reader display: sparse pale green/cyan LCD, set inside a black bezel.
    draw.rectangle((8, 8, 119, 119), fill=(5, 10, 15))
    draw.rectangle((13, 15, 114, 103), fill=(57, 91, 91))
    draw.rectangle((17, 19, 110, 99), fill=(207, 242, 224))
    draw.rectangle((20, 22, 107, 27), fill=(235, 251, 238))
    _label(details, (64, 44), 'CARD', 11, (53, 99, 95), True)
    draw.rectangle((49, 56, 74, 76), outline=(72, 130, 118), width=2)
    draw.line((52, 61, 71, 61), fill=(84, 150, 134), width=2)
    _label(details, (64, 88), 'TOUCH', 8, (66, 123, 111))
    draw.rectangle((59, 110, 68, 112), fill=(102, 213, 212))

    # Black headphone panel with brushed outline and socket/volume marks.
    draw.rectangle((136, 8, 247, 119), fill=(28, 30, 43))
    draw.line(((146, 14), (236, 14), (241, 19), (241, 107),
               (236, 113), (146, 113), (141, 108), (141, 19), (146, 14)),
              fill=(139, 151, 166), width=2)
    for x in (146, 236):
        for y in (20, 107):
            draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=(190, 198, 207))
    draw.arc((164, 28, 208, 71), 180, 360, fill=(219, 222, 231), width=4)
    draw.line((164, 48, 164, 68), fill=(219, 222, 231), width=3)
    draw.line((208, 48, 208, 68), fill=(219, 222, 231), width=3)
    draw.rectangle((164, 57, 171, 75), fill=(185, 194, 212))
    draw.rectangle((201, 57, 208, 75), fill=(185, 194, 212))
    draw.ellipse((182, 64, 191, 73), fill=(6, 8, 15), outline=(104, 121, 143), width=1)
    for x, height in ((219, 8), (225, 12), (231, 17)):
        draw.rectangle((x, 71 - height, x + 2, 71), fill=(140, 157, 182))
    _label(details, (192, 91), 'HEADPHONE', 10, (192, 204, 220), True)

    # Small manufacturer/service print for rear panels; no decorative posters.
    draw.rectangle((264, 8, 503, 119), fill=(156, 168, 175))
    draw.rectangle((268, 12, 499, 115), outline=(44, 52, 68), width=1)
    _label(details, (384, 29), 'TAITO', 18, (24, 48, 83), True)
    _label(details, (384, 51), 'GROOVE COASTER', 13, (31, 43, 62), True)
    draw.line((278, 65, 489, 65), fill=(89, 107, 121), width=1)
    _label(details, (384, 80), 'SERVICE / POWER', 10, (32, 40, 51))
    _label(details, (384, 101), 'CAUTION  -  ELECTRICAL', 9, (41, 48, 58))
    return details


def _bezier(a, b, c, d, steps=64):
    points = []
    for i in range(steps + 1):
        t = i / steps
        s = 1 - t
        points.append((s**3*a[0] + 3*s*s*t*b[0] + 3*s*t*t*c[0] + t**3*d[0],
                       s**3*a[1] + 3*s*s*t*b[1] + 3*s*t*t*c[1] + t**3*d[1]))
    return points


def _wing_lights():
    wing = Image.new('RGB', (256, 512), (34, 29, 124))
    draw = ImageDraw.Draw(wing)
    # Blue/purple printed acrylic, using broad quantised shading rather than
    # per-pixel noise. Atlas X follows cabinet Z, Y follows its vertical height.
    for y in range(0, 512, 8):
        for x in range(0, 256, 8):
            sweep = math.sin(x / 98 + y / 275)
            color = (round(35 + 9 * sweep), round(35 + 16 * sweep),
                     round(138 + 32 * sweep))
            draw.rectangle((x, y, x + 7, y + 7), fill=color)
    for x in range(12, 256, 16):
        draw.line((x, 8, x, 503), fill=(68, 76, 160), width=1)
    for y in range(16, 512, 24):
        draw.line((8, y, 247, y), fill=(66, 64, 152), width=1)

    # Nested white and cyan rails bend continuously over the upper shoulder and
    # down the tall lower cheek, as on the original illuminated blue side art.
    path = _bezier((28, 503), (28, 390), (26, 333), (63, 270))
    path += _bezier((63, 270), (94, 222), (174, 153), (183, 83))[1:]
    path += _bezier((183, 83), (190, 23), (154, 15), (104, 15))[1:]
    for offset, color, width in (
        (0, (177, 199, 253), 3), (7, (109, 204, 240), 1),
        (14, (232, 236, 255), 2), (22, (126, 161, 236), 1),
        (29, (188, 207, 253), 2), (35, (111, 139, 221), 1),
    ):
        shifted = [(round(x + offset), round(y)) for x, y in path]
        draw.line(shifted, fill=color, width=width)
    draw.line(((8, 498), (8, 304), (42, 238)), fill=(125, 144, 229), width=1)
    draw.line(((247, 498), (247, 234), (231, 202)), fill=(165, 173, 242), width=2)
    for x, y in ((56, 416), (104, 248), (198, 112)):
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(154, 207, 249), width=1)
        draw.line((x + 5, y, min(244, x + 32), y), fill=(110, 163, 226), width=1)
    return wing


def _booster_lights():
    booster = Image.new('RGB', (256, 128), (113, 132, 238))
    draw = ImageDraw.Draw(booster)
    # Opal cylinders show repeated vertical light bands, not discrete buttons.
    for x in range(256):
        wave = max(0, math.cos((x - 9) * math.tau / 52)) ** 2
        color = (round(108 + 119 * wave), round(119 + 127 * wave),
                 round(228 + 27 * wave))
        draw.line((x, 0, x, 127), fill=color)
    for y, color in ((8, (182, 211, 255)), (12, (240, 252, 253)),
                      (114, (231, 245, 252)), (119, (171, 196, 248))):
        draw.line((8, y, 247, y), fill=color, width=2)
    return booster


def _clear_deck():
    deck = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(deck)
    dim = (130, 174, 222, 255)
    bright = (202, 231, 253, 255)
    # Keep the clear field empty; only the printed rails, grid and tiny target
    # rings are opaque, avoiding a smoked sheet over the cabinet's open centre.
    draw.line(((12, 111), (12, 34), (30, 16), (224, 16), (243, 35),
               (243, 111)), fill=bright, width=2)
    draw.line(((19, 109), (19, 38), (35, 23), (218, 23), (236, 40),
               (236, 109)), fill=dim, width=1)
    for x in range(39, 237, 20):
        draw.line((x, 29, x, 109), fill=dim, width=1)
    for y in (43, 61, 79, 97):
        draw.line((26, y, 229, y), fill=dim, width=1)
    for x in (58, 196):
        draw.ellipse((x - 17, 47, x + 17, 81), outline=bright, width=2)
        draw.ellipse((x - 12, 52, x + 12, 76), outline=dim, width=1)
        draw.line((x - 21, 64, x + 21, 64), fill=bright, width=1)
    return deck


def _lights_atlas():
    lights = Image.new('RGBA', (512, 512), (*PALETTE['black'], 255))
    lights.paste(_wing_lights(), (0, 0))
    lights.paste(_booster_lights(), (256, 0))
    lights.paste(_clear_deck(), (256, 128))
    draw = ImageDraw.Draw(lights)
    # Four reserved opaque neon colour swatches, each with a broad interior.
    for box, color in (
        ((256, 256, 383, 383), (163, 142, 245, 255)),
        ((384, 256, 511, 383), (101, 216, 247, 255)),
        ((256, 384, 383, 511), (219, 235, 255, 255)),
        ((384, 384, 511, 511), (79, 72, 197, 255)),
    ):
        draw.rectangle(box, fill=color)
    return lights


def build_textures(textures):
    """Write all four hardware atlases; return the shared ordered palette."""
    textures = Path(textures)
    textures.mkdir(parents=True, exist_ok=True)
    _material_atlas().save(textures / 'groove_coaster_materials.png')
    _details_atlas().save(textures / 'groove_coaster_details.png')
    _lights_atlas().save(textures / 'groove_coaster_lights.png')
    _branding_atlas().save(textures / 'groove_coaster_branding.png')
    return dict(PALETTE), list(KEYS)
