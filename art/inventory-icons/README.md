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

Import a complete set with:

```powershell
python scripts/import_inventory_icons.py <native-capture-directory>
```

The importer validates the selected RGBA images before changing resources,
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
