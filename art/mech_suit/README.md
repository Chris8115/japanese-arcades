# Ivory Mech Suit model

Five-block pilotable reward suit inspired by the supplied white, gold, cyan and
dark armored mech references. The complete animated suit has **7,613 faces**,
including both long curved swords, shield mounts, back engines and armor details.
The separate deployment controller item has **22 faces** after vanilla item
extrusion; opening an inventory does not draw the entity mesh.

`scripts/make_mech_suit.py` is the canonical geometry and icon source. It exports
`assets/japanesearcades/meshes/mech_suit.json`, the material texture, item assets,
and `face-audit.json`. Coordinates use Minecraft blocks, Y up, -Z forward.
The generator checks exported face area and finite vertex data.

The 17 named mesh parts include independently driven upper arms, forearms, swords,
thighs, shins and feet. The wide dark shield backs rest against the outside of the
forearms; white curved armor faces outward. Their mounting cuffs and inherited
forearm transforms retain this alignment while flying and striking.
Both swords are oriented about their grip centers to point forward and down at
rest, with matching cutting-edge orientation and independent attack animations.

`MechSuitRenderer` loads immutable vertex arrays once per resource reload and
shares one material buffer. Walking, flying, and left/right sword poses transform
the cached parts without rebuilding geometry. Cyan details use full-bright light.
The local first-person cockpit omits the enclosing shell and wing shields and
raises the visible arms; other views draw the complete model. Culling includes
the swords and shields beyond the physical collision hull.

Run the generator with the configured Python/Pillow runtime. Run
`blender --background --python scripts/render_mech_suit.py` to refresh the exact
runtime-geometry previews and the editable `mech_suit.blend` scene generated locally by that script. The scene has
named, parented mesh parts with matching articulation pivots. Studio images use
different lighting from Minecraft; native captures verify the game renderer.

The references guide the silhouette and palette; detail is deliberately made
from efficient curved meshes and beveled plates rather than tiny mechanical
subdivisions. Geometry remains below the project's roughly 10,000-face target.
