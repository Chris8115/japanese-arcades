# DDR SuperNOVA cabinet and two-player stage

**DDR SuperNOVA Arcade Cabinet** is the tenth entry in **Japanese Arcades**.
The red cabinet, separate two-player metal dance stage, and raised handrails
follow the supplied SuperNOVA references.

The structure has a real **two-column, three-row floor footprint**, with the
cabinet at the back and a **two-by-two-block dance area** in front. Both players
can stand and move on the low platform. The handrails have narrow collision
shapes; the space above the pads remains open.

## Placement and use

```text
/give @s funpackcustom:ddr_supernova
```

Place the item on a solid floor. All six floor positions must have solid upper
faces. The cabinet faces the player and the stage extends two blocks forward.
The second column extends clockwise from the facing: east for a north-facing
cabinet, south for east, west for south, and north for west.

The connected structure occupies **twelve block cells**:

| Section in each column | Forward distance from cabinet | Height above base |
| --- | --- | --- |
| Cabinet base | 0 | 0 |
| Cabinet console | 0 | 1 |
| Cabinet marquee | 0 | 2 |
| Rear stage | 1 | 0 |
| Front stage | 2 | 0 |
| Handrail | 2 | 1 |

Placement checks all twelve cells and six supports before placing any section.
Blocked rails, pads, or cabinet cells prevent placement without consuming the
item. Allow extra lateral clearance for the visible cabinet and platform edges.
The platform is approximately **0.15 block high**, low enough to step onto.

Right-click any cabinet, stage, or rail section with a music disc to insert it
into the single saved jukebox. Right-click again to eject the disc over the open
stage near the cabinet. Both player stations share that inventory. Screens,
arrows, and buttons are decorative; native Minecraft music discs provide the
audio rather than a playable DDR chart.

Breaking any section or removing any of the six floor supports removes the
whole cabinet and platform. Survival returns one cabinet item and the stored
disc once; creative returns the disc without another cabinet item. Neighboring
DDR structures keep their own inventory and playback.

The primary cabinet base provides the one-slot container, playback ticker, and
redstone/comparator output. Saved disc and song progress survive block-entity
reloads. Registered modded songs with a valid jukebox-playable component use the
same native player.

## Model and runtime files

The block/item ID is `funpackcustom:ddr_supernova`. Runtime behavior is in
`src/main/java/local/funpack/custom/DdrCabinetBlock.java`; registration starts in
`FunPackCustom.java`. The block uses `side=primary|secondary` and six named
`section` values matching the table. The inherited `part` property is maintained
for shared jukebox compatibility.

The model contract is twelve `ddr_supernova_<side>_<section>.json` wrappers and
48 combinations of facing, side, and section. Sections route to one inventory
anchor through the shared base-position hook. Matching adjacent sections form
a connected structure, and placement/creative removal assemble or clear the
whole set before neighbor notifications propagate.

The model uses NeoForge's built-in OBJ loader, with no extra renderer mod. The
twelve section meshes partition each assembly at X=16 and Y=16/32; the stage
also splits at Z=-16. The inventory item has its own scaled OBJ. All wrappers use
`minecraft:cutout_mipped_all`; material ambient values distinguish fullbright
screens, marquee artwork, arrow inserts, and lamps from the shaded cabinet.
Texture aliases resolve through the shared MTL and each wrapper's texture map.

The red speaker cabinet is narrower than the stage, and its CRT enclosure leans
back 11.5 degrees. The upper sign has separate speaker/lamp wings. Both dance
stations have a brushed metal grid, four arrow panels, a center panel, exposed
fasteners, red rounded rails, and small front ramps. The cabinet includes
selection/start controls, coin slots and returns, service doors, rear vents,
levelling feet, and the short connection cable to the stage.

The final visible bounds in model units are X **-2.989 to 34.989**, Y **0.06 to
48**, and Z **-32 to 15.48**: about **2.37 blocks wide, 3 high, and 2.97 deep**.
The cabinet's section collision narrows independently of the platform, and the
low cable has its own small shape. Rail collision follows the posts, rounded
shoulders, grip, and mounting flanges, leaving both player areas open.

