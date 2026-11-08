# USS Asteria — integrated upholstered backrest A/B

Date: 2026-11-08. **Technical A/B passed; visual improvement observed; photorealism and production release NOT approved.**

## Exact preservation

The approved/frozen V3 source remains Git blob `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`. The verified in-context chair and browser work in draft PR #44 is the experimental base. This branch changes **no** V3/V5 public routes, player UI, character, campaign, topology, flight consoles, bridge layout, collision or live deployment. The chair script preserves its default; `--integrated-back` must be supplied to produce this new visual candidate. Revert by omitting that option or using the PR #44 head unchanged.

## Problem and rejected prior test

The former chair used two separate raised lumbar/shoulder slab meshes plus three raised transverse tube seams. Draft PR #45's smaller inset-softening experiment was rejected because real front Cycles images barely changed (whole image mean RGB difference ~0.249, backrest crop ~1.466); that branch was closed without merging.

## Single structural hypothesis: integrate backrest padding

An independent Blender/Cycles A/B run `42447906084` produced the original 26,908-face chair and the new 31,484-face chair at identical 900×800 camera, lighting, exposure and pinned scanned mauve-fabric PBR maps. The alternative removes 7 glTF primitives belonging to old independent lumbar/shoulder panels and raised transverse seams, while replacing only the two primitive groups of the physically continuous seat-back. All other chair objects retained identical geometry and the same scanned fabric and surface properties.

The test confirmed:
- Baseline: 47 geometry objects / 26,908 triangles
- Candidate: 40 geometry objects / 31,484 triangles
- Unchanged overall chair bounds (within 0.008 m)
- Exact removed objects: two lumbar primitives, two shoulder primitives and three horizontal raised seam tubes
- Only other modified geometry: the upholstered backrest front/back surfaces
- Backrest crop average absolute RGB difference: 16.62 across matched Cycles frames
- Editable Blender model and genuine textured GLB produced

Actual images were inspected side-by-side. The new backrest is significantly less like rigid separate plates; lumbar and upper padding follow continuous sculpted contours, and seam depressions are modeled in the upholstery rather than stacked floating objects. It remains visibly clean CGI with simplified armrests and an overly basic surrounding practical set. **This is an improvement for the targeted defect, not final artistic approval.**

## In-context browser acceptance — completed

After the offline visual A/B review, the same branch enabled `--integrated-back` only in its independent chair-review build. **GitHub Actions run `42448065265` passed every stage** in real Chromium software-WebGL. The original room geometry was unchanged apart from the exact 16,272 original V3 captain-chair faces already excluded by the verified parent build. The new hero chair contains 31,484 faces and was loaded once with the scanned-fabric maps.

Confirmed browser evidence:
- Full desktop and 390×844 mobile-sized screenshots from aft, command, science, and an extra read-only chair camera. No JavaScript page errors or external runtime asset requests in the checked views.
- Focused chair-area mean absolute RGB difference versus preserved V5 control: **5.38**. Unrelated central forward-command region difference: **0.00**.
- Real frame-gated WASD movement from (-1.23, 4.80) to approximately (-1.163, 4.658), followed by exact command waypoint (-2.32, 2.15).
- Mobile-sized browser station-button interaction successfully reached flight control at (0, -1.32), yaw 0.
- Source check passed: original V1–V5 UI routes, game map, campaign files, and PADD unchanged. The candidate remains on a separate draft branch and is not deployed.

I inspected the actual aft, chair-front, and mobile-sized images. The upholstery now reads as a continuous cushioned form, removing the old flat rectangular panels. The rear shell and chair mounting are still simplified, and the surrounding set's console, wall, texture, and indirect-lighting quality remains noticeably below photorealism. This is an **accepted technical integration and limited visual improvement, not final artistic or user approval**.

No externally accessible preview has been verified. Do not merge, publish or offer a speculative file or web link based on this experiment. Physical iPhone interaction and GPU FPS remain untested.
