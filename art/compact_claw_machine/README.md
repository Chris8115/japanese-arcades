# Compact claw machine

An original single-play adaptation of the white and pastel-pink SEGA UFO CATCHER TRIPLE TWIN family. The cabinet fits a 2 × 2 × 2 block volume and holds **12 prize positions (4 columns × 3 rows)**. The existing 3 × 2 × 3 machine now holds **15 positions (5 × 3)**. Official reference photographs, source URLs and SHA-256 hashes are preserved in `references/sources.json`.

The clear chamber, rounded canopy, joystick, drop button, service panel and open receiving bay are static chunk-baked geometry. The real floor aperture is separate from the front prize row. Runtime code supplies the moving gantry, cable, three-arm claw, target outline, price label and displayed rewards.

Find it in the Japanese Arcades creative tab or order it at the arcade kiosk for **18 iron ingots, 3 gold ingots, 1 diamond, 8 glass and 6 redstone**. Its ID is `japanesearcades:compact_claw_machine`. Right-click to play; shift-right-click with an empty hand for the same owner/PIN-protected operator setup as the larger cabinet. The compact machine requires full support under all four floor cells.

| Geometry | Compact | Existing larger cabinet |
|---|---:|---:|
| All placed static sections | 1,287 | 1,576 |
| Moving gantry/cable/claw | 90 | 90 |
| Cabinet including moving hardware | 1,377 | 1,666 |
| Transient selection outline | 24 | 24 |
| Peak cabinet-only total while aiming | **1,401** | **1,690** |
| Full 3D inventory model | 1,161 | 810 |
| Native captured GUI icon | 1 | 1 |

The totals exclude variable player-stocked prize models and price/count labels. Face counts describe geometry, not measured FPS. All eight compact textures are 16-pixel aligned, no dimension exceeds 512 pixels, and their combined 299,008 pixels require approximately **1.52 MiB** of RGBA storage with four mip levels. The supported lossless compaction pass found no removable padding. Large-cabinet texture hashes remain byte-identical.

The final compact centers are X = 26, 19⅓, 12⅔, 6; Z = 25, 17, 9. Maximum fitted prize envelopes are 4.6 wide × 4.6 high × 3.4 deep, uniformly scaled and bottom-aligned to Y = 11.2. Twelve prizes retain 2.07 model pixels between neighboring maximum-width prizes and approximately 1.07 pixels between neighboring open-claw sweep envelopes. See `capacity_comparison.svg` and `capacity_audit.json` for the nine-versus-twelve comparison. The native stocked-gallery inspection also includes figures, figure boxes, cabinet items and the fox plush.

`make_compact_claw_machine_model.py` generates the shipped OBJ resources and editable `compact_claw_machine.bbmodel`. `render_compact_claw_machine_model.py` renders the **actual shipped item OBJ** and saves the packed `compact_claw_machine.blend`. Hero, front, rear and control close-up PNGs were visually inspected; the item preview includes a separately authored copy of the runtime parked rig. The independent exported-file audit checks all eight section OBJs plus the full item for finite vertices, nondegenerate planar faces, normalized UVs and per-cell bounds.

Rebuild assets with `python scripts/make_compact_claw_machine_model.py`; render with `blender -b -P scripts/render_compact_claw_machine_model.py`. After regenerating an item model, recapture/import its native GUI icon through the repository's inventory-icon workflow.
