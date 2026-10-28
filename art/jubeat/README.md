# Jubeat arcade cabinet

A compact single cabinet based on the original black-and-blue Jubeat design:
a glass cube topper, upward-tilted silver speaker fronts, an inclined 4-by-4
panel grid, coin/card controls and a smaller glass display cube at the foot.

The model follows [KONAMI's original Jubeat cabinet reference](https://www.konami.com/arcadegames/products/am_jubeat_1/).
The blue grid graphics and cabinet labels are authored for this mod. The sixteen
raised panels are separate pieces of geometry over the inclined display.
The lower control housing is a rigid 10-by-10-by-10-unit cube, with square
checkered side faces and perpendicular button and service-panel faces.
Its control deck rests at 35 degrees above horizontal, with a separate display
continuing that same slope up to the repositioned utility panel and speaker bar.
The broad rear casing connects the control housing to the base. The bottom display
is a 9.2-unit cube reclining 25 degrees from vertical, and the upper 9-unit cube
tilts forward 12 degrees to face down toward the player. The larger 3.2-unit
square speaker faces tilt upward 10 degrees, with dark housings behind them.

Both display cubes have edge frames, transparent outer panes and
illuminated artwork recessed inside. The upper square circuitry is printed on
the glass, with the logo on the panel behind it. The lower cube has inset front
and side displays beneath clear glazing, with circular front artwork and plain
square logo panels on the sides. Its rear lower corner is embedded in
the plinth so the full front face reaches down close to the floor. The hidden
portion below the plinth is omitted from the rendered mesh. Native composite models render the
opaque structure and translucent glass separately, including the inventory item.

The sixteen raised buttons use the same neutral gray pad design, with no
colored notes or animation. The pads use one 512-by-512 texture with
no animation metadata. This replaces the former 24-frame light sequence and
removes 23 MiB of decoded RGBA frame data; its atlas footprint stays 512-by-512.

## Placement and ordering

Find **Jubeat Arcade Cabinet** in **Japanese Arcades**, use
`/give @s japanesearcades:jubeat`, or order one in the Arcade Ordering Kiosk's
**Machines** tab for **12 iron ingots, 2 gold ingots, 1 diamond, 4 glass blocks
and 4 redstone dust**.

One item places the connected base, console and marquee in a supported,
clear **1-by-1-by-3-block column**. The visible machine stays within one block
of width and depth, including its feet, speakers and topper. Neighboring
machines have independent inventories. Removing any section removes the
complete cabinet.

## Using the cabinet

Hold an Arcade Pass and right-click to spend Credits and receive a simulated
rank and Prize Points, with the same configurable economy and feedback as
the other arcade cabinets. The default cost is **10 Credits**. This does not
start a rhythm minigame.

Insert a music disc through any section, then right-click empty-handed to
eject it. Disc playback and saved progress use the shared cabinet inventory;
using a pass leaves playback and the idle artwork intact.

## Editable model

Source geometry, the embedded-texture Blockbench model, packed Blender scene
and previews are kept beside these notes. The runtime uses native OBJ models
split at the block boundaries, with a complete scaled model for the item.

Regenerate with `python scripts/make_jubeat_model.py`, then render the actual
mesh with `blender --background --python scripts/render_jubeat_model.py`.

![Jubeat mesh preview](../branding/curseforge-gallery-v1/02-cabinet-closeups/17-jubeat-studio-render.png)

The [side view](jubeat-side.png) shows the cabinet angles and separation;
the [controls view](jubeat-controls.png) shows the sixteen individual panels.
