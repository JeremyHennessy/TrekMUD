# USS Asteria — command-platform realism Stage 01

**Status as of 2026-11-08: independent Cycles/PBR and first full WebGL A/B passed; candidate, not user visually approved. This branch is not production.**

## Approved references and protected scope

- USS Asteria, NCC-63542, original Nebula-class-inspired 2372 visual set. The frozen original V3 HTML blob is `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`, with **106,988** measured triangles.
- Reference live deployment: `main` (PR #47 and #50) at `https://jeremyhennessy.github.io/TrekMUD/3d-preview-v5-chair/`. Existing UI, camera waypoints, walking/collision logic, MUD campaign, PADD and room ID `AST-D01-BRIDGE` are protected. Previous visual/campaign files are never overwritten to create this candidate.
- The integrated upholstered command chair, previously checked at **31,484** triangles, remains the same original asset. Its own approved source build is unchanged.
- External visual baseline is the actual public Chromium contact sheet from passing run `42451937137`, on the QA-only branch `qa/asteria-live-visual-audit-20261108`.

## Exact frozen-source removal, not bounding-box cropping

The executable original V3 command set was instrumented **in memory only** to recover these actual face ranges:

| Section | Zero-based first face | End-exclusive face | Faces |
|---|---:|---:|---:|
| Command oval platform, raised rim and rails | 12,620 | 14,404 | 1,784 |
| Twin independent command-console pylons | 30,676 | 37,104 | 6,428 |
| Original trim/dais joinery | 93,950 | 94,366 | 416 |
| **Total** | | | **8,628** |

The original chair range of 14,404–30,676 contains 16,272 faces. The ranges are disjoint. Together the optional experimental exporter excludes 24,900 original faces; **82,088 original V3 triangles are retained untouched**. Proven in run `42455829208`; no geometry edits are applied to the source capture.

## What the new Blender asset actually contains

- Original oval footprint and platform top at `x radius 1.85, z radius 1.54, centre z 1.11, y 0.281`.
- A closed layered architectural dais with separate machined trim and approach-tread seams inside its original extent.
- Twin original-position, rotated, tapered eight-corner cast housings at `(x,z)=(-1.27,.58),(1.27,.58)`, with physically modeled removable-service panels, independent gasket/screen surfaces, latching screws and small tactile controls.
- Real metal structural side-rail posts with held bronze handrails and lower cables; no freestanding/disconnected tube ornament intended.
- Reuse of the **actual frozen V3 instrument atlas pixels** (command overview and systems control) for the two display screens.
- Original authored PBR maps (powder coat, cast composite, brushed nickel, bronze, carpet, gaskets) with base/normal/ORM channels, physically scaled shader response. **These are original procedural microstructure maps, not photogrammetry/photo-scanned assets**; photographic realism of them has not been proven.
- A real **Cycles-baked ambient-occlusion map**, on the unique second UV channel of the command dais carpet top; glTF exports `occlusionTexture.texCoord=1` and `TEXCOORD_1`. This adds baked contact occlusion, **not full multi-bounce indirect global illumination**.

The isolated command GLB contains **16,292 triangles**, ~90 Blender mesh objects, at physical bounds x `[-1.85, 1.85]`, y `[.018, 1.195]`, z `[-.43, 2.65]`. It adds to the retained original room and 31,484-face hero chair for **129,864 total triangles** (excluding temporary display helper planes).

## Confirmed tests and actual visual assessment

- Initial Blender/Cycles stage `42456233005`: all 4 real 960×640 stills, textured glTF, 512×512 Cycles AO map, real UV1 export, asset bounds and model counts passed.
- First full in-context WebGL test `42456778068`: 11 real desktop/mobile-sized Chromium screenshot captures, no asset/JS errors, correct extracted source geometry and model counts, two direct A/B same-waypoint image differences, real frame-gated W walking, command waypoint and phone-sized station interaction passed. The command comparison ROI mean absolute RGB difference was about **4.07**.
- I inspected actual full-bridge frames. The new cast side housings have more rounded manufactured edges, the dais trim has physically connected rails, and display surfaces are clearer than the old simplified blocks. But the surrounding wall, ceiling, stair blocks and gallery still retain procedural styling. This is **not a photorealistic complete bridge**.
- The original first console-detail inspection camera looked at the keyboard from the non-operator side, making text orientation hard to judge. The screen UV was adjusted in a separate bounded change; a follow-up comparison places the *review-only* camera on the operator side. This change does not add a game location or alter any user station waypoint.
- The new route reuses the tested mobile heading/minimap spacing under `max-width:760px`. A full retest explicitly asserts no header overlap on phone-sized screenshots.

## Gate for further progression

1. Re-run screenshot/camera/mobile QA after the corrected operator-side closeup; visually inspect the real screenshot, do not rely on green status alone.
2. If passed, publish **only** a separate Pages preview path `/3d-preview-v5-command/` using source-pinned authoring and unchanged other Pages SHA-256 files, not a replacement of the current chair preview.
3. From an independent remote GitHub runner, verify real HTTPS 200 for the index, app, original retained GLB, hero chair GLB and command GLB, and load real WebGL from that public address. Capture actual public screenshots.
4. Preserve visual screenshots and exact stage SHA; do not claim physical iPhone FPS or user artistic approval.

**Rollback:** Delete the independent optional command Pages route or revert the workflow-only deployment addition. The existing V3/V4 and chair-only browser remain available with identical source files.
