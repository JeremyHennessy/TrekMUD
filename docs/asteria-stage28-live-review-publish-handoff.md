# USS Asteria Stage28 optional live review - handoff, Nov 9 2026

The owner explicitly requested publishing the latest work to a LIVE EXAMPLE. This publication creates ONLY a separate optional URL /3d-preview-v5-stage28-review/ and is not user art approval or a claim of photorealism. No gameplay, controls, collisions, current Pages route, original V3, or experimental modeling PR may be merged or replaced.

## Immutable provenance
- Last approved main source: 399de4debfa202e29dbe9887cf11f82cbfbc5b3b.
- Last independently verified public Pages: Actions run 42509385166, artifact 13628039000. SHA256 of ALL 51 original public files is pinned in docs/asteria-pages-published-sha256-20261108.json.
- Source-exact Stage28 architectural experiment SHA: ef7078dca29ddf5a89b83aac10bee1afbfa7672c. Full source/Cycles/Chromium test Actions 42664936329 succeeded; archived evidence artifact 13697640776.
- Frozen authored V3 source blob: 74a154ae62bccb0c16d03c2ecf791a64ab19ce81.
- Stage28 45 additional roof objects, 119 full envelope GLB meshes, 27,368 envelope triangles; 81,050 retained original source faces. Photo PBR is Poly Haven painted_plaster_wall CC0.
- Art remains experimental: ~10% of desktop command pixels and ~8% of mobile pixels changed against Stage23; no verified roof-specific new UV1 contact AO, no physical iPhone GPU QA, not photorealistic.

## Non-negotiable release gates
1. Compare every one of the 51 previously published files with the archived SHA256 manifest before and after adding the new optional path.
2. Historical player-data exports vary only by generatedAt. Restore their last approved generation value only if the SHA256 of the entire result matches exactly; never rewrite gameplay data.
3. Two existing command-model GLBs export nondeterministically. Restore ONLY these two original assets from the last verified GitHub Pages artifact, verify both SHA256s, and do not mask any unrelated divergence.
4. A zero-byte .nojekyll hosting marker is acceptable outside the archive, but not an altered old asset.
5. Build the separate Stage28 route from one SHA-pinned source checkout; original chair, command and fin GLBs remain byte-identical. Verify exact retained V3 faces, CC0 scans, Blender/Cycles AO/PBR, geometry, JavaScript and 5 loaded GLBs.
6. Merge only this publication branch after full PR preflight success. Verify subsequent real Pages deployment, remote HTTP assets, original route SHA256s, and actual hosted Chromium desktop/mobile screenshots including HUD non-overlap and error logs. Do NOT announce a live link before those pass.

## Failures isolated and corrected
- CI 42668549728: fail-closed on dynamic generatedAt and extra .nojekyll.
- CI 42669256566: player snapshot verified; two prior published command GLBs had nondeterministic export bytes.
- CI 42670049396: all 51 old published assets now match SHA256 PASS; relative Blender --python path was wrong.
- CI 42670719337: complete actual Stage28 model export passed, but bundle anchor typo p.y instead of p.yaw failed; exact source anchor was corrected and moved to fast preflight at SHA 820ce75ca5134a43cbbdb6c977be216e250575f5.
- CI 42671800681 and independent V4 42671800470: BOTH failed before any jobs were created. No job logs exist; rerun API refused with 403. This is an Actions scheduling or platform blocker, not evidence of a source test. This documentation-only commit triggers a new normal preflight. Do not bypass technical or remote gates.

Rollback: revert workflow-only PR #85 and restore preceding known-good approved Pages release. Production game and experimental art were never merged.
