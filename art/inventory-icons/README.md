# Cabinet inventory rendering

Cabinet inventory icons are 256 × 256 transparent captures of the existing
native Minecraft GUI view. Captures cover a 24-pixel canvas around the native
16-pixel slot, retaining the original scale and slight silhouette overhangs.
Each uses a single textured face. The original OBJ
and JSON models remain the source for placed, held, dropped, framed, and prize
display geometry.

Inventory thumbnails are static. In particular, the IIDX turntable and Jubeat
pad texture animations show the captured phase in GUI slots; they continue
animating on the full placed, held, and prize models.

`CabinetInventoryModels` registers the extra `item/gui/<cabinet>` models and
wraps only the nineteen explicitly listed cabinet item models at model bake.
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

The importer validates all nineteen RGBA images before changing resources,
copies their pixels verbatim, writes one-face GUI models, and records image
hashes in `manifest.json`. Rebuild and compare the normal and enlarged GUI
views. Regenerate affected captures whenever cabinet geometry, textures, or
GUI transforms change. Resource packs changing the cabinet artwork can also
replace `textures/item/gui/<cabinet>.png` and its model.

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
