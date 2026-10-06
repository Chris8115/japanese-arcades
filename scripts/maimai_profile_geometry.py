"""Shape maimai's continuous recline after extracting its exterior surfaces.

The upright lower face blends into an eight-degree upper face, while the rear
wall stays vertical. Shared curve endpoints keep the molded surface continuous;
the built-in NeoForge OBJ loader renders the actual inclined planes.
"""
import math
BEND_START = 13.0
BEND_END = 19.0
LEAN_DEGREES = 8.0
FRONT_RETURN = 1.23
REAR_WALL = 15.18


def recession(y):
    """Depth along a curve with continuous position, slope, and curvature."""
    if y <= BEND_START:
        return 0.0
    slope = math.tan(math.radians(LEAN_DEGREES))
    span = BEND_END - BEND_START
    if y >= BEND_END:
        return slope * (y - (BEND_START + BEND_END) / 2)
    t = (y - BEND_START) / span
    return span * slope * (t ** 3 - .5 * t ** 4)


def depth(z, shift):
    # Preserve the relief of buttons, lens glass, trim and payment hardware.
    # Only the deep enclosure tapers toward its unchanged rear service wall.
    weight = max(0.0, min(1.0, (REAR_WALL - z) / (REAR_WALL - FRONT_RETURN)))
    return z + shift * weight


def shape_point(point, group):
    x, y, z = point
    # Retain the canopy lip's own rolled-forward shape above the leaning face.
    if group == 'Wide coral DX canopy':
        return [x, y, z + recession(43.84)]
    return [x, y, depth(z, recession(y))]
