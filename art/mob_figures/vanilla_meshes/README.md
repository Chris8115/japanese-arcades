# Vanilla mob mesh source captures

These 76 source meshes were captured once from Minecraft 1.21.1's actual entity renderers in an isolated development client. The runtime mod does not create or render these entities. The six earlier figures remain preserved; together they cover all 82 vanilla `Mob` entity types, including the dragon, wither, giant, illusioner and zombie horse.

Each JSON stores renderer identity, a fixed adult pose, explicit forward direction, bounds, materials and primitive vertices. Vertex rows are twelve values: **x, y, z, u, v, r, g, b, a, nx, ny, nz**. Positions and normals already include vanilla model transforms; RGBA is 0–255. Y is up. At entity yaw zero ordinary living models face +Z; the special dragon renderer faces −Z. Cow and pig nose bounds confirm the ordinary direction.

Aquatic mobs are captured in water to avoid the stranded-fish sideways pose. The pufferfish is inflated. The dragon uses straight flight history and a fixed wing phase. Signature held weapons are present. Sheep wool, mooshroom mushrooms and the snow golem's carved pumpkin are retained.

Materials retain original render type/state, culling/transparency, emissive flags and recommended overlay exclusions. Raw duplicate eye/emissive geometry is intentionally preserved in these source captures so the static exporter can composite its texture pixels onto the base skin and omit overlapping faces. Tropical fish and villager clothing overlays also require compositing where their geometry coincides. Breeze wind has distinct signature geometry and should be retained. Coplanar overlay handling belongs to the static bake, not runtime entity rendering.

Block-atlas quads for mushrooms, pumpkin faces and equipment have already been resolved to original PNGs and local UVs. The 104 PNGs under `textures/<namespace>/<resource-path>` are byte-identical to the local vanilla resource JAR; see `source-texture-verification.json`. Some vanilla fish faces legitimately use UVs beyond 0–1. The static exporter must tile the relevant source texture and remap those UVs rather than sampling adjacent stitched sprites or clamping them.

`manifest.json` records the complete roster, all 76 successful captures and zero failures. `export-provenance.json` identifies the clean release used to host the isolated authoring session. Temporary exporter source and its disposable world remain in ignored `build/verification/vanilla-mob-export` and `runs/vanilla-mob-export`.
