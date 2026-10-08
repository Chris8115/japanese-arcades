# Static item inventory rendering

Inventory icons are 256 × 256 transparent captures of the existing
native Minecraft GUI view. Captures cover a 24-pixel canvas around the native
16-pixel slot, retaining the original scale and slight silhouette overhangs.
Each uses a single textured face. The original OBJ
and JSON models remain the source for placed, held, dropped, framed, and prize
display geometry.

Inventory thumbnails are static. The IIDX turntable animation shows its captured
phase in GUI slots and continues animating on full placed, held, and prize models.
Jubeat now uses static gray pads in every context.

`CabinetInventoryModels` registers the extra `item/gui/<item>` models and
wraps only the explicitly listed static item models at model bake: nineteen
cabinets plus the arcade kiosk, gachapon machine, Miku figure, and Teto figure.
The wrapper chooses the capture for GUI rendering and delegates every other
display context to the original model. Missing, tinted, custom-rendered, and
override-driven models retain native rendering. Enchanted stacks also retain
the full model so the glint follows the real surfaces.

Claw, gachapon, and custom display boxes intentionally use the GUI *angle* for
their three-dimensional contents. They explicitly unwrap the original model,
including their bounds/color analysis and cached meshes. This prevents GUI
optimization from flattening prizes.

## Why this helps

Minecraft 1.21.1's `GuiGraphics.renderItem` sends the item through
`ItemRenderer.renderModelLists` and flushes the item buffers for every icon.
`renderQuadList` emits every quad again each frame. A small on-screen icon
therefore still incurs the CPU vertex work of the complete model. Static
placed cabinets instead use reusable section vertex buffers, uploaded when
their chunk mesh is rebuilt.

## Regenerating captures

Capture with Minecraft's native item renderer using the original detailed
model, normal GUI angle, full light, transparent framebuffer, and exact GUI
slot framing. Capture outside benchmark samples. The reusable native capture
helper is `scripts/inventory_icons/InventoryIconBake.java`. Compile it into a
disposable client probe (package `probe`), then call
`InventoryIconBake.capture(new ItemStack(item), outputPath)` on the render
thread after model loading. It unwraps the optimized model before capturing,
and fails if the image is empty, opaque throughout, or clips the canvas.

The development probe used for this change lives in the ignored
`build/verification/inventory-performance-probe`; its fixture and results live
in `runs/inventory-performance-world-baseline-visual-probe`. The helper has no
runtime registration and is never packaged into the production mod.

Import a complete set with:

```powershell
python scripts/import_inventory_icons.py <native-capture-directory>
```

The importer validates all twenty-three RGBA images before changing resources,
copies their pixels verbatim, writes one-face GUI models, and records image
hashes in `manifest.json`. Rebuild and compare the normal and enlarged GUI
views. Regenerate affected captures whenever item geometry, textures, or
GUI transforms change. Resource packs changing the item artwork can also
replace `textures/item/gui/<item>.png` and its model.

To refresh a subset without touching other captures or their manifest entries:

```powershell
python scripts/import_inventory_icons.py <native-capture-directory> --ids arcade_kiosk gachapon hatsune_miku_figure kasane_teto_figure
```

The four additional static items use exactly the same one-face GUI path. Their
detailed native models remain available for held, dropped, fixed/frame, claw,
custom-box and shelf displays. The new snapshots also benefit gachapon's flat
printed prize pictures. Their native GUI transforms are captured without auto-fit
or a changed camera angle; small sampling differences are checked in native
normal-size and enlarged views.

## Taiko selection outline

`CachedCabinetShape` caches Taiko's existing voxel shape edges and bounding
boxes. It retains every original grid coordinate and occupied cell. Vanilla
outline rendering and raycasting receive the same geometry without repeatedly
scanning the detailed sliced drum voxel grid. Collision, ray targeting, drum
head/rim behavior, and visible geometry remain intact. `toAabbs` still returns
a fresh mutable list, preventing callers from altering the retained boxes.

The cache is limited by Taiko's forty immutable shapes. It is shared across
all placed Taiko machines and does not retain worlds or block entities.

## Verification, 2026-10-07

`performance.json` records native before/after measurements in a disposable
flat world, with repeated vanilla controls and no FPS cap:

