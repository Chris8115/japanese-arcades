# Jubeat arcade cabinet

A compact single cabinet based on the original black-and-blue Jubeat design:
an illuminated cube topper, silver speaker pods, an inclined 4-by-4 panel grid,
coin/card controls and a blue lower sign on a narrow pedestal.

The model follows [KONAMI's original Jubeat cabinet reference](https://www.konami.com/arcadegames/products/am_jubeat_1/).
The blue grid graphics and cabinet labels are authored for this mod. The sixteen
raised panels are separate pieces of geometry over the inclined display.
The lower control housing is a rigid 10-by-10-by-10-unit cube, with square
checkered side faces and perpendicular button and service-panel faces.
Its control deck rests at 35 degrees above horizontal, with a separate sloped
display connecting it to the speaker bar below the topper. The bottom blue sign
reclines 35 degrees from vertical, and the upper cube tilts forward 12 degrees
to face down toward the player.

## Placement and ordering

Find **Jubeat Arcade Cabinet** in **Japanese Arcades**, use
`/give @s funpackcustom:jubeat`, or order one in the Arcade Ordering Kiosk's
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

![Jubeat mesh preview](jubeat.png)

The [side view](jubeat-side.png) shows the cabinet angles and separation;
the [controls view](jubeat-controls.png) shows the sixteen individual panels.

## Verification

The final reference-based model passes the Java 21 build and all **108
dedicated-server GameTests**, including Jubeat placement, saved playback,
adjacent cabinets, collision and selection, support loss, kiosk ordering and
Arcade Pass rewards. The display neck and tilted cubes have matching
selection and collision shapes. Geometric checks also cover the lower cube's
width and the open space under its sloping front.

The native NeoForge OBJ loader baked **8,000 quads** across every block rotation
and the item, with verified texture coordinates and emissive materials. All
packaged Jubeat resources match the source assets. The visible model stays
within X **0.55–15.45**, Y **0–41.3373**, Z **0.55–15.7873** model units
(16 units per block); all sixteen raised pads remain square.

The small native client completed real kiosk ordering, survival placement,
configured credit deduction and point awards, disc insertion/playback/ejection,
and removal with adjacent cabinets intact. The item and all model textures
rendered correctly, and the client exited with code 0.

The same release also completed those interactions in a copied modpack with all
218 third-party mods enabled and exited with code 0. Both clients spent 10 Credits
and awarded 20 Prize Points on the selected pass during verification. No Jubeat
model or texture errors were reported. The original instance and saves were not
modified.

- [Native cabinet view](jubeat-in-game.png)
- [Native side profile](jubeat-side-in-game.png)
- [Adjacent row](jubeat-row-in-game.png)
- [Kiosk ordering and item model](jubeat-ordering.png)
