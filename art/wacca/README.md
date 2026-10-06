# WACCA Reverse cabinet

WACCA Reverse is the third cabinet in the **Japanese Arcades** creative tab. Its
proportions, circular touch enclosure, and pedestal follow the supplied reference
photos, adapted to Minecraft's stepped cuboid geometry. Dimensions are artistic
estimates rather than manufacturer measurements.

The touch enclosure forms a deep bowl around a recessed circular display. Its
white rim has eight main sections and leans slightly backward, with layered
purple/blue surfaces and pink/cyan illuminated panels leading into the screen.
This depth is modeled with physical geometry, so the bowl remains visible from
oblique and side views. The sloped fascia below it carries the AIME reader,
headphone connection, coin hardware, and printed labels. A black-and-ivory pedestal,
rear service panels, vents, feet, and the raised WACCA Reverse marquee complete
the cabinet.

The rim and circular screen use 0.25-unit courses. The bowl uses a 0.5-unit surface
grid with 0.25-unit depth steps, preserving its slight backward lean and recessed
profile. A continuous 60-sector LED texture follows the bowl across merged surface
patches, with wider spacing and lower contrast in its fine light pattern.

The flicker correction removes overlapping faces on the white/gray rim and clips
hidden and overlapping surfaces throughout the axis-aligned casing geometry. These
faces previously competed at the same depth. World and inventory models use solid
rendering so Minecraft can apply mipmaps to their opaque textures. The coarser
surface steps also reduce tiny edges that can shimmer while the camera moves.

Material UVs stay eight pixels inside their 64-pixel palette tiles, which provides
a half-texel margin at mip level 4. The white ring's horizontal ledges use ordinary
two-dimensional material patches. They previously sampled a zero-height row at
the texture atlas boundary, allowing neighboring dark textures to appear as
speckles even after the overlapping geometry had been removed.

The base is approximately **1.1 blocks wide** (17.7 model units); the touch enclosure
reaches **1.375 blocks** (22 units). The highest point is approximately **2.81 blocks**
(44.96 units), while placement occupies one column of **three vertical blocks**.
Allow side clearance around the ring. Placing cabinet centers two blocks apart
gives them clear separation. Selection/collision shapes account for the wider
upper enclosure and rotate with the cabinet.

The display, touch ring, reader, and other controls are decorative. The cabinet
plays Minecraft music discs through the native jukebox system; there is no playable
WACCA game or touch interface. Illuminated faces stay fullbright. The base emits
light level 4, and the console and upper sections emit level 13. Bloom depends on
shaders; vanilla Minecraft does not add that effect.

## Try it in Minecraft

Launch `dev.cmd Client` or `dev.cmd PackClient`, then select **WACCA Reverse Arcade
Cabinet** in the **Japanese Arcades** creative tab. Alternatively:

```text
/give @s funpackcustom:wacca
```

Place it on a solid floor with three clear blocks above the floor and enough room
on either side. The front faces the player. Breaking any section removes the other
sections and drops one cabinet item in survival.

Right-click any section while holding a music disc to insert one and start playback.
Right-click again to eject it. Each cabinet stores one disc in its base and saves
the disc and playback progress. Registered modded songs with a valid jukebox-playable
component use the same system. Removing the cabinet stops its song and returns
the disc once, including creative removal. Neighboring cabinets keep their own
discs and playback. The base also supplies jukebox redstone/comparator output and
a one-slot container.

Restart the development client after Java changes. F3+T reloads model and texture
changes only.

## Files

- `wacca.bbmodel`: editable Blockbench Generic Model with named groups and embedded textures.
- `wacca.blend`: Blender preview scene with packed textures.
- `wacca-front.png`, `wacca-back.png`, and `wacca-side.png`: complete cabinet renders.
- `wacca-controls.png`: close-up of the sloped reader/headphone/coin fascia.
- `wacca-ring.png`: close-up of the deep touch bowl and recessed screen.
- `wacca-marquee.png`: upper rim and raised marquee close-up.
- `geometry.json`: exported cabinet elements, visible faces, and UV data used by the renderer.
- `display-artwork-source.png` and `marquee-artwork-source.png`: original source artwork made with the built-in imagegen tool.
- `display-artwork-v1.png`: retained first version of the display artwork.
- `imagegen-prompts.txt`: exact artwork prompts and provenance.

