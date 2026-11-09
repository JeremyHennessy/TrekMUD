# USS Asteria Stage25 — Six-opal material emission attribution (NO DEPLOY)

## Exact historic control and approvals
- Production main as observed: `399de4debfa202e29dbe9887cf11f82cbfbc5b3b`; successful historical Pages run `42509385166` and 51-file artifact `13628039000`. Neither implies verified current hosted appearance.
- Frozen Stage12 QA reference: `e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b`, run `42524417159`, real screenshot artifact `13634679552`, three pinned command/aft/ceiling SHA-256 checks.
- Original V3 browser source blob: `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`.
- The Stage22 hatch PR #78 and Stage20/23/24 joinery-lighting PRs #76/#79/#80 remain draft, technically testable but ART HOLD. No owner visual approval. **This branch derives only from Stage24 head `133289b42d6a59a255daab9bd83995a348b7fda4`**. It does not combine the Stage22 hatch or publish an unsupported artwork change.
- Old production and optional routes, campaign, controls, UI/HUD, walk and collision, original 12 ceiling fixtures, game room graph and original source geometry stay untouched.

## Single testable hypothesis
Stage24 reduced the six **new** Stage23 point lights from 1.85 to 0.45 but left the six newly modeled opal diffuser surfaces emitting at their original material brightness; screenshots still show surface-mounted white spots. Testing whether reducing **only these six surface material emissions 5x** makes the architectural lighting more plausible is a one-variable hypothesis. No other light, geometry or interface change is authorized.

The Blender generator gives these six opal mesh surfaces a dedicated copy of the original diffuse/emissive material; this alone is visually identical and leaves the previous twelve roof diffusers untouched. The runner builds the **real** Blender/CC0-scanned-PBR/Cycles-local-AO whole-room GLB exactly once. It copies exact runtime, assets and source to the temporary Stage24 control, then writes a temporary Stage25 GLB changing only one material's three `emissiveFactor` components from 1.0x to 0.2x. Assertions guarantee six actual mesh users, no other glTF scene/material/texture change, identical binary vertex/UV/normal/image payload, and byte-identical app.js, HTML, control model GLBs and unaffected asset files. No production file is rewritten.

The Stage23-vs-Stage24 same-run Chromium comparison remains intact on its original Stage24 job-only route. Stage24-vs-Stage25 tests exact mobile and desktop matched software-WebGL command/ceiling/wall/aft views with actual screenshots, browser/HTTP errors, same navigation and frame readiness; controls/room/collision source cannot change. Furnished Cycles comparison holds Stage24 physical proxy lights at 10.2 W and changes only the six opal surface Principled emissions by the same factor. Blender Watts and WebGL intensity are not mutually calibrated. All screenshot metrics are *change diagnostics*, not proof of physical photorealism.

## Release and rejection conditions
Inspect the actual Cycles and Chromium images, especially bright emitter spots, oblique joins, ceiling readability and upper-left command HUD, including three mobile angles. Reject if there is only a trivial impact, if lowered emission looks like black blank slots, if already-approved surfaces/UI regress, or if source, assets, navigation or browser error checks fail. Even technical PASS is **ART HOLD** until an independent visual gate succeeds.

No deployment, merge, preview-route publication or claim of photorealism. User approval is still required for changing existing published/approved routes. Independent hosted browser screenshot proof, physical mobile GPU/FPS, full collision sweeps and end-to-end full-ship interior remain future gates.
