"""Native hardware atlases for the Chunithm Paradise Lost cabinet.

These manufactured materials, printed trim and individual LED lamps are drawn
procedurally. The separately generated display and marquee artwork is untouched.
Atlas coordinates below are native pixels; callers inset each region by 8 pixels
(.25 model UV on a 512px atlas) to avoid sampling its neighbouring regions.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PALETTE = {
    'black': (16, 18, 25), 'charcoal': (31, 32, 42),
    'white': (230, 233, 229), 'ivory': (213, 217, 212),
    'silver': (167, 178, 187), 'steel': (78, 88, 99),
    'rubber': (8, 10, 17), 'vent': (20, 23, 30),
    'magenta': (191, 28, 166), 'pink': (242, 91, 220),
    'cyan': (58, 208, 233), 'purple': (109, 41, 213),
    'blue': (37, 43, 169), 'rim_gray': (191, 199, 200),
    'green': (57, 224, 112), 'black_mesh': (25, 28, 35),
}
KEYS = list(PALETTE)


def _label(image, xy, text, size, color, bold=False):
    """Use a binary mask so small printed lettering has crisp pixel edges."""
    filename = 'consolab.ttf' if bold else 'consola.ttf'
    try:
        font = ImageFont.truetype(str(Path('C:/Windows/Fonts') / filename), size)
    except OSError:
        font = ImageFont.load_default(size=size)
    mask = Image.new('1', image.size)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=1, anchor='mm')
    if image.mode == 'RGBA' and len(color) == 3:
        color = (*color, 255)
    image.paste(color, (0, 0), mask)


def _material_atlas():
    atlas = Image.new('RGB', (256, 256))
    rng = random.Random(710)
    for index, name in enumerate(KEYS):
        base = PALETTE[name]
        tile = Image.new('RGB', (64, 64), base)
        draw = ImageDraw.Draw(tile)
        for y in range(0, 64, 4):
            for x in range(0, 64, 4):
                variation = rng.choice((-2, 0, 0, 2))
                color = tuple(max(0, min(255, c + variation)) for c in base)
                draw.rectangle((x, y, x + 3, y + 3), fill=color)
        # White and ivory are plain powder-coated metal. Do not inherit the
        # patterned WACCA ivory tile: Chunithm's lower enclosure is unprinted.
        if name == 'vent':
            for y in range(3, 64, 6):
                for x in range(3, 64, 8):
                    draw.rectangle((x, y, x + 5, y + 2), fill=(5, 8, 13))
                    draw.line((x, y + 3, x + 5, y + 3), fill=(32, 36, 42))
        elif name == 'black_mesh':
            for y in range(2, 64, 5):
                offset = 2 if (y // 5) % 2 else 0
                for x in range(2 + offset, 64, 5):
                    draw.rectangle((x, y, x + 2, y + 2), fill=(6, 9, 14))
                    draw.point((x + 3, y + 2), fill=(43, 47, 54))
        atlas.paste(tile, ((index % 4) * 64, (index // 4) * 64))
    return atlas


def _flower(draw, x, y, radius, color, outline):
    """Small angular petal print, rather than noisy pixels or a photo texture."""
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        points = []
        for distance, delta in ((2, 0), (radius * .65, -.38),
                                (radius, 0), (radius * .65, .38)):
            points.append((round(x + distance * math.cos(a + delta)),
                           round(y + distance * math.sin(a + delta))))
        draw.polygon(points, fill=color, outline=outline)
    draw.rectangle((x - 2, y - 2, x + 2, y + 2), fill=(246, 232, 193))


def _speaker_print():
    band = Image.new('RGB', (512, 128), (219, 225, 218))
    draw = ImageDraw.Draw(band)
    # Broad low-contrast colour shapes remain readable behind the speaker pods.
    for x in range(-40, 560, 80):
        draw.polygon(((x, 0), (x + 40, 0), (x + 108, 127), (x + 64, 127)),
                     fill=(236, 208, 220))
        draw.line(((x + 15, 0), (x + 69, 70), (x + 58, 127)),
                  fill=(193, 218, 209), width=3)
    for x, y, radius in ((30, 40, 21), (97, 91, 22), (169, 37, 23),
                          (241, 93, 20), (306, 37, 23), (378, 89, 22),
                          (449, 35, 23), (503, 100, 20)):
        _flower(draw, x, y, radius, (233, 178, 199), (190, 145, 170))
        draw.arc((x - 32, y - 30, x + 38, y + 34), 35, 256,
                 fill=(177, 203, 193), width=2)
    for x in range(16, 512, 48):
        y = 18 if (x // 48) % 2 else 111
        draw.polygon(((x, y - 5), (x + 3, y), (x, y + 5), (x - 3, y)),
                     fill=(249, 237, 211))
    draw.line((8, 9, 503, 9), fill=(246, 235, 223), width=2)
    draw.line((8, 118, 503, 118), fill=(180, 166, 181), width=2)
    return band


def _wing_print():
    # Clear acrylic is represented by empty alpha, not a dark opaque wall or
    # semitransparent smoke. Only the screen-printed technical marks are visible.
    # 8..248 U and 8..376 V map to physical Z=-5.6..14, Y=42.3..16.6.
    # Working in cabinet coordinates keeps this print aligned with the elbow,
    # upper icon column and lower sensing area when the acrylic is reshaped.
    wing = Image.new('RGBA', (256, 384), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wing)
    cyan = (92, 184, 195, 255)
    pale = (190, 220, 222, 255)
    dim = (123, 165, 177, 255)

    def point(z, y):
        return (round(8 + (z + 5.6) / 19.6 * 240),
                round(8 + (42.3 - y) / 25.7 * 368))

    def line(points, color=dim, width=1):
        draw.line([point(z, y) for z, y in points], fill=color, width=width)

    def arc(center, radius, start, end, color=cyan, width=1):
        steps = max(2, math.ceil((end - start) / 4))
        line([(center[0] + radius * math.cos(math.radians(start + (end - start) * i / steps)),
               center[1] + radius * math.sin(math.radians(start + (end - start) * i / steps)))
              for i in range(steps + 1)], color, width)

    def node(center, radius=.25):
        arc(center, radius, 0, 360, pale)
        arc(center, radius * .56, 0, 360, cyan)

    # The reference has one prominent broken annulus at the forward elbow,
    # rather than repeated equal-sized circles all the way down the acrylic.
    centre = (-2.0, 29.5)
    for start, end in ((-28, 51), (85, 170), (206, 282)):
        arc(centre, 3.0, start, end, dim)
        outer = [(centre[0] + 2.66 * math.cos(math.radians(a)),
                  centre[1] + 2.66 * math.sin(math.radians(a)))
                 for a in range(start, end + 1, 2)]
        inner = [(centre[0] + 2.12 * math.cos(math.radians(a)),
                  centre[1] + 2.12 * math.sin(math.radians(a)))
                 for a in reversed(range(start, end + 1, 2))]
        draw.polygon([point(z, y) for z, y in outer + inner], fill=cyan)
    arc(centre, .47, 0, 360, pale)
    arc(centre, .29, 0, 360, cyan)
    # Fine connector lines lead to the real acrylic's upper and lower targets.
    line([centre, (-3.55, 32.0), (6.95, 40.75), (9.35, 40.75)], pale)
    line([centre, (8.7, 25.7), (.55, 17.8)], pale)
    line([centre, (-.25, 22.5), (.55, 17.8)], dim)
    for target in ((9.35, 40.75), (8.7, 25.7), (.55, 17.8)):
        node(target, .34)

    # Four compact printed technology icons, as on the upper rear of the
    # photographed clear wing: controls, air, slider and waveform.
    for index, y in enumerate((39.15, 37.65, 36.15, 34.65)):
        z = 8.0
        arc((z, y), .63, 0, 360, cyan)
        if index == 0:
            for dz, dy in ((-.27, .15), (.27, .15), (0, -.22)):
                node((z + dz, y + dy), .13)
        elif index == 1:
            line([(z - .32, y - .20), (z - .15, y + .27),
                  (z, y - .05), (z + .15, y + .27), (z + .32, y - .20)], pale)
        elif index == 2:
            line([(z - .36, y + .18), (z + .36, y + .18),
                  (z + .36, y - .16), (z - .36, y - .16),
                  (z - .36, y + .18)], pale)
            for dz in (-.12, .12):
                line([(z + dz, y + .14), (z + dz, y - .12)], cyan)
        else:
            for offset, height in ((-.32, .09), (-.16, .22), (0, .34),
                                   (.16, .22), (.32, .09)):
                line([(z + offset, y - height), (z + offset, y + height)], pale)

    # A fine triangular range grid occupies only the low sensing area. The
    # surrounding acrylic stays clear, with no smoked fill or alpha dither.
    triangle = [(1.4, 25.0), (7.4, 25.0), (2.7, 18.7), (1.4, 25.0)]
    line(triangle, dim)
    for index in range(16):
        y = 20.0 + index * .30
        if 22.05 < y < 22.85:
            continue  # Quiet band behind the small printed sensing-range label.
        t = (25.0 - y) / 6.3
        left = 1.4 + 1.3 * t
        right = 7.4 - 4.7 * t
        line([(left, y), (right, y)], dim)
    for z in (2.9, 4.4, 5.9):
        line([(z, 24.9), (2.7, 18.8)], dim)
    _label(wing, point(4.5, 22.45), 'Sensing Range', 8, pale, True)
    _label(wing, point(5.7, 26.2), 'AIR', 8, pale, True)
    _label(wing, point(7.9, 33.50), 'AIR SENSING', 6, cyan, True)
    return wing


def _details_atlas():
    details = Image.new('RGBA', (512, 512), (*PALETTE['black'], 255))
    details.paste(_speaker_print(), (0, 0))
    details.paste(_wing_print(), (0, 128))
    draw = ImageDraw.Draw(details)
    # Central factory reader. Its title and target fit the model's narrower
    # 272..368 horizontal sampling footprint as well as the 8px regional guard.
    draw.rectangle((256, 128, 383, 223), fill=(236, 232, 230))
    draw.rectangle((274, 137, 365, 214), outline=(209, 108, 161), width=2)
    draw.rectangle((275, 138, 364, 144), fill=(199, 57, 131))
    _label(details, (320, 165), 'Aime', 24, (185, 49, 125), True)
    draw.rectangle((304, 184, 329, 201), outline=(169, 71, 128), width=2)
    draw.line((307, 189, 326, 189), fill=(201, 129, 167), width=2)
    for radius in (6, 10, 14):
        draw.arc((326 - radius, 188 - radius, 326 + radius, 188 + radius),
                 290, 70, fill=(169, 71, 128), width=1)
    # Narrow dark strip under the LED matrix; leave an 8px border throughout.
    draw.rectangle((256, 224, 511, 255), fill=(13, 20, 29))
    _label(details, (384, 240), 'VISUALIZE SYSTEM', 13, (168, 216, 219), True)
    draw.line((268, 239, 310, 239), fill=(53, 116, 129), width=1)
    draw.line((458, 239, 499, 239), fill=(53, 116, 129), width=1)
    return details


def _led_matrix():
    matrix = Image.new('RGB', (384, 512), (7, 13, 23))
    draw = ImageDraw.Draw(matrix)
    # Sixteen physical columns and thirty-two rows. A deliberate standing light
    # pattern leaves some lamps dim while the lower rows shift violet to rose.
    # Flat stepped halos keep the lamps pixel-like; no speckled noise or blur.
    for row in range(32):
        y = round(8 + (row + .5) * 496 / 32)
        for column in range(16):
            x = round(8 + (column + .5) * 368 / 16)
            bottom = max(0, min(1, (row - 19) / 12))
            pulse = math.cos(column * .52 + row * .20)
            bright = pulse > -.54 or (column + row) % 9 == 0
            violet = row >= 21 and (column < 3 or column > 12 or row > 25)
            if not bright:
                edge, body, core = (10, 24, 35), (18, 53, 68), (33, 86, 104)
            elif violet:
                edge = (25, 17, 56)
                body = (round(104 + 105 * bottom), 71, round(239 - 21 * bottom))
                core = (round(200 + 49 * bottom), round(159 + 28 * bottom), 250)
            else:
                edge, body, core = (10, 43, 58), (40, 181, 217), (195, 250, 253)
            draw.rectangle((x - 7, y - 5, x + 7, y + 5), fill=edge)
            draw.rectangle((x - 5, y - 4, x + 5, y + 4), fill=body)
            draw.rectangle((x - 3, y - 3, x + 3, y + 3), fill=core)
            if bright:
                draw.rectangle((x - 1, y - 2, x + 1, y + 2), fill=(236, 253, 251))
    return matrix


def _slider_strip():
    strip = Image.new('RGB', (128, 128), (187, 37, 132))
    draw = ImageDraw.Draw(strip)
    for top, bottom, color in (
        (8, 119, (224, 75, 177)), (13, 114, (253, 139, 212)),
        (17, 110, (251, 219, 236)), (23, 104, (240, 136, 204)),
        (34, 93, (248, 167, 220)), (48, 79, (255, 202, 233)),
        (57, 70, (255, 225, 241)),
    ):
        draw.rectangle((8, top, 119, bottom), fill=color)
    # Subtle glass edges, leaving the central sensing surface uninterrupted.
    draw.line((8, 20, 119, 20), fill=(255, 245, 246), width=3)
    draw.line((8, 107, 119, 107), fill=(255, 245, 246), width=3)
    return strip


def _air_lamps():
    lamps = Image.new('RGB', (64, 384), (8, 32, 42))
    draw = ImageDraw.Draw(lamps)
    draw.rectangle((21, 8, 42, 375), fill=(13, 67, 83))
    draw.line((23, 8, 23, 375), fill=(37, 136, 151), width=2)
    draw.line((40, 8, 40, 375), fill=(37, 136, 151), width=2)
    for index in range(16):
        y = round(8 + (index + .5) * 368 / 16)
        draw.rectangle((26, y - 7, 37, y + 7), fill=(30, 166, 195))
        draw.rectangle((28, y - 5, 35, y + 5), fill=(171, 245, 246))
        draw.rectangle((30, y - 3, 33, y + 3), fill=(241, 255, 251))
    return lamps


def _lights_atlas():
    lights = Image.new('RGB', (512, 512), PALETTE['black'])
    lights.paste(_led_matrix(), (0, 0))
    lights.paste(_slider_strip(), (384, 0))
    lights.paste(_air_lamps(), (384, 128))
    return lights


def build_textures(textures):
    """Write the three hardware atlases and return the ordered material palette."""
    textures = Path(textures)
    textures.mkdir(parents=True, exist_ok=True)
    _material_atlas().save(textures / 'chunithm_materials.png')
    _details_atlas().save(textures / 'chunithm_details.png')
    _lights_atlas().save(textures / 'chunithm_lights.png')
    return dict(PALETTE), list(KEYS)
