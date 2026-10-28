# MÚSECA cabinet

MÚSECA is the sixth cabinet in the **Japanese Arcades** creative tab, with the
same three-part placement and native music-disc playback as the other machines.
The model follows the supplied cabinet photographs, including its five-spinner
deck, reclined monitor, layered marquee, black body, and projecting central pedal.
Its dimensions are interpreted from those references, not manufacturer measurements.

Placement occupies **three vertical blocks**. The current envelope is about
**1.34 blocks wide**, **1.76 blocks deep** including the pedal, and just under
three blocks tall. Allow an open aisle in front and approximately two-block
center spacing between machines. The deck and marquee selection shapes rotate
with the cabinet. At the bottom, the low pedal has its own narrower collision
shape, leaving the space beside it clear.

The spinners, pedal, and screen are decorative. Minecraft music discs provide
the playable audio; the cabinet does not run a MÚSECA rhythm game. The base emits
light level 4 and the two upper sections emit level 13.

## Use in Minecraft

Launch `dev.cmd Client` or `dev.cmd PackClient`, then select **MÚSECA Arcade
Cabinet** from **Japanese Arcades**, or run:

```text
/give @s japanesearcades:museca
```

Place it on a solid floor with three clear vertical blocks and room for the
projecting deck and pedal. Its front faces the player. Breaking any section
removes all three; survival drops one cabinet item from the base.

Right-click any section with a music disc to insert it and start playback.
Right-click again to eject it. A cabinet stores one disc and saves its playback
progress. Registered modded songs with a valid jukebox-playable component use
the same native player. Breaking the cabinet stops the song and returns the
disc once, including in creative mode. Neighboring cabinets keep independent
discs and playback. The base provides jukebox redstone/comparator output and
a one-slot container.

MÚSECA ejects its disc farther forward to clear its projecting body. Its pedal
remains below the initial dropped item's position. Restart the development
client after Java changes; F3+T reloads model and texture changes only.

## Model files and editing

The cabinet combines a recessed portrait display, five staggered luminous spinner
rings with separate hubs, a faceted illuminated front column, an angled card
reader, a metal pedal, and overlapping geometric marquee pieces. The layered
character print and separate thin MÚSECA wordmark follow the supplied photographs.
The upper-left decoration uses three overlapping red paper facets. All five
spinner bodies stay neutral white, and the seven lower prism lights are red,
matching the supplied white-background product reference.

| File | Purpose |
| --- | --- |
| [museca.bbmodel](museca.bbmodel) | Complete editable Blockbench model with embedded textures and named groups |
| `museca.blend` (generated locally) | Packed Blender studio preview scene |
| [geometry.json](geometry.json) | Complete native mesh faces, UVs, retained source cuboids, and optimization statistics |
| [museca-front.png](museca-front.png) | Overall three-quarter preview |
| [display-artwork-source.png](display-artwork-source.png) | Original portrait display illustration |
| [marquee-artwork-source.png](marquee-artwork-source.png) | Original character marquee illustration |

The current export has **7,425 world faces** split across three block models:
**3,571 base**, **2,735 console**, and **1,119 marquee**. Its item has **7,349
faces**. Compared with the saved pre-optimization models (9,987 world / 9,983
item), this removes **25.7%** of world faces and **26.4%** of item faces.

The printed controller deck is two coplanar quads on its original shallow
`y = 18.07 + 0.145 × (z + 7.50)` slope. Six straight bevels, continuous sidewalls,
and a sealed undertray replace the former 24 stair courses. Its complete shell
uses 22 faces. The five spinners use 24 radial segments with the original tier
radii, heights and white lighting; their hubs, inlays, screw heads and rear
function button follow the same slope. Cabinet bounds, monitor, marquee, lower
body, pedal and all five texture files remain unchanged.

The follow-up controller reduction lowers each round body and hub from 448 to
336 faces (32 to 24 radial segments), saving another 560 faces across the five
controllers. All 5,669 other source faces are exactly unchanged, including the
approved flat deck and center inlays. The previous planar-deck revision is
saved as `backup/museca-before-spinner-reduction-20261007-112932` with a matching
external backup archive.

The surface optimizer removes hidden cuboid faces and clips overlapping opaque
surfaces. Static NeoForge OBJ models preserve native lighting and guarded UVs
without a custom renderer. The editable source contains 7,349 faces before
section clipping and conservative coplanar merging.

The two source illustrations were produced with the built-in image-generation
tool. Their original pixels are retained in the source PNGs and padded onto
power-of-two runtime textures without resampling. Exact prompts and provenance
are recorded in [imagegen-prompts.txt](imagegen-prompts.txt). Hardware, material,
and branding atlases are generated by `scripts/museca_textures.py`.

Regenerate with Python and Pillow, then render with Blender:

```powershell
python scripts/make_museca_model.py
blender --background --python scripts/render_museca_model.py
```

The generator uses `scripts/museca_shell_geometry.py`,
`scripts/museca_upper_geometry.py`, and `scripts/museca_mesh_geometry.py` for the model. The renderer reads the exported
geometry and texture atlases, produces `museca-{front,back,side,controls,screen,marquee}.png`,
and saves a packed `museca.blend`. Append `-- --front-only` for a front preview or
`-- --detail-only` for controls, screen, and marquee views. Add `--quick` after
`--` for 12-sample previews. Studio previews use the actual exported mesh faces
and UVs, but their lighting differs from Minecraft.

The generator is the canonical model source. Save manual Blockbench edits
separately or transfer them into the generator before regeneration, which
replaces exported model files.

## Runtime implementation

The block/item ID is `japanesearcades:museca`. Registration begins in
`src/main/java/local/japanesearcades/JapaneseArcades.java`. `MusecaCabinetBlock.java`
defines the section bounds, compound pedal/base collision, and disc-ejection
position. It inherits placement and interaction from `NostalgiaCabinetBlock.java`.
All cabinets share `NostalgiaJukeboxBlockEntity.java` and Minecraft's native
`JukeboxSongPlayer`, retaining the existing saved-data and block-entity IDs.