The final mesh has **6,867 authoring faces**, **7,395 faces across twelve runtime
sections**, and **6,867 item faces**. The section split preserves the same
surface area, vertex positions, and interpolated UVs. The geometry audit found
zero positive-area coplanar overlaps among 15,924 candidates.

Editable sources:

- `geometry.json`: final mesh surfaces, UVs, materials, and export metadata.
- `ddr_supernova.bbmodel`: textured Blockbench free-mesh project.
- `ddr_supernova.blend`: packed Blender preview scene.
- `scripts/make_ddr_model.py`: assembly and asset generation.
- `scripts/ddr_cabinet_geometry.py` and `scripts/ddr_platform_geometry.py`:
  cabinet, stage, and rail construction.
- `scripts/ddr_mesh_export.py`: surface extraction, partitioning, OBJ/MTL,
  item, and Blockbench export.
- `scripts/ddr_textures.py`: hardware labels, arrow panels, and material tiles.
- `scripts/render_ddr_model.py`: front, back, side, platform, screen, and
  marquee previews.

The user supplied the red SuperNOVA cabinet photographs and confirmed this
edition. The generated marquee and demonstration-screen sources are retained as
`header-artwork-source.png` and `display-artwork-source.png`. Exact prompts and
source paths are recorded in `imagegen-prompts.txt`. Hardware textures are
drawn separately by the generator; generated illustration sources remain intact.
The 1354-by-1161 marquee and 1448-by-1086 screen images retain their native
aspect ratios. The earlier wider marquee source is retained separately for
provenance and is not used by the runtime texture.

Previews: [front](ddr_supernova-front.png), [back](ddr_supernova-back.png),
[side](ddr_supernova-side.png), [platform](ddr_supernova-platform.png),
[screen](ddr_supernova-screen.png), and [marquee](ddr_supernova-marquee.png).

## Verification

The final Build passed and **all 47 integration tests passed on
2026-10-06**, including the previous forty. Seven new DDR tests cover:

- Shared disc insertion/ejection through all twelve sections and clear ejection
  in every facing.
- All twelve break positions in all four facings, with exactly one cabinet and
  one stored-disc drop in survival.
- Creative removal at every break position and facing while an adjacent DDR
  structure keeps playing its own disc.
- Saved-disc placement, playback ticks, block-entity reload, and ejection through
  the secondary rail.
- Rejected placement for every occupied secondary/upper/stage/rail cell and
  each missing floor support, without item loss or partial structures.
- Complete removal after any of the six supports is lost, in all facings.
- Actual gravity settling of two player-sized entities onto the stage, player
  step-on access without jumping, unobstructed movement across the dance area,
  and solid handrail collision, in all facings.

Final logs are `build/verification/ddr-supernova-final-build.log` and
`build/verification/ddr-supernova-final-gametest.log`. The geometry audit is
`build/verification/ddr-mesh-audit.json`.

The actual NeoForge 21.1.252 OBJ parser, material parser, and model baker passed
all thirteen meshes and all four rotations of each block section: **36,447
baked quads** checked for face counts, finite coordinates, preserved UVs,
vertical UV orientation, and fullbright lighting. The isolated harness supplies
material binding and a unit sprite; it does not exercise client resource-manager
startup, texture-atlas upload, or live-game rendering. Its report is
`build/verification/ddr-supernova-obj-bake-audit.json`.

The release JAR audit confirms **150 resource files and 35 Java 21 classes**
match the current sources/build exactly, all OBJ/MTL texture references resolve,
and only the primary cabinet base drops the cabinet item. Authoring files and
nested mod JARs are excluded. Details are in
`build/verification/ddr-supernova-package-audit.json`.

The original pack and its saves remain untouched. Live full-pack rendering and
gameplay compatibility are separate from these headless and server checks.
