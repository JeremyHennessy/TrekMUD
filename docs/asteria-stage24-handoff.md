# USS Asteria Stage24 — source-identical recessed-fixture light-intensity attribution (NO DEPLOY)

## Exact parents and non-approval
- Base is Stage23 draft PR #79 SHA `4aff55de9fedafa4ee5b68d2f9146a96a157df17` (technical PASS, *art hold*), not production. Stage23 predecessor Stage20 `f4d4af6700be1dff551ca560a441de230120e5f0` was also visually rejected; Stage22 is a separate hatch idea and is not combined here.
- Production branch and latest authenticated artifact baseline at start: `399de4debfa202e29dbe9887cf11f82cbfbc5b3b`. Frozen Stage12 preview/camera reference: `e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b`, run `42524417159`, artifact `13634679552`.
- V3 original browser model Git blob `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`, and original 864 source faces excluded by Stage23, are immutable. Do not touch game controls/UI, PADD, collision, scenario data, room graph, old URLs.

## One hypothesis
Stage23's six late-injected `THREE.PointLight(0xffddbc,1.85,2.7,2)` near the new soffit diffusers contribute materially to the upper-left bright wall/ceiling flare and HUD contrast loss. **Change only those six light intensities** from `1.85` to `0.45` while holding emitted color, falloff, decay, placement, GLB geometry, UV/PBR maps, masks, app cameras and HUD source exactly constant.

The CI job first builds original Stage23 runtime, copies it *within the job* to `_site/3d-preview-v5-command-stage23`, then recompiles the candidate via the one-string source change at `_site/3d-preview-v5-command-envelope`. Except `app.js`, every file is hashed equal between those two job-local routes. Nothing is published.

For comparable genuine **Blender/Cycles** furnished A/B, the six Stage23 Cycles area-light proxies at 42 W get a third matched same-model `zone24` mode at 10.2 W (same fraction .45/1.85). These proxy Watts and WebGL point-light numerical intensity are *not calibrated to identical physical units*. All other studio lights and five imported original/proposed models are unchanged. This is one physical-light-intensity hypothesis in both renderers; it must not be mistaken for proving parity between engines.

## Decision test
- Real full-scene 1280 command, ceiling, wall, aft and 390 command **same-run** Chromium software-WebGL matched Stage23 vs Stage24 screenshots, with exact model/UI SHA equality and page/network error checks; plus the existing 14 Stage12-vs-candidate screenshot, walking and control/source gates.
- Independent Cycles 6 images, same furnished geometry/camera/environment, stage20 and zone24 difference only in the six lights' wattage. AO, material/UV and CC0 provenance validated by the existing workflow.
- Report pixel differences AND regional upper-left near-white clipping, local luminance statistics and HUD contrast concerns. Those are diagnostic metrics, **not** automated claims of artistic improvement. Actual images need human/independent visual comparison. If the washout remains, reject this test and investigate the separately authored emissive opacity/strength in Stage23's actual diffuser surfaces next (do not stack that change into this experiment).
- Stage23 command/mobile effect was nearly zero. The same camera framing here is intentionally preserved; no pretense of mobile realism advancement or approval.
- No merge, no production deploy, no optional publicly hosted route until source/Cycles/Chromium/nav plus actual visual acceptance and independent remote QA pass, unaffected Pages hashes recorded, and owner's explicit authorization. No automated publishing workflow is invoked.

## History
Single *reversible*, one-commit evidence experiment. Pinned source screenshots and last production artifact are evidence of historical release, not a fresh reachable hosted URL or physical-GPU validation. The Actions job's _site is private and temporary.
