# maimai DX twin cabinet

maimai DX is the ninth cabinet in the **Japanese Arcades** creative tab. Its
two stations form one connected **two-column, three-row** Minecraft structure.
The twin enclosure is deliberately wider than the single cabinets, following
the supplied maimai DX references.

The cabinet occupies **six block cells**, with two solid floor supports. Leave
additional room at the sides and in front for the enclosure and player mat.
Its dimensions are interpreted from the photographs rather than manufacturer
measurements.

The body and mat are **2.4 blocks wide**; the upper side badges extend the
overall width to about **2.46 blocks**. The complete visible model is about
**2.95 blocks tall** and **1.78 blocks deep**, including the thin mat. The floor
collision follows that mat at a height of 0.35/16 of a block, allowing players
to approach both stations without a raised platform.

Both stations share **one saved music disc** at the primary base. The screens,
buttons, and other controls are decorative; native Minecraft discs provide the
audio rather than a playable maimai rhythm game. Both lower sections emit light
level 4, and the four upper sections emit level 13.

## Use in Minecraft

Launch `dev.cmd Client` or `dev.cmd PackClient`, then select **maimai DX Twin
Arcade Cabinet** from **Japanese Arcades**, or run:

```text
/give @s japanesearcades:maimai
```

Place the item on a solid floor with two adjacent supported columns and three
clear blocks above each support. The front faces the player. The second column
extends clockwise from the cabinet's facing: east when the front faces north,
south when it faces east, west when it faces south, and north when it faces west.
Placement checks all six cells before adding any parts. An obstructed cell or
missing second support leaves the item unconsumed and no partial cabinet behind.

Right-click **any of the six sections** with a music disc to insert it and start
playback. Right-click any section again to eject the disc in front of the twin
cabinet's center. Each pair saves its disc and playback progress independently
from adjacent cabinets. Registered modded songs with a valid jukebox-playable
component use the same native player.

Breaking any section removes the complete six-cell pair. Survival returns one
cabinet item and its stored disc once. Creative removal returns the disc without
a cabinet item. Removing either floor support also tears down the whole pair.
Redstone/comparator output and the one-slot container belong to the primary base.

Restart the development client after Java changes. F3+T reloads model and texture
changes only.

## Model files and editing

| File | Purpose |
| --- | --- |
| [maimai.bbmodel](maimai.bbmodel) | Complete editable Blockbench model with embedded textures |
| `maimai.blend` (generated locally) | Packed Blender studio preview scene |
| [geometry.json](geometry.json) | Complete exported surface mesh and processing statistics |
| [maimai-front.png](maimai-front.png) | Overall three-quarter studio preview |
| [display-artwork-source.png](display-artwork-source.png) | Original circular-screen maimai DX title artwork |
| [upper-artwork-source.png](upper-artwork-source.png) | Original wide upper information-screen artwork |

The twin white enclosure uses the reference cabinet's coral and yellow palette,
with blue title screens and separate station controls. The shared center column
contains payment and service hardware, and the low black plinth carries a thin,
wide printed rubber mat in front. Rear service doors, vents, carrying grips,
and levelling feet complete the enclosure.

Both screen illustrations were created in **built-in image generation mode**.
The original PNG pixels remain unchanged; runtime packing and circular UV
masking are separate. Exact prompts and provenance are recorded in
[imagegen-prompts.txt](imagegen-prompts.txt). Material, floor, hardware, and
branding prints are produced by `scripts/maimai_textures.py`.

Each circular station has eight raised white buttons around a blue title
screen. The two upper rectangular screens, shaped side badges, coral and yellow
trim, and individual speaker grilles follow the references. Flat graphics and
hardware use texture detail while the button rims and enclosure contours have
separate geometry.

The circular housings lean rearward by **eight degrees**, with a rounded
transition into the upright lower enclosure. `scripts/maimai_profile_geometry.py`
blends the profile between model heights 13 and 19 and preserves the vertical
rear service wall. Shared mesh edges keep the screen, buttons, trim, and their
UVs continuous across the transition. NeoForge's built-in OBJ loader renders
the inclined surfaces directly, without a custom Java renderer or another mod.

The complete model is divided into six runtime section models:
`maimai_primary_{base,console,marquee}` and
`maimai_secondary_{base,console,marquee}`. Each section is positioned within its
own block cell. The blockstate file contains 24 combinations of facing, side,
and vertical part; record presence does not change the model.

Each runtime section has a JSON wrapper pointing to its OBJ mesh. A separate
scaled OBJ supplies the item model. All seven meshes share `models/block/maimai.mtl`
and five texture atlases for materials, hardware, branding, circular displays,
and upper displays. The MTL ambient channels retain full brightness on the lit
surfaces; the cutout render type preserves the DX badge's transparent outline.
Internal surfaces are removed before the continuous profile and section split.
The complete authoring mesh contains **20,112 faces**. Its optimized native
exports contain **17,697 world faces** and **17,089 item faces**, down from
24,182 and 23,826 respectively. The sixteen buttons retain all 64 socket, cap,
lens and lip layers as closed curved prisms using their original arc outlines.
The enclosure and hardware share a half-unit bend grid, so tiny screw and
socket endpoints no longer subdivide every large panel. Maximum displacement
from the previous analytic curve is less than **0.0011 model units**, and the
overall bounds and all five runtime texture files are unchanged. Shared
transition vertices keep adjacent hardware and enclosure surfaces joined.

Regenerate the canonical model with Python and Pillow:

```powershell
python scripts/make_maimai_model.py
blender --background --python scripts/render_maimai_model.py
```

Keep manual Blockbench edits separately or transfer them into the generator
before regeneration replaces the exported model files. Studio renders use the
runtime geometry and UVs with lighting that differs from Minecraft.

## Runtime implementation

The block/item ID is `japanesearcades:maimai`. Registration begins in
`src/main/java/local/japanesearcades/JapaneseArcades.java`. `MaimaiCabinetBlock.java`
adds a `side=primary|secondary` property to the shared facing, part, and record
properties. It resolves all six interactions to the primary base through the
protected base-position hook in `NostalgiaCabinetBlock.java`.

Only the primary base creates a `NostalgiaJukeboxBlockEntity` and receives a
playback ticker. Placement assembles all six cells before notifying neighboring
shapes. Each section requires its vertical neighbors and matching section in the
other column; breaking those connections removes the entire structure. Creative
removal clears the matched pair before propagation so it cannot drop a second
cabinet or affect an adjacent maimai. Loot is restricted to the primary base.

The existing block-entity and saved-data IDs are unchanged. All cabinets use
Minecraft's native `JukeboxSongPlayer`.
