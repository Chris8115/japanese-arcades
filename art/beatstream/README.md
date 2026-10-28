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
The white lower-screen surround forms a broad bridge beneath the speaker triangles.
Its upper edge meets the black upper surround at the triangles' inward points;
the outer trim is white below that seam and black above it.
The export contains 290 cuboids and 24 speaker/separator mesh polygons. Its visual bounds are X 0.20–15.75,
Y 0–47.65 and Z 0–15.355 model units, fitting inside a 1×1×3 block column.

## Obtain and use

- Find **BeatStream Arcade Cabinet** in the **Japanese Arcades** creative tab.
- Or order it from the kiosk for **16 iron ingots, 4 gold ingots, 1 diamond,
  6 glass and 6 redstone**.
- Command: `/give @s japanesearcades:beatstream`.
- Place on a solid floor with three clear vertical cells. It faces the player.
- Use an Arcade Pass to spend Credits and earn Prize Points through the shared
  simulated-play system. The default cost is 10 Credits; the server can override
  its distinct machine ID, `japanesearcades:beatstream`, in the arcade economy config.
- Insert/eject a music disc through any cabinet section. Its base stores one disc
  and playback progress, using the same jukebox behavior as Nostalgia.
- Breaking a section removes the cabinet and returns its disc once. Adjacent
  machines keep their own inventories and playback.

## Editable source and artwork

`beatstream.bbmodel` is the complete grouped Blockbench model with embedded textures.
The locally generated `beatstream.blend` contains the preview scene with packed textures. `geometry.json`
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
housings and the flat white/black connecting panels. The console and item models
combine these meshes with their native cuboids.

```powershell
& 'python' scripts/make_beatstream_model.py
blender -b --python scripts/render_beatstream_model.py
.\dev.cmd Build
.\dev.cmd GameTest
```

The cabinet is decorative with simulated Arcade Pass results; it does not implement
BeatStream rhythm gameplay. Illuminated faces remain bright, while bloom depends
on the active shader. The exported model combines native Minecraft cuboids with
the triangular speakers and connecting-panel meshes.
