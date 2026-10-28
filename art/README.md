# Artwork source workflow

The runtime assets in `src/main/resources` are sufficient to build and run the mod.
Python and Blender are only needed to regenerate or edit artwork.

Most models have a portable `.bbmodel` file with embedded textures and a geometry
JSON export in their feature directory. The matching scripts under `scripts/`
create the runtime OBJ/JSON resources and render preview images. Individual
feature READMEs describe their commands and required source images.

Blender `.blend` scenes are generated locally and are not tracked. Run a model's
`render_*` script with Blender to create its packed preview scene from the
retained geometry and textures. The [sleeping fox plush](sleeping_fox_plush/README.md)
uses its `make_*` script to create its Blender source before export or rendering.

Do not replace source images with preview renders. Poster originals and cleaned
artwork, captured vanilla mob meshes and textures, and cabinet illustration
sources are inputs to the generators. Runtime model files remain checked in so
normal Java builds never need to run the artwork pipeline.

Selected in-game views and their captions are in the
[curated gallery](branding/curseforge-gallery-v1/index.html).
Disposable test worlds, benchmark output, local previews, and rollback archives
are maintained outside the public source history.

Before publishing regenerated artwork, run `python scripts/check_public_repository.py`
from the repository root to check the tracked files for private metadata and local paths.
