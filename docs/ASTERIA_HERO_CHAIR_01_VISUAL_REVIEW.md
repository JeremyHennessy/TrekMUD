# USS Asteria hero chair — first real Cycles review (candidate, unapproved)

Date: 2026-11-06 (America/Halifax)

## Preserved starting point

- Source chair proportions and original command position were taken from `ui/3d-preview-v3/hero-v3.js` (frozen V3 blob `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`).
- The separate chair experiment is built atop the V5 fidelity branch via PR #41. **No original V1–V5 viewer, PADD, world state, campaign, collider or existing geometry was modified.**
- Proven command-chair face-winding fix in PR #41 remains separate and unchanged.

## Confirmed outputs

- Draft PR #42 / `experiment/asteria-hero-chair-01`.
- A deterministic Blender source script generates an editable `.blend`, a chair-only `.glb`, and four actual Cycles viewpoints.
- Blender 4.0.2 and glTF validation CI succeeded; measured GLB has **47 geometry objects**, **26,908 triangles**, **10 named materials**, **~600 KB** as exported, approximately **1.58 m wide × 1.81 m high × 1.01 m deep**. The floor, lights and camera were not exported with the chair.
- Successful independent run `42328510896` created front, rear, three-quarter and detail images at 900×800, but these frames were inadequately framed and overexposed.
- Run `42328806275` used wider offline review cameras only; verified four-view images and chair-only GLB again. No mesh geometry changed.
- Run `42329016688` adjusted only Cycles display exposure from 0 to -1.4 EV. The first front render had about 57.4% of pixels above RGB mean 212 (whole image, not masked to chair); this dropped to roughly 0.1% in the exposure-controlled render. The original command chair image therefore became inspectable rather than nearly white.

## Actual human visual assessment

**The modeled chair is structurally more complete but not yet photorealistic.**

Improvements observed: full-thickness curved shell, rounded upholstered back, separate armrest housing, individual command controls, metal supports and pedestal. Compared with the earlier V3 chair, these details are not merely texture decals.

Remaining failures: front upholstery is too uniform and smooth, inserted lumbar/shoulder pads look like raised flat panels, seat lip is rigid, seam piping is visually simplistic, and the rear shell reads as clean CGI instead of a photographed practical-set component. The current Cycles fabric bump is procedural and is **not exported into the GLB**; browser fidelity is therefore not established.

The standalone studio images cannot establish how the model will fit beside the existing Asteria consoles or whether camera/collision behave correctly. No user visual approval, renderer quality gate or public release is claimed.

## Next controlled asset improvement

Use a physically photo-scanned CC0 upholstered-fabric PBR set (e.g. Poly Haven's 'Velour Velvet') at a modest resolution, with correctly unwrapped fabric UVs, and bake/pack normal, roughness and palette-correct base color into the candidate GLB. Keep old material workflow independently reproducible, compare images at matched cameras/exposure, and measure browser export texture payload before replacing any existing asset.

Never publish a live preview or provide an untested chat file link just because the CI is green.