| Nineteen icons | First sample mean | Repeated sample mean |
| --- | ---: | ---: |
| Detailed cabinet meshes | 14.898 ms | 13.654 ms |
| Captured cabinet icons | 0.133 ms | 0.125 ms |
| Vanilla control before | 0.175 ms | 0.168 ms |
| Vanilla control after | 0.180 ms | 0.179 ms |

These are item drawing times on one machine, not promised FPS in a modpack.
`inventory-before.png` and `inventory-after.png` show the enlarged native GUI
comparison: framing and viewing angles match, with expected sampling changes
in fine texture detail. `context-verification.json` checks all nineteen GUI
models, every non-GUI model/transform identity, and enchanted-stack fallback.

The exact Taiko comparison in `taiko-shape-verification.json` checks all forty
shapes, 4,800 rays, 28,800 collision queries, and identical emitted outline
vertices. In the direct native comparison, scanning and emitting one north
drum outline took 9.4–11.2 ms before caching and 0.038–0.043 ms afterward.
The source and cached shapes have identical boxes, cells, and edges.

`taiko-target-performance.json` also measures the original and cached drum
shapes in the same actual client scene with the crosshair on the drum and the
black outline visible. Mean frame-render time was 10.303 ms before and
0.265 ms after; repeated samples were 10.258 ms and 0.264 ms. The screenshot
`taiko-cached-outline.png` shows the retained detailed outline. These frame
timings use a small isolated fixture, not a representative populated world.

The release build and all 190 server GameTests passed, including Taiko's
head/rim interactions, obstruction checks, and cabinet lifecycle tests.
The same GUI/context checks and visual comparison also passed with Sodium
0.8.13, Iris 1.8.14-beta.1, and Complementary Reimagined 5.9.3 selected; see
`shader-verification.json`. The targeted development fixtures do not modify
the original modpack or its saves.

## Static item expansion, 2026-10-08

The arcade kiosk, gachapon machine, Miku figure, and Teto figure retain their
existing meshes (4,816, 3,676, 4,230, and 4,765 quads respectively). Their four
ordinary GUI slots now submit four faces instead of 17,487. Native captures
add 33,687 bytes of PNG data; all nineteen existing captures are unchanged.

`static-expansion/baseline-performance.json` and `candidate-performance.json`
record the same four 16-pixel `GuiGraphics.renderItem` slots in an isolated
flat world, with three-second warmups, five-second measurement windows, and
repeated vanilla controls. These are elapsed item-grid drawing times on one
machine, not GPU-only measurements or a full-modpack FPS promise.

| Four static icons | Median draw time | Repeated median |
| --- | ---: | ---: |
| Original meshes | 2.0798 ms | 2.0924 ms |
| Native snapshot icons | 0.0253 ms | 0.0254 ms |
| Vanilla control before | 0.0287 ms | 0.0290 ms |
| Vanilla control after | 0.0284 ms | 0.0291 ms |

The baseline used release `07c7461fb96cb9829e5f9e3fe1ed4978756b9ccc53447ea9559347f656dec815`;
the timed candidate used `b368eb8b296e0b649f2c8a916e6705795c29bcdcbcc583d59001c7c9329ca9b1`.
These timings cover the four static icons independently of the custom-box buffer bridge.
The native candidate passed all nine display contexts for each item, original
model/pose identity in non-GUI contexts, enchanted-stack fallback, and resource
reload. `before-normal-size.png` and `after-normal-size.png` preserve the actual
16-pixel-slot comparison; fine sampling and a small color-quantization shift
are visible under magnification.

The enlarged diagnostic uses uniform X/Y/Z scaling. Scaling only X/Y changes
the original model's lighting normals and creates a misleading brightness
difference when comparing a detailed model with its flat snapshot.

Final visual/context validation used release
`cd3ae3fe0cfd94ad9ed66a6a5d50302df8429ef591cada0c79febd8ffd107317`.
Both vanilla and Sodium 0.8.13 / Iris 1.8.14-beta.1 with Complementary
Reimagined 5.9.3 enabled passed before/after-reload model-context and foil
checks. `static-expansion/verification.json` records the exact build hashes
and evidence. `comparison-vanilla.png` and `comparison-iris.png` show original
full models above the snapshot icons in the same frame, with matching angle,
framing, and silhouettes. All screenshots are native captures; no image pixels
were edited. The isolated clients exited normally and did not use the original
modpack's worlds.
