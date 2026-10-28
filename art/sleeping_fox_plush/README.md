# Sleeping fox plush

An oversized, placeable sleeping fox prize with Minecraft-style cuboid geometry,
vanilla fox colors, tucked paws, and a curled tail. It can be redeemed from the
Arcade Kiosk and displayed as an arcade prize.

## Retained source files

- `model.fox_sleep.png`: source sleeping-fox texture used by the generator.
- `model.texture.png`: the exported model atlas.
- `model.obj`, `model.mtl`, and `model.glb`: portable model exports.
- `manifest.json` and `runtime_audit.json`: dimensions, geometry counts, and export notes.
- `scripts/make_sleeping_fox_plush.py`: the editable procedural model definition.

The Blender source `model.blend` is generated locally and is not tracked.
Normal mod builds use the checked-in runtime assets and do not require Blender.

## Regenerate the model

From the repository root, with Blender on your command path, run these steps in order:

```sh
blender --background --python scripts/make_sleeping_fox_plush.py
blender --background --python scripts/export_sleeping_fox_plush.py
blender --background --python scripts/render_sleeping_fox_plush.py
```

The first command creates `art/sleeping_fox_plush/model.blend`. The second reads
that scene to rebuild the placed sections, item mesh, and atlas in the runtime
resources. The third creates preview renders from the same scene. Keep the
source sleeping-fox PNG available when regenerating; it is included here.

After changing the item's appearance, refresh its native GUI inventory icon
using the [inventory-icon workflow](../inventory-icons/README.md).

[View the fox in Minecraft](../branding/curseforge-gallery-v1/01-recommended-gallery/11-sleeping-fox-plush.png).
