"""Native pixel artwork for the Nostalgia cabinet's small manufactured surfaces.

These are drawn from geometry and a restrained palette, not raster edits of the
reference photographs or the separately generated marquee illustrations.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


IVORY = (225, 218, 199)
PAPER = (239, 232, 214)
GOLD = (172, 139, 76)
PALE_GOLD = (207, 184, 131)
GOLD_SHADOW = (126, 100, 57)
INK = (68, 65, 59)


def _label(im, xy, message, font, size, fill, *, serif=False, anchor='mm'):
    """Thresholded type keeps the art crisp rather than adding antialias colors."""
    mask = Image.new('1', im.size)
    ImageDraw.Draw(mask).text(xy, message, font=font(size, serif), fill=1, anchor=anchor)
    im.paste(fill, (0, 0), mask)


def _diamond(d, x, y, radius, color, *, fill=None):
    points = [(x, y-radius), (x+radius, y), (x, y+radius), (x-radius, y)]
    d.polygon(points, fill=fill)
    d.line(points + points[:1], fill=color, width=1)


def _star(d, x, y, r, color):
    d.line((x-r, y, x+r, y), fill=color)
    d.line((x, y-r, x, y+r), fill=color)
    if r > 3:
        d.line((x-2, y-2, x+2, y+2), fill=color)
        d.line((x-2, y+2, x+2, y-2), fill=color)


def _rosette(d, x, y, r, color, *, center=None):
    """Eight symmetric pointed leaves, used as the printed brass ornament."""
    for i in range(8):
        angle = i * math.pi / 4
        points = []
        for radius, delta in ((r*.38, -.2), (r, 0), (r*.38, .2)):
            points.append((round(x+math.cos(angle+delta)*radius),
                           round(y+math.sin(angle+delta)*radius)))
        d.line(points + points[:1], fill=color)
    d.ellipse((x-r*.26, y-r*.26, x+r*.26, y+r*.26), outline=color)
    _diamond(d, x, y, max(1, round(r*.13)), center or color)


def _scroll(d, x, y, length, color, *, flip=False):
    """A square-stepped mirrored acanthus-like printed curl."""
    direction = -1 if flip else 1
    points = [(0, 0), (length*.23, 0), (length*.35, -3),
              (length*.43, -7), (length*.62, -8), (length*.79, -5),
              (length*.8, 0), (length*.66, 3), (length*.57, 1),
              (length*.57, -2), (length*.67, -2)]
    d.line([(round(x+direction*a), round(y+b)) for a, b in points], fill=color)
    d.line([(round(x+direction*length*.27), y-1),
            (round(x+direction*length*.34), y+4),
            (round(x+direction*length*.51), y+5)], fill=color)


def _screw(d, x, y, dark=INK, light=PAPER):
    d.rectangle((x-2, y-2, x+2, y+2), fill=(161, 159, 148))
    d.line((x-1, y-2, x+1, y-2), fill=light)
    d.line((x-1, y, x+1, y), fill=dark)


def _rhythm(font):
    im = Image.new('RGB', (256, 160))
    d = ImageDraw.Draw(im)
    bands = [(18, 19, 39), (21, 20, 47), (27, 23, 59), (33, 26, 68),
             (39, 29, 80), (44, 32, 89), (42, 32, 82), (35, 30, 68)]
    for y in range(160):
        d.line((0, y, 255, y), fill=bands[min(7, y//20)])

    # Restrained stars and angular distant architecture behind the playfield.
    for x, y in ((36, 28), (52, 17), (207, 32), (184, 20), (31, 64),
                 (219, 69), (98, 17), (166, 16), (79, 53), (199, 91)):
        _star(d, x, y, 2 if y < 40 else 1, (116, 106, 155))
    skyline = (48, 40, 44, 31, 38, 34, 25, 43, 30, 47, 36, 51)
    for side in (0, 1):
        for i, h in enumerate(skyline):
            x = 4+i*4 if side == 0 else 251-i*4
            d.rectangle((x-2, 145-h, x+2, 145), fill=(46, 42, 78))
            d.polygon([(x-3, 145-h), (x, 138-h), (x+3, 145-h)], fill=(65, 53, 96))
            if i % 3 == 0:
                d.point((x, 149-h), fill=(177, 142, 144))

    # A rhythm highway narrows into the screen, towards the horizon.
    top_y, bottom_y = 24, 143
    left_top, right_top, left_bottom, right_bottom = 72, 184, 25, 231
    d.polygon([(left_top, top_y), (right_top, top_y),
               (right_bottom, bottom_y), (left_bottom, bottom_y)], fill=(31, 27, 57))
    for lane in range(8):
        x0 = left_top+(right_top-left_top)*lane/8
        x1 = left_top+(right_top-left_top)*(lane+1)/8
        b0 = left_bottom+(right_bottom-left_bottom)*lane/8
        b1 = left_bottom+(right_bottom-left_bottom)*(lane+1)/8
        if lane % 2:
            d.polygon([(x0, top_y), (x1, top_y), (b1, bottom_y), (b0, bottom_y)],
                      fill=(36, 30, 67))
    for y in (40, 60, 84, 112, 139):
        t = (y-top_y)/(bottom_y-top_y)
        a = round(left_top+(left_bottom-left_top)*t)
        b = round(right_top+(right_bottom-right_top)*t)
        d.line((a, y, b, y), fill=(66, 58, 98))
        d.line((a, y+1, b, y+1), fill=(28, 26, 54))
    for lane in range(9):
        x0 = round(left_top+(right_top-left_top)*lane/8)
        x1 = round(left_bottom+(right_bottom-left_bottom)*lane/8)
        color = (190, 164, 219) if lane in (0, 8) else (76, 65, 111)
        d.line((x0, top_y, x1, bottom_y), fill=color, width=1)

    # Notes have a tiny colored fringe and a bright one-pixel face, no blur.
    for lane, y, width in ((1, 54, 11), (5, 63, 13), (3, 80, 16),
                           (6, 96, 19), (2, 109, 20), (4, 128, 22), (1, 137, 22)):
        t = (y-top_y)/(bottom_y-top_y)
        left = left_top+(left_bottom-left_top)*t
        right = right_top+(right_bottom-right_top)*t
        center = round(left+(right-left)*(lane+.5)/8)
        d.rectangle((center-width//2-1, y-1, center+width//2+1, y+3), fill=(36, 101, 123))
        d.rectangle((center-width//2, y, center+width//2, y+2), fill=(98, 206, 224))
        d.line((center-width//2+1, y, center+width//2-1, y), fill=(221, 250, 245))

    # White-and-gold machine UI, following the sample's 280 / A composition.
    _label(im, (128, 38), '280', font, 14, (234, 221, 245), serif=True)
    _label(im, (128, 60), 'COMBO', font, 5, (180, 170, 202))
    _label(im, (128, 84), 'A', font, 23, (238, 202, 111), serif=True)
    for side in (-1, 1):
        for i in range(7):
            a = math.radians(25+i*18)
            x, y = 128+side*round(math.sin(a)*23), 81+round(math.cos(a)*23)
            d.polygon([(x, y), (x+side*5, y-2), (x+side*3, y-5)], fill=(191, 157, 80))
    _diamond(d, 128, 109, 3, (222, 190, 120))

    # The cabinet's floral clockwork border stays subordinate to the notes.
    for x in (17, 239):
        d.ellipse((x-11, 17, x+11, 39), outline=(134, 115, 143), width=1)
        d.ellipse((x-8, 20, x+8, 36), outline=(178, 153, 155), width=1)
        _rosette(d, x, 28, 6, (205, 181, 164))
        for y in (56, 75, 96, 118):
            _diamond(d, x, y, 2, (125, 105, 140))
        _scroll(d, x, 49, 15, (125, 105, 140), flip=x > 128)
        _scroll(d, x, 128, 17, (162, 138, 155), flip=x > 128)
    for x in range(11, 250, 13):
        d.arc((x-6, 5, x+6, 17), 180, 360, fill=(125, 104, 161))
        d.point((x, 11), fill=(223, 204, 231))
    d.line((7, 4, 248, 4), fill=(192, 158, 180))
    d.line((7, 14, 248, 14), fill=(82, 59, 111))
    d.line((3, 4, 3, 155), fill=(116, 90, 138))
    d.line((252, 4, 252, 155), fill=(116, 90, 138))

    d.rectangle((20, 144, 235, 146), fill=(62, 145, 178))
    d.line((21, 144, 234, 144), fill=(189, 240, 243))
    for x in (56, 184):
        d.rectangle((x-5, 141, x+5, 153), fill=(65, 151, 177))
        d.rectangle((x-3, 143, x+3, 152), fill=(130, 223, 226))
        d.rectangle((x-1, 145, x+1, 151), fill=(231, 253, 242))
    _label(im, (128, 154), 'NOSTALGIA  Op.3', font, 5, (187, 175, 211))
    _label(im, (29, 153), 'EXPERT', font, 5, (228, 204, 174), anchor='lm')
    _label(im, (228, 153), '100%', font, 5, (228, 204, 174), anchor='rm')
    return im


def _controls(font):
    im = Image.new('RGB', (512, 64), IVORY)
    d = ImageDraw.Draw(im)
    d.rectangle((2, 2, 509, 61), outline=GOLD)
    d.line((5, 5, 506, 5), fill=PAPER)
    d.line((5, 59, 506, 59), fill=(185, 172, 141))
    d.line((18, 14, 491, 14), fill=PALE_GOLD)
    for x in (11, 500):
        _screw(d, x, 9)
        _screw(d, x, 54)
    for x, width in ((25, 102), (381, 70)):
        d.rectangle((x, 25, x+width, 46), fill=(43, 44, 42))
        d.rectangle((x+2, 27, x+width-2, 32), fill=(221, 189, 77))
        for start in range(x+4, x+width-6, 12):
            d.line((start, 36, start+7, 36), fill=(210, 211, 190))
            d.line((start, 40, start+5, 40), fill=(153, 157, 148))
    _label(im, (76, 30), 'CAUTION', font, 6, (39, 38, 31))
    _label(im, (416, 30), 'NOTICE', font, 6, (39, 38, 31))
    _label(im, (251, 35), 'N O S T A L G I A', font, 15, (121, 100, 70), serif=True)
    _scroll(d, 172, 48, 36, PALE_GOLD)
    _scroll(d, 331, 48, 36, PALE_GOLD, flip=True)
    _diamond(d, 251, 50, 3, GOLD)
    d.rectangle((348, 25, 366, 43), fill=(185, 54, 61))
    d.line((353, 30, 353, 39), fill=PAPER, width=2)
    d.line((353, 30, 361, 28, 361, 37), fill=PAPER, width=2)
    d.rectangle((350, 38, 354, 40), fill=PAPER)
    d.rectangle((358, 36, 362, 38), fill=PAPER)
    # A coin/disc slot remains on the keyboard deck, not a separate card reader.
    d.rectangle((466, 23, 484, 48), fill=(129, 132, 130), outline=(90, 91, 86))
    d.line((468, 24, 482, 24), fill=(231, 231, 210))
    d.rectangle((473, 27, 477, 44), fill=(32, 34, 33))
    d.line((478, 28, 478, 42), fill=(225, 226, 211))
    return im


def _side(font):
    im = Image.new('RGB', (128, 512), IVORY)
    d = ImageDraw.Draw(im)
    d.rectangle((3, 3, 124, 508), outline=GOLD)
    d.rectangle((6, 6, 121, 505), outline=PAPER)
    d.rectangle((11, 11, 116, 500), outline=PALE_GOLD)
    for x in (17, 111):
        for y in (18, 494):
            _screw(d, x, y)
    # Sparse large-scale filigree, allowing the cabinet material to read clearly.
    for y in (83, 159, 352, 432):
        for x, flip in ((18, False), (110, True)):
            _scroll(d, x, y, 30, PALE_GOLD, flip=flip)
            _diamond(d, x, y+15, 4, GOLD)
            d.line((x, y+20, x, y+36), fill=PALE_GOLD)
            _star(d, x, y+42, 3, PALE_GOLD)
    _rosette(d, 64, 111, 30, GOLD)
    for x, y in ((43, 71), (85, 71), (43, 151), (85, 151)):
        _star(d, x, y, 4, PALE_GOLD)
    d.line((64, 35, 64, 65), fill=GOLD)
    _diamond(d, 64, 43, 5, GOLD)
    _diamond(d, 64, 178, 8, GOLD)
    d.line((64, 156, 64, 170), fill=GOLD)
    _label(im, (64, 233), 'NOSTALGIA', font, 15, (92, 77, 58), serif=True)
    _label(im, (64, 263), 'Op.3', font, 26, (110, 86, 61), serif=True)
    _label(im, (64, 286), 'N O S T A L G I A', font, 5, GOLD_SHADOW)
    for y in (210, 304):
        d.line((27, y, 101, y), fill=PALE_GOLD)
        _diamond(d, 64, y, 3, GOLD, fill=IVORY)
    _rosette(d, 64, 390, 24, PALE_GOLD)
    _diamond(d, 64, 390, 10, GOLD)
    d.line((64, 424, 64, 467), fill=PALE_GOLD)
    _diamond(d, 64, 471, 6, GOLD)
    for x, flip in ((59, True), (69, False)):
        _scroll(d, x, 485, 32, GOLD, flip=flip)
    return im


def _trim(font):
    im = Image.new('RGB', (512, 64), IVORY)
    d = ImageDraw.Draw(im)
    d.rectangle((1, 1, 510, 62), outline=GOLD_SHADOW)
    d.rectangle((3, 3, 508, 60), outline=PALE_GOLD)
    d.line((5, 5, 506, 5), fill=PAPER, width=2)
    d.line((5, 58, 506, 58), fill=GOLD)
    for x in (12, 500):
        _screw(d, x, 13)
        _screw(d, x, 50)
    for x in (61, 161, 351, 451):
        _rosette(d, x, 33, 15, PALE_GOLD, center=GOLD)
        _scroll(d, x-15, 36, 31, GOLD, flip=True)
        _scroll(d, x+15, 36, 31, GOLD)
        d.line((x-3, 12, x+3, 12), fill=GOLD)
        _diamond(d, x, 15, 2, PALE_GOLD)
    _label(im, (256, 28), 'Op.3', font, 23, GOLD, serif=True)
    _label(im, (256, 47), 'N O S T A L G I A', font, 6, GOLD_SHADOW)
    for x in (211, 301):
        _diamond(d, x, 29, 5, GOLD)
        _star(d, x, 47, 2, PALE_GOLD)
    return im


def build_surface_art(texture_dir: Path, palette, font):
    """Write four separate native atlases and return their logical UV sizes.

    The caller maps ``rhythm``, ``controls``, ``side`` and ``trim`` to these file
    names. Dimensions are non-square intentionally; Blockbench's texture records
    should use each returned width and height independently.
    """
    texture_dir = Path(texture_dir)
    texture_dir.mkdir(parents=True, exist_ok=True)
    textures = {
        'rhythm': ('nostalgia_rhythm.png', _rhythm(font)),
        'controls': ('nostalgia_controls.png', _controls(font)),
        'side': ('nostalgia_side_v2.png', _side(font)),
        'trim': ('nostalgia_trim_v2.png', _trim(font)),
    }
    sizes = {}
    for key, (filename, im) in textures.items():
        im.save(texture_dir / filename)
        sizes[key] = im.size
    return sizes
