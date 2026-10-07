# Authoring assets and historical verification

Current generators, editable asset references, commands and runtime paths use the `japanesearcades` namespace and the `local.japanesearcades` Java package.

Existing screenshots and recorded verification/optimization audit JSON describe builds made before this rename. Those records retain their original resource names, logged messages, build hashes and measured results. Historical audit files containing the former namespace carry an explicit `namespace_history_note`; they are evidence for the recorded build, not a claim that the renamed build has been tested.

Source artwork, native screenshots, mesh coordinates, UVs and face-count measurements were preserved during the rename. Current resource references in authoring metadata and Blender image links were updated without regenerating the artwork or geometry.
