# USS Asteria — fidelity recovery V5 candidate

## Why this experiment exists

The user correctly reported the separately authored V4 bridge looked worse in several ways than V3: exaggerated chair scale, blank wall panels, empty side sectors and reduced set cohesion. V4 also had a misleading Gaussian-splat experiment: loaded records without visible splats. The V3 set arrangement is a better source of visual geometry than the V4 shell.

## Exact continuity

**The source model is not recreated from memory.** `scripts/extract_asteria_v3_for_v5.py` evaluates the immutable `ui/3d-preview-v3/index.html` (Git blob `74a154ae62bccb0c16d03c2ecf791a64ab19ce81`) with the original geometry-generating scripts, capturing its actual 106,988 triangles, 3D positions, normals, colors, UVs and console atlas. It validates the exact source hash and refuses to build on drift.

`build_asteria_v5_assets.py` exports those triangles to genuine glTF 2.0 as nine physically based material groups plus one unlit forward starfield plane. Geometry bounds remain `[-7.55,-.35,-6.558]` to `[7.55,4.462,6.558]` metres. Its near-neutral procedural surface maps represent physical wall composite, carpet pile, fabric upholstery, brushed metal, cast material, smoky glass and practical diffusers. The maps are a *measured material rendering study*, **not photogrammetry, Gaussian splatting, or photo-realistic material scans**. The original V3 screen atlas remains intact.

## No-risk presentation / quality gates

Independent route `/3d-preview-v5/`; exact V3 layout, original in-ship first-person camera poses, game collision volumes, HUD layout, station buttons, keyboard/mouse and mobile joystick. **No PADD, campaign, or V1–V4 file change.** The view never writes the game state.

The Three.js renderer uses physically based textures, filmic tonemapping, studio area-light approximation, a restrained reflection probe, optional directional upholstery shadows and floor-level contact attenuation. Asset generation is offline and deterministic from the V3 code. Runtime does not depend on a remote CDN. The generated GLB is bundled with Pages only after PADD/game checks pass.

CI must capture matched V3 vs V5 screenshots at the exact same 1280x800 viewpoints (aft, command, flight), V5 science and mobile, and run real Chrome keyboard movement. **A passing build or newer rendering engine never constitutes approval.** Review screenshots and reject the experiment if it visually regresses. Do not replace the V3 route, the V4 route, or any approved visual checkpoint without explicit authorization.

### Limits

Professional film realism would still require professional asset modeling, proper physically captured PBR surface scans and global illumination; this study addresses V4's destructive layout changes and tests a better renderer without sacrificing the V3 shape language.