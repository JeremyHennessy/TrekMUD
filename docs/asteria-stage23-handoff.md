# USS Asteria Stage23 — forward-command flank coverage experiment (NO DEPLOY)

## Immutable sources / approvals
- Production `main` at experiment creation: `399de4debfa202e29dbe9887cf11f82cbfbc5b3b`; its files are not changed by this branch.
- Frozen V3 authored browser source blob: `74a154ae62bccb0c16d03c2ecf791a64ab19ce81` / 106,988 triangles; original camera, campaign, controls and collision remain unchanged.
- Frozen Stage12 read-only screenshot/geometry baseline: `e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b`, Actions run `42524417159`, artifact `13634679552`, SHA256 checks in workflow.
- Experiment parent: passing Stage20 `f4d4af6700be1dff551ca560a441de230120e5f0`, Actions run `42554569423` (ART NO-GO, never approved or published). Stage22 separate hatch experiment PR #78 commit `1f021c74bda1d57bf5f7614f57df8411712dcadb` engineering-pass/visual-hold, not stacked here.

## Single hypothesis / reversible controlled change
The three Stage20 connected wall/soffit/plinth bays at original 112-sector wall indices 75–82 are largely off-camera in the normal command shot (Stage20 command-pixel mean RGB difference only ~0.187). Keep **exact Stage20 engineered form geometry, PBR provenance, scale, bevels, Cycles AO handling and visual UI**. Only change the zone *coverage* to six bays forming two forward-facing symmetric flank arcs: indices 36–45 and 67–76; each has three continuous wall-to-ceiling joinery bays, a modeled lower plinth and physical practical housing. Do not cover the viewscreen centre, change source hatch calls, or edit game geometry. Four end columns bridge the two new assemblies back to the existing envelope. These are reversible overlays in one optional GLB and an isolated browser route assembled exclusively during CI.

## Gates / decision
1. Assert all source, model/GLB mesh (74), AO UV1/materials, scan provenance, and protected-control hashes. Expected overlay 44 mesh objects (6×6 plus 4×2 columns); original V3 excluded source faces must remain 864, no other exclusions.
2. Confirm genuine furnished Cycles A/B under unchanged lighting, geometry and camera; actual Chromium software-WebGL 1280×800 and 390×844 A/B; pageerror/HTTP logs, walking/waypoint controls; command viewpoint must change >2% of pixels over RGB threshold 10 (visibility floor, **not** artistic pass).
3. Human/independent actual-image visual review: reject if wall modules appear pasted on, occlude consoles, create bright roof strips, harm legibility, produce impossible shadows, fail physical-device performance, or yield negligible improvement. Never call 'photorealistic' from a green CI badge. Do NOT merge this or Stage20/22 or deploy or advertise a published preview before independent remote screenshot QA, exact unaffected Pages file hashes and owner approval.
4. If tests fail, preserve artifacts and evidence, diagnose one failure, no speculative production edits. Next experiment only after review.

## Review route
`_site/3d-preview-v5-command-envelope/` is assembled *within Actions artifact/runtime* only, not published GitHub Pages. Historical production routes remain at their prior SHA; no public URL asserted.
