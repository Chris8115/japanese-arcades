# Eight more arcade posters and shared black frames

All twenty posters have the original WACCA outer dimensions, **1 × 4096/2979
blocks**, and a visible black front frame. Existing placed posters update through
their renderer. Each poster costs **750 Prize Points** at the kiosk and is also
available in the Japanese Arcades creative tab.

| Item ID | Print |
| --- | --- |
| `project_diva_arcade_poster` | Project DIVA Arcade |
| `chunithm_luminous_plus_poster` | CHUNITHM Luminous PLUS |
| `sound_voltex_exceed_gear_ensemble_poster` | SOUND VOLTEX EXCEED GEAR Ensemble |
| `maimai_splash_poster` | maimai Splash |
| `sega_cygames_poster` | SEGA Rhythm Games × Cygames |
| `maimai_universe_poster` | maimai UNiVERSE |
| `chunithm_paradise_poster` | CHUNITHM PARADISE |
| `we_love_music_game_poster` | We Love Music Game |

## Photograph cleanup

`sources/` preserves the eight supplied WEBPs byte-for-byte. Project DIVA was
already a clean digital print and uses that source directly. The other seven
photographs were edited with the **built-in image_gen tool** to extract and
straighten the print, remove the surroundings, cups, frame hardware, reflections,
glare and curled supports, and restore obscured details. The resulting PNGs are
saved under `cleaned/`. The original character arrangements, colors and major
logos were retained as closely as possible; obscured fine lettering and small
illustration details may be approximated by restoration.

The exact final prompt set and original/edited hashes are stored per print in
`provenance/`. Each prompt identifies the photograph as the edit target, requests
a flat full-poster extraction, preserves its characters/layout/lettering, and
forbids added frames or surrounding objects. No fallback API or CLI was used.

The common exporter `scripts/make_arcade_posters.py` consumes the saved results.
It uniformly fits each complete image into a 512 × 704 texture, using technical
black padding where required. Source images and cleaned masters are never
overwritten during export. `../manifest.json` records all source and runtime
texture hashes, dimensions, restoration provenance and geometry audits.

## Front frame

The original WACCA print already includes its front border. Other prints are
uniformly inset to 91% inside four black geometric strips, preserving the full
image without cropping or distortion. The strips meet the artwork at its edges;
no second front plane overlaps it. The back and thin outer edges are also black.
The same frame appears on the inventory and held item models.

Framed posters use **10 placed faces** and **14 item faces** each; original WACCA
uses **6 placed / 6 item faces**. All retain the same wall support, selection
bounds, placement, save/reload, and matching-item recovery behavior.

## Verification

`dev.cmd Build` and all **202 required GameTests** pass. Tests cover all nineteen
shared variants and the original WACCA, including all wall facings, saved artwork,
support loss, adjacent placement, recovery, and the 38-entry prize catalog.
All **307 native checks** pass, including exact dimensions, visible black frames,
artwork inset, zero coplanar overlap, all twenty atlas sprites and item models.
Gallery, frame comparison, inventory captures and exact release provenance are
recorded under `native/`.

![WACCA and Nostalgia with visible black frames](native/04-original-wacca-nostalgia-frames.png)
