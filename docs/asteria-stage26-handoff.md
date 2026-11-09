# USS Asteria Stage26 — continuous bridge forward-flank soffit (NO DEPLOY)

## Immutable source checkpoints
- Protected production main: `399de4debfa202e29dbe9887cf11f82cbfbc5b3b` (read-only for this experiment).
- Original V3 authored bridge source blob: `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`, original 106,988 triangles and controls/campaign untouched.
- Frozen Stage12 measured baseline: `e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b`; actual chromium reference from Actions `42524417159`.
- Stage23 technical-pass/art-hold review source `4aff55de9fedafa4ee5b68d2f9146a96a157df17` (PR #79). This experimental branch starts at that exact commit. Stage24 and Stage25 rejected/held lighting investigations are intentionally NOT stacked here. Neither Stage23 nor Stage26 is user-approved for deployment.

## One controlled structural hypothesis
Stage23 makes six repeated soffit roof-underside modules that visually disconnect the wall and ceiling. Preserve all six source-measured wall, upper fascia, plinth, graphite light housing and opal diffuser assemblies, six scene practical lights, scan provenance, glTF exporter, source-face removals, HUD/navigation/camera/collision unchanged. **Replace only six separate molded roof-underside meshes** with **two continuous closed, UV-mapped, physically curved and capped multi-bay cove shells** covering indices 36–45 and 67–76, plus two thin physically modeled black captured junctions. This is a same-scope reversible successor to Stage23, not six extra ornaments, and is intended to improve the normal command view.

Expected: 42 geometry-only zone meshes vs 44 in Stage23; full exported mesh objects 72 vs 74. New continuous form uses an eight-station elliptical profile with real 26-mm thickness, double-sided manufactured end closures, 80 angular segments per arc, CC0 scanned ceiling PBR. Separate 10-mm deep physical captured joints use original procedural graphite. The cove does not change room topology, controls, lighting intensity or any original source exclusion.

## No-release technical and visual gates
- Validate frozen V3 source and Stage12 immutable screenshot SHA; ensure exactly the same 864 original envelope triangles excluded, source geometry base 81,050, unmodified character/game.
- Real Blender Cycles built-environment and all-five-GLB furnished A/B, manifold orientation, 72 meshes, materials, UV1 AO, genuine Poly Haven CC0 scan provenance, gap/overlap and roof/wall fitting.
- Full real SwiftShader Chromium desktop/mobile/focus comparison, main command, ceiling and wall closeups; preserve source navigation and HUD; capture console/page/HTTP and performance. Independently inspect these images vs Stage23 as well as Stage12, reject any bright strip, obstruction or pasted-on visual or worsening.
- **Do not merge PR or publish any Pages optional route** unless visually accepted and independently remotely checked with published unaffected Pages file hashes. Green CI alone is NOT acceptance. In the absence of physical device tests, explicitly mark performance incomplete.

## Speed-focused handoff
Stop wasting runs on tiny emissive adjustments. If this joined architecture does not actually look substantially better in normal desktop command view, do not keep tuning speculative geometry: compare image evidence, classify reason (angle/location/lighting/material or physically incorrect joints), and choose a larger complete forward-wall/ceiling replacement for the next bounded experiment.

## Route handling
All Stage26 visual routes are built in isolated runner `_site` and evidence artifacts. Nothing modifies the existing published GitHub Pages routes, approved HUD, original V3 game, or production branch.
