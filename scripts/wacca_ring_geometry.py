"""Fine WACCA touch-bowl courses with a continuous native LED texture.

Depth includes the cabinet's backward lean before it is quantized. Coplanar
neighbours can therefore merge without changing either silhouette or texture
placement. The returned cuboids must not pass through another lean transform.
"""

import math
from pathlib import Path

from PIL import Image


CENTER_X, CENTER_Y = 8.0, 28.2
OUTER_RADIUS, INNER_RADIUS = 10.32, 6.23
XY_STEP, DEPTH_STEP = .25, .125
GRID_SPAN = 22.0
GRID_MIN_X, GRID_MIN_Y = -3.0, 17.2
GRID_MAX_Y = 39.2
GRID_COUNT = 88
BACK_DEPTH = 9.98
SECTOR_COUNT = 60

# Preserve the existing attraction-screen colours: blue/violet around most of
# the ring, magenta at the lower right, and a short cyan section at the bottom.
LED_COLORS = ((35, 25, 146), (37, 25, 103), (89, 32, 180), (67, 24, 130),
              (211, 28, 181), (141, 25, 144), (26, 161, 199), (21, 104, 148))


def _sector_style(x, y):
    radius = math.hypot(x-CENTER_X, y-CENTER_Y)
    angle = math.atan2(x-CENTER_X, y-CENTER_Y) % math.tau
    position = angle/math.tau*SECTOR_COUNT
    sector = int(position)
    fraction = position-sector
    radial = max(0.0, min(1.0, (OUTER_RADIUS-radius)/(OUTER_RADIUS-INNER_RADIUS)))
    band = min(7, int(radial*8))
    swatch = 2 if sector % 9 in (0, 1, 2, 6) else 0
    if sector % 7 in (3, 4):
        swatch += 1
    if 19 <= sector <= 28 and band <= 5:
        swatch = 4+int(sector % 4 == 0)
    if 29 <= sector <= 31 and band <= 6:
        swatch = 6
    if 32 <= sector <= 38 and band < 3:
        swatch = 2
    if sector in (7, 8, 45, 46, 56):
        swatch = 1
    return radius, fraction, LED_COLORS[swatch]


def _write_led_atlas(texture_dir):
    """Draw the LED lens detail once in XY space instead of once per cuboid."""
    size = 512
    texture = Image.new('RGB', (size, size))
    pixels = texture.load()
    for py in range(size):
        y = GRID_MAX_Y-(py+.5)/size*GRID_SPAN
        for px in range(size):
            x = GRID_MIN_X+(px+.5)/size*GRID_SPAN
            radius, fraction, base = _sector_style(x, y)
            # Physical seam width stays approximately constant around the cone.
            # Colour is continued outside the nominal radii so staircase edges
            # never sample a black texture border or an unrelated atlas cell.
            arc_width = max(INNER_RADIUS, radius)*math.tau/SECTOR_COUNT
            seam_distance = min(fraction, 1-fraction)*arc_width
            if seam_distance < .029:
                colour = (12, 11, 31)
            else:
                radial_distance = OUTER_RADIUS-radius
                radial_phase = radial_distance % .125
                angular_phase = (fraction*arc_width) % .15
                delta = -17 if radial_phase < .021 else 0
                if angular_phase < .018:
                    delta += 10
                colour = tuple(max(0, min(255, c+delta)) for c in base)
            pixels[px, py] = colour
    directory = Path(texture_dir)
    directory.mkdir(parents=True, exist_ok=True)
    texture.save(directory/'wacca_leds.png')


def _depth_cells():
    """Return exact visible cell coverage and the final, quantized front plane."""
    rows = []
    for row in range(GRID_COUNT):
        y = GRID_MIN_Y+(row+.5)*XY_STEP
        cells = []
        for col in range(GRID_COUNT):
            x = GRID_MIN_X+(col+.5)*XY_STEP
            radius = math.hypot(x-CENTER_X, y-CENTER_Y)
            if not INNER_RADIUS <= radius <= OUTER_RADIUS:
                cells.append(None)
                continue
            final_z = 1.65+(OUTER_RADIUS-radius)*1.04+(y-17.2)*.10
            cells.append(round(final_z/DEPTH_STEP))
        rows.append(cells)
    return rows


