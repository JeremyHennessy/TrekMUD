# USS Asteria Stage27 — one connected forward bridge architectural rebuild (NO DEPLOY)

## Why this is not another micro-adjustment
The visual review of Stage26 `ffeb74ec61421f75ca6cb66df60d2e0cec9c2b88` (Actions [#42639304838](https://github.com/JeremyHennessy/TrekMUD/actions/runs/42639304838), artifact 13685512441) measured only 0.9456% pixels changed in the 1280x800 normal command camera relative to Stage23, 0.0003% mobile, 1.5265% ceiling and 0.3795% wall (>10 max RGB difference). Human inspection confirmed negligible practical improvement. Stage26 is TECH PASS / ART NO-GO. Do not build on its two local soffit replacements or publish them.

Stage27 starts **directly from Stage23 source** `4aff55de9fedafa4ee5b68d2f9146a96a157df17` and experiments with one substantially broader, integrated unit: forward wall / ceiling / viewscreen surround. All original V3/campaign/control code remains read-only.

## Immutable sources and physical geometry authority
- Protected published `main`: `399de4debfa202e29dbe9887cf11f82cbfbc5b3b`; no changes permitted.
- Frozen original V3 authored source git blob: `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`, 106,988 triangles; the exact model and player controls are not edited.
- Source line 250 of `ui/3d-preview-v3/index.html` authors a forward structural screen outer box `box(0,2.04,-6.38,7.2,3.15,.24)`, meaning x [-3.60, 3.60], y [.465, 3.615] and z [-6.50, -6.26]. The original display is 6.43 m wide, centred at y=2.02, with its visible dark display z approximately -6.115; do not obscure those pixels.
- Frozen Stage12 comparison: commit `e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b`, Actions #42524417159 and SHA-pinned browser reference images; this is NOT user approval of its artwork.
- Stage23 technical build / ART HOLD: PR #79 commit `4aff55de9fedafa4ee5b68d2f9146a96a157df17`, Actions #42595417600 artifact 13664500249. It is the direct same-source predecessor for independent command/mobile/ceiling/wall screenshot A/B.
- Stage26 ART NO-GO: PR #82, not inherited, merged or deployed.

## One cohesive, testable structural hypothesis
Rather than a subtly changed pair of ceiling joins, replace the repeated disconnected Stage23 flank wall/upper fascia/lower plinth and roof underpanels as one physical front-of-bridge unit, with:
1. Two full-height, physically returned continuous scanned-PBR flank bulkhead skins with a shared upper fascia and service sill, in exactly source-measured elliptical sectors 36–45 and 67–76.
2. ONE physically closed, curved UV-mapped panoramic forward roof shell spanning all forward sectors 36–76, with one narrow manufactured reveal. Covers the visual gap above the centre screen, not just the former side soffits.
3. An integrated crown, lower sill, two closed vertical structural side returns, two fine inner trim reveals and captured black crown joint around the original *measured* viewscreen extents—7 manufactured pieces, with original display fully retained.

Six original Stage23 furnished light housings / diffusers and their lighting positions and powers are deliberately unchanged; the current hypothesis is **large integrated architecture**, not light-intensity tuning. Reuse source-proven Poly Haven `painted_plaster_wall` CC0 photographic PBR, original satin hardware and corrected local-ray UV1 Cycles AO handling. No new unlicensed textures or AI-generated image maps.

Expected: **35** ZONE20-tagged architecture mesh objects and **65** envelope GLB meshes including the 30 unchanged full room objects; exact 864 source wall/roof faces excluded as Stage23, original floor, screen display, hero furniture and walkable boundaries intact. Candidate is a **new architecture experiment**, not an approved full-ship design.

## Fast reject / full acceptance gates
- First validate source presence + original screen extents, Python code, exact mesh counts, excluded faces, materials, GLB triangle bound, smooth/flat normals, UV0/UV1 and scan provenance. Reject non-manifold or self-crossing panels, large blotches, fake dark strips and ungrounded geometry.
- Render actual furnished Blender/Cycles A/B and original Stage12/Stage23/Stage27 matched-camera Chromium software-WebGL screenshots: normal desktop command, mobile command, aft, wall and ceiling. Review visually, not by pixel differences alone; a large visible change that looks worse must be rejected.
- Preserve HTTP/page error logs, physical walking/waypoint and mobile HUD legibility; require no screen occlusion. Software-WebGL tests are not equivalent to iPhone GPU performance verification.
- Compare directly against archived **Stage23** (not only Stage12) before declaring a visual improvement. Stage26 failed because the normal command and mobile views barely changed; do not repeat that.
- Do not merge, modify `main`, change the existing Pages routes or publish any optional review route unless full technical + inspected artistic gates pass, then require exact unaffected Pages file hashes and independent hosted screenshot QA.

## Run handoff
Report exact commit SHA, PR, Actions run/artifact URLs, camera-matched rendered image proof, geometry stats, screen visibility, art verdict and next single high-impact action. If the visually broader candidate still fails, reject it without building another small patch on top. The default original UI, camera, navigation, original source V3, control game and published routes are immutable.
