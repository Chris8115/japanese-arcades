# BeatStream arcade cabinet

BeatStream is a separate copy of the Nostalgia cabinet: the same slim black chassis,
recessed footwell, metal threshold, service doors, feet and three-block placement.
The original Nostalgia model and artwork are unchanged.

The conversion replaces the round upper speakers with inward-facing triangular
grilles edged in cyan light, and lights the large triangular lower speaker to match.
The lower triangle keeps Nostalgia's centered shape, position and backward lean.
The upper speakers are rigid triangular meshes, with continuous outer edges even
at their combined inward and backward angles.
The central Nostalgia plaque, piano keys, gold ornament and book decoration are gone.
A larger inclined touch display reaches down toward a flat white front strip.
BeatStream has its own upper screen, lower touch-screen artwork, patterned trim,
and a thin die-cut illustrated topper based on the supplied photographs.
The white lower-screen surround continues up beside the speaker triangles and
meets the upper screen's black surround. Its shoulder pieces align flush with
the existing white frame, with no gap at the join.
The export contains 290 cuboids and twelve speaker-mesh polygons. Its visual bounds are X 0.20–15.75,
Y 0–47.65 and Z 0–15.355 model units, fitting inside a 1×1×3 block column.

## Obtain and use

- Find **BeatStream Arcade Cabinet** in the **Japanese Arcades** creative tab.
- Or order it from the kiosk for **16 iron ingots, 4 gold ingots, 1 diamond,
  6 glass and 6 redstone**.
- Command: `/give @s funpackcustom:beatstream`.
- Place on a solid floor with three clear vertical cells. It faces the player.
- Use an Arcade Pass to spend Credits and earn Prize Points through the shared
  simulated-play system. The default cost is 10 Credits; the server can override
  its distinct machine ID, `funpackcustom:beatstream`, in the arcade economy config.
- Insert/eject a music disc through any cabinet section. Its base stores one disc
  and playback progress, using the same jukebox behavior as Nostalgia.
- Breaking a section removes the cabinet and returns its disc once. Adjacent
  machines keep their own inventories and playback.

## Editable source and artwork

`beatstream.bbmodel` is the complete grouped Blockbench model with embedded textures.
`beatstream.blend` contains the preview scene with packed textures. `geometry.json`
is the complete exported cabinet geometry; the front/side/back/detail images render
that same geometry and its UVs. Studio lighting is only for the previews.

`topper-source.png` and `screens-source.png` were created with the built-in
imagegen tool using the user's BeatStream photos as references. The exact prompts
are saved in [imagegen-prompts.txt](imagegen-prompts.txt). Source pixels are retained;
the model generator packs the artwork into runtime atlases and maps the two screen
cells independently. The topper's transparent silhouette also guides its thin
physical cutout. Native cabinet materials and trim are generated separately.

The entry points are `scripts/make_beatstream_model.py` and
`scripts/render_beatstream_model.py`. Apply lasting geometry changes to the source
scripts; regenerating replaces the exported assets and editable model.
`scripts/beatstream_speaker_geometry.py` supplies the two rigid triangular speaker
housings. The console and item models combine these meshes with their native cuboids.

```powershell
& 'python' scripts/make_beatstream_model.py
& 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe' -b --python scripts/render_beatstream_model.py
.\dev.cmd Build
.\dev.cmd GameTest
```

The cabinet is decorative with simulated Arcade Pass results; it does not implement
BeatStream rhythm gameplay. Illuminated faces remain bright, while bloom depends
on the active shader. The exported model combines native Minecraft cuboids with
two triangular speaker meshes.

## Verification

All 112 GameTests passed on 2026-10-06, including four BeatStream-specific checks
for all-section disc use, saved playback, all-facing neighboring cabinets, blocked
placement and support loss. The catalog purchase and Arcade Pass tests also include
BeatStream automatically.
The export audit confirms all twelve facing/part variants, eight textures, valid
native model bounds/rotations/UVs, and matching Blockbench geometry and embedded
artwork. All 35 original Nostalgia art, resource and generator files are unchanged.
The 36 lower-triangle cuboids match Nostalgia's positions, dimensions and rotations
exactly. Both upper speaker housings have closed, planar geometry, with matching
OBJ and Blockbench coordinates, UVs and material assignments.

The corrected build also passes native small-client checks for all four facings,
both composite children, render layers and inventory-item pass order. In-game
closeups confirm the centered lower triangle and clean upper speaker edges.
`native-front.png`, `native-triangles-close.png` and `native-kiosk.png` show this
final geometry in Minecraft. The earlier complete kiosk/pass/disc/removal checks
passed in both the small client and the copied 218-mod pack; this visual revision
changes model resources only.

The rigid speaker meshes also passed a resource-only check under the copied pack's
shaders. `native-pack-*.png` captures that version, before the final white shoulder
extensions. The final shoulder build passes the small-client visual check; its
only differences from the pack-tested JAR are the console and item JSON models.
Java classes, speaker meshes and textures are identical. The full-pack check needed
one unchanged retry after an NTGL 3.2.0 startup race; the retry exited successfully.
Current `native-*.png` images without `pack` in the name show the final white trim.
