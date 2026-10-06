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
/give @s funpackcustom:maimai
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
| [maimai.blend](maimai.blend) | Packed Blender studio preview scene |
| [geometry.json](geometry.json) | Complete exported geometry and surface-pass statistics |
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

The complete model is divided into six runtime section models:
`maimai_primary_{base,console,marquee}` and
`maimai_secondary_{base,console,marquee}`. Each section is positioned within its
own block cell. The blockstate file contains 24 combinations of facing, side,
and vertical part; record presence does not change the model.

The authoring model contains **20,615 surface elements and 21,131 faces**.
Splitting surfaces at the seam between columns yields **20,785 runtime elements
and 21,313 faces** across the six sections. Five shared texture atlases cover materials, hardware,
branding, circular displays, and the upper displays. Internal surfaces are
removed before the section split, with no positive-area coplanar overlaps found
in the geometry audit. Native element bounds, UVs, volume, and rotation angles
pass the export audit.

Regenerate the canonical model with Python and Pillow:

```powershell
python scripts/make_maimai_model.py
blender --background --python scripts/render_maimai_model.py
```

Keep manual Blockbench edits separately or transfer them into the generator
before regeneration replaces the exported model files. Studio renders use the
runtime geometry and UVs with lighting that differs from Minecraft.

## Runtime implementation

The block/item ID is `funpackcustom:maimai`. Registration begins in
`src/main/java/local/funpack/custom/FunPackCustom.java`. `MaimaiCabinetBlock.java`
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

## Verification

Six maimai integration tests exercise actual six-cell placement and interaction:

- Every section inserts into the same inventory and ejects through the opposite
  column in all four facings, with the full dropped-item box clear of all six
  collision shapes and world collision.
- All six possible break points in all four facings remove both columns and
  drop one cabinet item and one disc in survival.
- The same break-point/facing combinations in creative return the disc once,
  produce no cabinet item, and leave an adjacent maimai pair playing.
- Saved-disc placement and a block-entity reload retain the disc and playback
  progress; the disc can then eject through the secondary marquee.
- Obstruction in either upper primary cell or any secondary cell blocks the
  entire placement; a missing second support also leaves no fragments or item loss.
- Removing either support in every facing removes the pair and drops its item
  and disc once.

The final build succeeded and **all 40 native integration tests passed on
2026-10-06**, including the existing thirty-four, after the final collision bounds
were applied. Logs are `build/verification/maimai-final-build.log` and
`build/verification/maimai-final-gametest.log`.

The final jar audit confirms that all **109 runtime resources** and **30 compiled
Java 21 classes** match their source/build files. maimai's 24 blockstate variants,
six section models, five texture atlases, language entry, pickaxe tag, and
primary-base-only loot are present. No authoring files or nested jars are included.
The report is `build/verification/maimai-package-audit.json`; geometry results are
in `build/verification/maimai-geometry-audit.json`.

The rendered preview was checked against the supplied references. In-game visual
inspection and full-pack compatibility are separate checks and were not run for
this addition. The original playable instance and its saves remain untouched.
