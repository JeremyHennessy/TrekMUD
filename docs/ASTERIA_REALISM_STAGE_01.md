# Asteria Blender/Cycles realism stage 01

**Status:** source-stage candidate. Not a completed photorealistic bridge, not a published preview, and not user-approved.

This branch adds a repeatable offline Blender source scene **using the unchanged V3-derived V5 GLB**. The authoring stage is separate from the browser app. It does not alter the first-person controls, colliders, material exports, world IDs, PADD, or any campaign state. The purpose is to establish a stable lighting / close-up visual reference before remodelling detailed chair/command assets.

## Required V5 asset

Use the reproducible existing extraction/build in this branch:

```bash
python -m pip install numpy pillow playwright
python scripts/extract_asteria_v3_for_v5.py
python scripts/build_asteria_v5_assets.py
```

The extractor needs Chromium, Playwright, and the original V3 source blob; see `scripts/extract_asteria_v3_for_v5.py`. Both scripts use default paths `_v5_mesh_capture/` and `_site/3d-preview-v5/models/`. Do not fake a missing GLB.

## Build a Blender stage (Blender 4.x or later)

```bash
blender -b -t 8 --python scripts/asteria_blender_stage.py -- \
  --glb _site/3d-preview-v5/models/asteria-v3-restored-pbr.glb \
  --out _blender_asteria --samples 96 --view all
```

Creates:
- `_blender_asteria/asteria-bridge-realism-stage.blend` — the editable Blender master
- `_blender_asteria/asteria-cycles-{aft,command,flight,science}.png` — Cycles reference renders
- `_blender_asteria/stage-manifest.json` — source hash, triangle count, render settings

`--no-render` only builds the Blender master (for quicker modeling). `--resolution 1280 800` is the default. Run on CPU if no compatible GPU is configured. A Blender installation is required. We do not claim a rendered image merely because the script exists.

## Safety and visual acceptance

- Source geometry: 106,988 triangles from frozen V3 blob `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`; script refuses any imported GLB with a different triangle count.
- Original coordinates retained, with glTF Y-up to Blender Z-up conversion explicitly applied to all cameras and lights.
- No edits to existing V1–V5 browser routes or model files.
- Lighting is a Cycles reference rig, **not** a baked GI solution, runtime Three.js scene, or finished production material pass.
- Compare Cycles stills at matched eye-height positions. Inspect chair upholstery, armrest controls, floor clearance, console geometry, wall junctions, light leakage, material texture scale, shadows and screen legibility.
- On acceptance, model *one* physically refined command chair and console as separate Blender objects; preserve source room/collision geometry. Export an isolated test GLB and bake lightmaps into a dedicated UV channel, then compare multi-angle in-browser captures.
- Do **not** replace the V3/V5 baseline until the new close-up asset and browser walkthrough both pass visual review.

## Current limitations

The script intentionally does not claim that the chair is remodelled, that professional texture scans exist, or that lightmaps are baked. It prepares a reproducible editable source and reference-render workflow. Runtime execution, screenshots and visual acceptance are separate verification gates.
