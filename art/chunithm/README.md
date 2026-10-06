# Chunithm Paradise Lost cabinet

Chunithm Paradise Lost is the fourth cabinet in the **Japanese Arcades** creative
tab. It shares the existing cabinets' three-part placement and native Minecraft
jukebox playback. The cabinet proportions are adapted from the supplied photos;
model dimensions are artistic estimates rather than manufacturer measurements.

The landscape display leans back at 45 degrees above a flat, illuminated sixteen-zone
touch slider. The deck has a little extra depth toward the screen while its front
edge stays flush with the pedestal. Its solid enclosure joins the white pedestal to the rear cabinet.
Clear acrylic air-sensor wings have dark perimeter rails and cyan technical prints;
their lower front edges continue the lower cabinet's 22.5-degree slope forward,
then return toward the canopy at 45 degrees above the pronounced mid-height elbow.
The two acrylic planes stay parallel; the inward-facing sensor masts stand beside
the screen. A recessed LED matrix,
capsule speakers, central Aime target, deep canopy, and colorful cutout marquee
complete the upper cabinet. The white front fascia meets the slider's front edge
and leans inward toward the floor at 22.5 degrees. The lower housing includes service doors, vents,
locks, the photographed green venue reader, and a projecting metal U-shaped step.

The placement column occupies **three vertical blocks**. The rendered cabinet is
approximately **1.19 blocks wide, 2.96 high, and 1.35 deep**, including the acrylic
projection. Allow room beside the
broader upper cabinet and in front of its projecting base. Two-block center spacing
gives neighboring cabinets clear separation. Selection/collision shapes rotate
with the cabinet. The upper selection bounds extend forward to cover the projecting
acrylic elbows, including when the cabinet faces east, south, or west.

The screen, slider, and other controls are decorative. This cabinet plays music
discs rather than running a playable Chunithm rhythm game. The base emits light
level 4 and both upper sections emit level 13.
Lit screen, slider, matrix, and accent faces remain fullbright. Bloom depends on
shaders; vanilla Minecraft does not add a bloom effect.

## Try it in Minecraft

Launch `dev.cmd Client` or `dev.cmd PackClient`, then choose **Chunithm Paradise Lost
Arcade Cabinet** in the **Japanese Arcades** creative tab. Alternatively:

```text
/give @s funpackcustom:chunithm
```

Place it on a solid floor with three clear vertical blocks and space beside the
cabinet. Its front faces the player. Breaking any section removes the entire
cabinet; survival drops one cabinet item from the base.

Right-click any section while holding a music disc to insert one and start
playback. Right-click again to eject it. Each cabinet stores one disc and saves
the disc and playback progress. Registered modded songs with a valid
jukebox-playable component use the same native playback system. Breaking the
cabinet stops its song and returns the disc once, including creative removal.
Other cabinets keep their own independent discs and playback. The base provides
jukebox redstone/comparator output and a one-slot container.

Restart the development client after Java changes. F3+T reloads model and texture
changes only.

## Files and artwork

- [chunithm.bbmodel](chunithm.bbmodel): editable Blockbench Generic Model with named groups and embedded textures.
- [chunithm.blend](chunithm.blend): editable Blender preview scene with packed textures.
- [Front](chunithm-front.png), [back](chunithm-back.png), and [side](chunithm-side.png): complete cabinet renders.
- [Controls](chunithm-controls.png): sloped display, air sensors, slider, and lower housing close-up.
- [LED tower](chunithm-tower.png): clear sensor wings, matrix, and speaker band close-up.
- [Marquee](chunithm-marquee.png): canopy and colorful title cutout close-up.
- [geometry.json](geometry.json): complete exported elements, faces, UVs, and optimization statistics used by the renderer.
- [display-artwork-source.png](display-artwork-source.png): original 1672 × 941 RGB display artwork made with the built-in imagegen tool.
- [marquee-artwork-source.png](marquee-artwork-source.png): original 2172 × 724 RGBA marquee artwork made with the built-in imagegen tool.
- [imagegen-prompts.txt](imagegen-prompts.txt): exact artwork generation prompts and provenance.

