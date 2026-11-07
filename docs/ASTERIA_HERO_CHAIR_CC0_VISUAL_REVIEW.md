# USS Asteria — scanned-fabric upholstery A/B visual review

Date: 2026-11-06. Status: **technical PASS, material appearance improved, full photorealism NOT approved**.

## Source and license

- Poly Haven's `velour_velvet` scanned fabric at 1K resolution.
- Official source: `https://polyhaven.com/a/velour_velvet` and source/license `https://polyhaven.com/license`.
- CC0 1.0, downloaded through Poly Haven's documented public API with identifying User-Agent, checksums checked against live API records.
- `scripts/asteria_fetch_cc0_velour.py` converts source diffuse tonal detail into two muted mauve palette maps while preserving the original roughness and OpenGL normal scans. All five inputs are SHA-256 pinned in `scripts/asteria_hero_chair_blender.py`.

## Exactly what was tested

- Control: hero chair model with its original flat-color/procedural material.
- Candidate: **identical geometry, camera, lights and Cycles exposure (-1.4 EV)** with photo-scanned fabric material.
- Four candidate views (front, rear, quarter, detail) and one matched control quarter view at 900×800 / 24 CPU samples.
- All render checks passed in GitHub Actions run `42329574956`.
- Original scanned source/provenance test independently passed in run `42329401995`.
- GLB geometry preserved exactly: **47 scene geometries and 26,908 triangles**, unchanged bounds.
- Textured GLB embeds normal, roughness and albedo images, has UV texture coordinates, is approximately **9.2 MB**, and contains no live/runtime Poly Haven requests.

## Direct visual inspection

The candidate has richer, less washed-out plum upholstery and visible fabric microtexture at close distances. The face color around the quarter-view centre changed from approximately RGB `[194,178,180]` to `[156,124,131]` with identical exposure.

This is a meaningful material improvement but **not a completed realistic captain's chair**. The lumbar/head cushion shapes read as somewhat flat inset panels. Seat-lip supports and piping remain too architectural, and 24-sample Cycles renders contain visible Monte Carlo noise. The test is an isolated studio scene and cannot establish room placement, walking clearance, lighting balance under the bridge fixtures or user-visible browser accessibility.

## Preservation and release

- This CC0 material experiment is a draft PR #43 based on draft PR #42, itself based on the tested V5/Cycles foundation PR #41.
- No edits to the approved V1–V5 routes, public Pages output, existing game collision/UI or campaign topology.
- No user approval or public preview link is claimed.
- Next highest-value gate is a **separate in-context browser candidate**, with only the original captain chair replaced, verified by actual screenshots and walking; do not overlay both chair models.
- Further photorealism requires tailored cushion curvature, proper construction seams and stronger overall bridge lighting/material work; finishing this chair is only one part of the larger room.
