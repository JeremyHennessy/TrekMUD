# USS Asteria — chair front shading root-cause evidence and V5 candidate gate
Date: 2026-11-06

## Confirmed defect and root cause

The V3-exact V5 GLB imported into Blender/Cycles produced an almost-black centre on the captain's chair. This was visible in actual matching chair-front renders, with all camera, light and material settings held constant.

A new **read-only source triangle ray probe** identified the camera's nearest surface as `material 5 / upholstery` with source vertex color approximately `[0.631, 0.549, 0.588]`, not an unlit black-glass plane or missing texture. Its face winding was **opposite** to its stored vertex normal: geometric normal approximately `[-0.011,-0.171,+0.985]`; imported shading normal approximately `[+0.007,+0.170,-0.985]`. The source contained 20,544 opposed upholstery faces out of 23,744 globally and 5,136 opposed faces out of 5,936 upholstery faces near the command chair.

Evidence: workflow `Asteria chair material ray diagnosis (no Blender)`, run `42306141795`. The experiment does not establish the general validity of flipping unrelated upholstery elsewhere; only a focused command-chair repair was tested.

## Scoped correction and A/B

`scripts/asteria_trial_chair_winding.py` cloned the frozen source arrays into an isolated output directory, and swapped triangle vertex ordering only for the 5,136 command-chair upholstery faces whose normals opposed face winding. It did not move a vertex, change a texture coordinate's vertex association, relocate the chair, change a collision volume or alter a public browser file.

In matched 960×600, 24-sample Blender/Cycles chair-front renders:

- Original: the selected centre-chair image region had 94.22% pixels with all RGB channels below 3.
- Corrected experiment: 0.00% of that same region were near-black.
- Original region RGB mean: `[6.10, 5.16, 5.39]`.
- Corrected region RGB mean: `[158.94, 137.66, 140.40]`.

Actual renders were inspected side by side and show visible mauve-grey upholstery in the corrected candidate. **The narrow material/shading defect is fixed in this test**, not the bridge's overall fidelity.

Evidence: successful isolated Cycles test run `42306399446`. The original V3 source hash and room triangle count were retained.

## V5 browser QA

The same operation is implemented as an **opt-in, default-OFF** path within `scripts/build_asteria_v5_assets.py`:

```bash
ASTERIA_V5_CHAIR_WINDING_REPAIR=1 python scripts/build_asteria_v5_assets.py
```

The opt-in build asserts exactly 5,136 affected faces and aborts if those invariants drift. Unset, the original V5 scene geometry build is preserved. No public Pages route or player campaign is changed by this branch.

A self-contained V5 browser build with this flag enabled passed WebGL screenshots, physical keyboard walking, command station jumps, material consistency and original V3 comparison at desktop and mobile-sized viewports. Evidence: workflow `Asteria V5 chair-winding browser acceptance candidate`, run `42306969139`. The assistant visually reviewed the aft, command, V3 baseline and mobile images. The bridge remains readable and traversable; however its furniture construction, lighting and surfaces remain visibly stylized. No photorealism claim or user visual approval is warranted.

## Preservation and next fidelity gate

- Approved V1 / V2 / V3 routes, existing V4 and V5 public pages, PADD UI, campaign, topology and physics collision logic are unchanged. This is an unmerged draft PR against the V5 candidate branch.
- The earlier optional floating-stitch experiment was rejected and removed; do not reintroduce it.
- The tested face-winding repair addresses a **correct material/geometry layer defect** and is a prerequisite to evaluating a physically modeled captain's chair.
- Next: create an isolated Blender captain's chair replacement with genuinely rounded shell construction, realistic upholstery thickness and calibrated material maps. Visual comparison must include chair front, chair rear, command-wide and walking views before any default enablement or publication.
- Do not substitute GitHub Actions passing status for physical browser-device validation or user visual approval.