def _merge_depth_cells(rows):
    """Merge horizontal runs and then identical runs on consecutive scanlines."""
    rectangles, active = [], {}
    for row_index, row in enumerate(rows):
        following = {}
        col = 0
        while col < GRID_COUNT:
            depth = row[col]
            if depth is None:
                col += 1
                continue
            left = col
            while col < GRID_COUNT and row[col] == depth:
                col += 1
            key = (left, col, depth)
            if key in active:
                rectangle = active.pop(key)
                rectangle[3] = row_index+1
            else:
                rectangle = [left, col, row_index, row_index+1, depth]
            following[key] = rectangle
        rectangles.extend(active.values())
        active = following
    rectangles.extend(active.values())
    return sorted(rectangles, key=lambda value: (value[2], value[0], value[4]))


def _validate_coverage(rows, rectangles):
    """Guard against holes, overlap, and accidental merging across depth steps."""
    covered = {}
    for left, right, bottom, top, depth in rectangles:
        assert left < right and bottom < top
        assert depth*DEPTH_STEP < BACK_DEPTH
        for row in range(bottom, top):
            for col in range(left, right):
                assert (row, col) not in covered, 'Overlapping touch-bowl rectangles'
                assert rows[row][col] == depth, 'Touch-bowl rectangle crossed a depth step'
                covered[row, col] = depth
    expected = {(row, col): depth for row, cells in enumerate(rows)
                for col, depth in enumerate(cells) if depth is not None}
    assert covered == expected, 'Touch-bowl merging changed the annular silhouette'
    # The inward depth gradient is 1.04 minus the lean contribution, whose
    # maximum magnitude is .10; quantization preserves its monotonic ordering.
    for sector in range(SECTOR_COUNT):
        angle = sector/SECTOR_COUNT*math.tau
        previous = -math.inf
        for sample in range(65):
            radius = OUTER_RADIUS-(OUTER_RADIUS-INNER_RADIUS)*sample/64
            y = CENTER_Y+radius*math.cos(angle)
            depth = round((1.65+(OUTER_RADIUS-radius)*1.04+(y-17.2)*.10)/DEPTH_STEP)
            assert depth >= previous, 'Touch bowl must recede continuously inward'
            previous = depth


def build_touch_bowl(cube, texture_dir):
    """Write the continuous LED atlas and emit already-leaned bowl cuboids."""
    _write_led_atlas(texture_dir)
    cells = _depth_cells()
    rectangles = _merge_depth_cells(cells)
    _validate_coverage(cells, rectangles)
    for index, (left, right, bottom, top, depth) in enumerate(rectangles):
        x0, x1 = GRID_MIN_X+left*XY_STEP, GRID_MIN_X+right*XY_STEP
        y0, y1 = GRID_MIN_Y+bottom*XY_STEP, GRID_MIN_Y+top*XY_STEP
        u0, u1 = (x0-GRID_MIN_X)/GRID_SPAN*16, (x1-GRID_MIN_X)/GRID_SPAN*16
        v0, v1 = (GRID_MAX_Y-y1)/GRID_SPAN*16, (GRID_MAX_Y-y0)/GRID_SPAN*16
        cube('Continuous touch bowl patch %04d'%index,
             (x0, y0, depth*DEPTH_STEP), (x1, y1, BACK_DEPTH), 'black',
             north=('leds', [u0, v0, u1, v1]),
             up=('leds', [u0, v0, u1, v0]),
             down=('leds', [u0, v1, u1, v1]),
             east=('leds', [u1, v0, u1, v1]),
             west=('leds', [u0, v0, u0, v1]),
             glow=('north', 'up', 'down', 'east', 'west'),
             group='Segmented touch bowl')
    return {'cells': sum(cell is not None for row in cells for cell in row),
            'cuboids': len(rectangles), 'grid_step': XY_STEP, 'depth_step': DEPTH_STEP}