The generated artwork draws on the supplied cabinet references and retains the
machine title for identification. The current display character was reworked to
follow the reference face, hair, uniform, and both hands; the exact revision prompt
is saved with the original generation prompts. Source pixels are packed unchanged into
power-of-two runtime sheets; model UVs select the visible regions. Material patterns,
hardware labels, and geometry are generated separately in code. The source geometry
contains **1,282 solid cuboids**. After hidden-face removal and overlap clipping,
the export has **6,545 surface elements carrying 7,052 rendered faces**, down from
26,406 faces in the earlier model—a **73.3% reduction**. The optimizer removes
2,698 fully hidden source faces and clips 3,511 overlapping source faces.

Clipping can split one cuboid into several elements that each carry only part of
its exterior. Exported element counts therefore do not equal full cuboid counts
or rendered polygon counts; visible faces are the useful measure of the final
rendering work.

## Edit and regenerate

Open `wacca.bbmodel` in Blockbench to edit the complete cabinet. It uses Generic
Model format because the cabinet spans three blocks. The generator exports the
separate bounded Java block models, facing variants, inventory model, textures,
geometry data, and the Blockbench project.

- `scripts/make_wacca_model.py`: main generator, rim, screen, artwork packing, and exports.
- `scripts/wacca_ring_geometry.py`: touch-bowl surface, continuous LED map, and coplanar patch merging.
- `scripts/wacca_shell_geometry.py`: pedestal, sloped fascia, casing, and service details.
- `scripts/wacca_surface_geometry.py`: clips internal and overlapping axis-aligned faces while preserving the visible UV regions.
- `scripts/test_wacca_surface_geometry.py`: regression checks for face clipping, UVs, material lighting, and exterior surface coverage; `--model` also audits the saved cabinet export.
- `scripts/render_wacca_model.py`: renders the exported cuboids and UVs in Blender.

**Regeneration overwrites the generated Blockbench project and model files.** Save
manual Blockbench edits separately or transfer those changes into the generator
before regenerating. The Blender previews use the same geometry and textures as
the game, with studio lights and a floor that are not included in the Minecraft
model. In-game lighting and shader settings can produce a different appearance.

The generator requires Python with Pillow; the renderer runs inside Blender 5.0.
From the repository root on this machine:

```powershell
& 'python' scripts/make_wacca_model.py
& 'python' scripts/test_wacca_surface_geometry.py --model
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' -b --python scripts/render_wacca_model.py
.\dev.cmd Build
```

## Runtime verification

The surface regression script checks touching and overlapping cuboids, partial
occlusion, all six UV directions and quarter-turn UV rotations, fullbright data,
and unchanged rotated elements. It also compares 30 randomized box unions against
an independent exterior-area calculation. Its optional model audit checks positive
dimensions, unique element names, and absence of same-facing coplanar overlaps
in the saved export. These checks target the geometry defect separately from the
jukebox tests.
The model audit also checks every material UV against its mip-level-4 tile margin
and confirms that all white-ring ledges have a two-dimensional texture footprint.

The runtime implementation built successfully, and all **13 native integration
tests passed on 2026-10-05** using `dev.cmd GameTest` in a disposable world. Three
tests exercise WACCA specifically: placement and disc interaction through every
section followed by single-drop removal; saved-disc placement, ticking, restoration,
and ejection; and creative removal beside an independently playing Valkyrie.
The other ten cover Nostalgia and Valkyrie. These server tests do not verify
rendered appearance or full-pack client compatibility.

The copied full-pack client successfully completed startup with the initial WACCA
model and no WACCA asset errors; the log is
`build/verification/wacca-pack-client.log`. The revised character artwork and earlier
geometry refinement were audited and rendered. The current flicker correction
passes the build, exterior-surface regressions, and asset/UV audit, including the
scaled inventory model's vertex tolerance. It removes all same-facing coplanar
overlaps in the unrotated geometry. The preview renders use the exported geometry;
moving-camera appearance still needs confirmation in Minecraft.

The block/item ID is `funpackcustom:wacca`. Assets live under
`src/main/resources/assets/funpackcustom`. `WaccaCabinetBlock.java` supplies the wider
bounds and inherits placement and interactions from `NostalgiaCabinetBlock.java`.
All three cabinets use `NostalgiaJukeboxBlockEntity.java` and Minecraft's native
`JukeboxSongPlayer`; existing registry and saved-data IDs remain unchanged.
No additional mod dependencies are required.
