# WACCA Reverse cabinet

WACCA Reverse is the third cabinet in the **Japanese Arcades** creative tab. Its
proportions, circular touch enclosure, and pedestal follow the supplied reference
photos, using native polygon meshes for its curved surfaces. Dimensions are artistic
estimates rather than manufacturer measurements.

The touch enclosure forms a deep bowl around a recessed circular display. Its
white rim has eight main sections and leans slightly backward, with layered
purple/blue surfaces and pink/cyan illuminated panels leading into the screen.
This depth is modeled with physical geometry, so the bowl remains visible from
oblique and side views. The sloped fascia below it carries the AIME reader,
headphone connection, coin hardware, and printed labels. A black-and-ivory pedestal,
rear service panels, vents, feet, and the raised WACCA Reverse marquee complete
the cabinet.

The bowl and rim now use continuous polygon surfaces instead of stacked rectangular
courses. The white lip has a rounded bevel and eight panel seams; the touch bowl
tapers into a recessed circular screen. All of these surfaces share the original
backward lean. The existing 60-sector LED artwork follows the taper continuously.
The bowl, rim and screen share 104 angular boundaries, so their edges join exactly.
The rear enclosure and curved marquee outline also use polygon surfaces.

The model uses static NeoForge OBJ geometry, solid rendering and mipmapped textures.
It does not add a per-frame cabinet renderer. Palette UVs retain their eight-pixel
guard inside each material tile, and shared mesh boundaries avoid overlapping
surfaces at the rim, cone and screen.

The complete placed cabinet uses **3,103 faces**, down from **7,034** before this
rebuild (about 56% fewer). The inventory model uses **2,918**, down from **7,031**.
These are geometry counts, not an FPS benchmark.

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
/give @s japanesearcades:wacca
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
- `wacca-native-cabinet.png` and `wacca-native-cone.png`: Minecraft views without shaders.
- `wacca-shader-cabinet.png` and `wacca-shader-cone.png`: Minecraft views with Complementary Reimagined.
- `geometry.json`: exported mesh faces and UVs, plus retained casing elements for auditing.
- `display-artwork-source.png` and `marquee-artwork-source.png`: original source artwork made with the built-in imagegen tool.
- `display-artwork-v1.png`: retained first version of the display artwork.
- `imagegen-prompts.txt`: exact artwork prompts and provenance.

The generated artwork draws on the supplied cabinet references and retains the
machine title for identification. The current display character was reworked to
follow the reference face, hair, uniform, and both hands; the exact revision prompt
is saved with the original generation prompts. Source pixels are packed unchanged into
power-of-two runtime sheets; model UVs select the visible regions. Material patterns,
hardware labels, and geometry are generated separately in code. The smooth rebuild
preserves all five runtime texture files and the original source artwork.

## Edit and regenerate

Open `wacca.bbmodel` in Blockbench to edit the complete cabinet. It uses Generic
Model format because the cabinet spans three blocks. The generator exports the
separate native OBJ block models, facing variants, inventory model, textures,
geometry data, and the Blockbench project.

- `scripts/make_wacca_model.py`: main generator, rim, screen, artwork packing, and exports.
- `scripts/wacca_mesh_geometry.py`: continuous bowl, beveled rim, circular screen and mesh export.
- `scripts/wacca_ring_geometry.py`: original continuous LED texture and retained legacy surface helpers.
- `scripts/wacca_shell_geometry.py`: pedestal, sloped fascia, casing, and service details.
- `scripts/wacca_surface_geometry.py`: clips internal and overlapping axis-aligned faces while preserving the visible UV regions.
- `scripts/test_wacca_surface_geometry.py`: regression checks for face clipping, UVs, material lighting, and exterior surface coverage; `--model` also audits the saved cabinet export.
- `scripts/render_wacca_model.py`: renders the exported native faces and UVs in Blender.

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

## Verification and rollback

The smooth rebuild passed `dev.cmd Build` and the surface/model regressions on
2026-10-07. Those checks cover face clipping, all six UV directions, quarter-turn
UV rotations, fullbright data, rotated elements and 30 randomized box unions.
The mesh audit checks the cone's shared boundaries, winding, recessed depth,
palette margins and two-dimensional white-rim UV footprints. An independent audit
also verified unchanged artwork hashes and sampled 6,735 positions across 1,347
original casing/hardware faces: their positions and interpolated UVs are preserved.
The catalog optimizer reports zero pending optimizations.

A disposable native Minecraft client verified all 24 block states and the inventory
model, then exercised kiosk purchase, survival placement, configured paid play,
disc insertion/playback/ejection and independent cabinet removal. All checks passed
again where applicable after a resource reload. Front, side, rear, inventory and
close-up views were inspected. The report is
`runs/wacca-smooth-native-visual-probe/native-report.json`.

A second disposable client using Sodium 0.8.13, Iris 1.8.14-beta.1 and Complementary
Reimagined r5.9.3 passed the same model/texture and resource-reload checks. Its
cabinet and cone screenshots are saved here alongside the native views. Existing
optional-mod and shader-uniform warnings remained, but there were no WACCA model
loading errors. This verifies appearance with that shader configuration; it is
not a full-modpack test or performance benchmark.

The pre-rebuild source and assets are retained at Git tag
`backup/wacca-before-smooth-20261007-100821`. A separately verified ZIP of all 33
original WACCA files and a SHA-256 manifest are stored outside the repository in
the local `source/backups/fun-pack-mods/wacca-before-smooth-20261007-100821` folder.
Rollback should restore only the WACCA changes and remove the added WACCA mesh
files; it should not reset unrelated cabinet work.

The block/item ID is `japanesearcades:wacca`. Assets live under
`src/main/resources/assets/japanesearcades`. `WaccaCabinetBlock.java` supplies the wider
bounds and inherits placement and interactions from `NostalgiaCabinetBlock.java`.
The cabinet uses `NostalgiaJukeboxBlockEntity.java` and Minecraft's native
`JukeboxSongPlayer`; existing registry and saved-data IDs remain unchanged.
No additional mod dependencies are required.