The generated artwork is inspired by the supplied reference photos and retains
the machine names for identification. Source pixels are packed unchanged into
power-of-two runtime textures, with UVs selecting the intended image regions.
Materials, printed labels, LED patterns, and the clear-background acrylic artwork
are generated in code. The models use `minecraft:cutout_mipped_all` and inset UV
regions to preserve the transparent details while limiting texture-edge bleed.

The exterior-surface optimizer removes hidden and overlapping opaque faces;
marquee and acrylic-wing elements with transparent artwork are preserved separately.
Clipping can split one source cuboid into several surface elements, so an exported
element is not necessarily a complete six-faced cuboid. The current export has
**2,883 surface elements and 4,154 faces**; full statistics are in `geometry.json`.
Rotated fascia corners and toe caps have distinct surface planes to prevent
coplanar seams against their surrounding axis-aligned supports.

## Development and editing

Java registration starts in `src/main/java/local/funpack/custom/FunPackCustom.java`.
The block/item ID is `funpackcustom:chunithm`. `ChunithmCabinetBlock.java` supplies
the cabinet's wider bounds and inherits placement and interactions from
`NostalgiaCabinetBlock.java`. All four cabinets use the saved disc inventory in
`NostalgiaJukeboxBlockEntity.java` and Minecraft's native `JukeboxSongPlayer`.
Existing cabinet registry and saved-data IDs remain unchanged.

Generated model resources belong under `src/main/resources/assets/funpackcustom`.
Open `chunithm.bbmodel` in Blockbench to edit the complete grouped cabinet. It uses
Generic Model format because the cabinet spans three blocks; the generator exports
the separate bounded Java models, facing variants, inventory model, textures,
geometry data, and Blockbench project.

- `scripts/make_chunithm_model.py`: main generator, texture mapping, surface optimization, and exports.
- `scripts/chunithm_upper_geometry.py`: display, slider, clear air-sensor wings, LED tower, speakers, canopy, and marquee.
- `scripts/chunithm_shell_geometry.py`: pedestal, display support, service hardware, and metal footstep.
- `scripts/chunithm_textures.py`: native material, label, light, and acrylic artwork.
- `scripts/render_chunithm_model.py`: renders the exported geometry and UVs in Blender.

The generator reuses the exterior-surface clipping utility in
`scripts/wacca_surface_geometry.py`; this does not regenerate or modify WACCA assets.
**Regeneration overwrites the generated Blockbench project and model files.** Keep
manual Blockbench changes separately or transfer them into the generator first.

The builder requires Python with Pillow. The renderer runs inside Blender 5.0.
From the repository root on this machine:

```powershell
& 'python' scripts/make_chunithm_model.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' -b --python scripts/render_chunithm_model.py
.\dev.cmd Build
```

The renderer uses the actual exported cuboids and UVs with studio lighting. Its
floor and lights are preview-only; Minecraft lighting and shaders can differ.
`-- --front-only` renders just the front view, and `-- --detail-only` renders the
three close-ups. Both options still save the packed Blender scene.

## Runtime verification

The runtime implementation built successfully, and all **17 native integration
tests passed on 2026-10-06** using `dev.cmd GameTest` in a disposable world. The four
Chunithm tests execute the shared scenarios against its actual registered block
and item: placement and disc interaction through every section followed by
single-drop removal; saved-disc placement, ticking, restoration, and ejection;
creative removal beside an independently playing WACCA; and selection rays hitting
the acrylic overhang in both upper sections across all four horizontal facings.
The other thirteen tests cover Nostalgia, Valkyrie, and WACCA.

The final six views were rendered from the exported geometry, and the packaged
jar was checked for all model/texture resources. Native bounds, UVs, section and
inventory transforms, and unchanged source artwork pixels were verified. A running
Minecraft 1.21.1 development client loaded the assets without model/texture errors;
the completed cabinet was also visually inspected in the development world.
Full-pack compatibility was not re-tested in this pass. Logs for the runtime pass are
`build/verification/chunithm-wing-build.log` and `build/verification/chunithm-wing-gametest.log`.
No additional mod dependencies are required.
