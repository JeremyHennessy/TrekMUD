# USS Asteria — isolated 3D Gaussian Splat feasibility spike

**Status: experimental, not a new ship interior, not user-approved, not published.**

This tests **Spark 2.4.0 + Three.js 0.187.0 + an existing original Asteria GLB** in one mixed scene. It exists on an independent branch and does not touch the approved `/3d/`, `/3d-preview/`, `/3d-preview-v3/` or `/3d-preview-v4/` routes, MUD campaign, player location, collision graph, or PADD interface.

## Actual question we are testing

Can the Asteria maintain correct room geometry, free walking, door boundaries and current 3D furnishings while rendering selected surfaces as Gaussian splats, using a locally bundled browser renderer and no runtime CDN?

The proof uses *only the captain's chair*, deliberately sampled from the **existing V4 mesh** into around 20,000 Gaussians. The source mesh retains its material base-color texture; the conversion pre-bakes one rough light estimate. This is **NOT 3D Gaussian Splat training from photographs**, **NOT a generative/photorealistic asset**, and **NOT a claim of higher visual quality**. It should usually look blurrier than a good PBR model. A successful test proves compatibility, not that Gaussian splats solve V4's poor set design.

## A/B experiment

- Query `?capture=command&chair=mesh` displays the same original V4 meshes.
- Query `?capture=command&chair=splat` replaces the captain chair's *selected visible surfaces* with `.splat` Gaussians while leaving floors, walls, controls, and collision geometry as real meshes. If the splat cannot initialize, the original meshes remain visible.
- The same `aft` camera angle should also be captured in both modes.
- Do not judge the scene quality from a single angle. Capture aft, command, side and chair close-up; inspect splat floaters, fuzziness, occlusion, transparency, lighting consistency and FPS.

## Production recommendation if this works

**Hybrid, not all-splat:** Retain real layout and collider GLB for room topology and reliable interaction. Add *authored/captured* splats for richly detailed static surfaces only. Keep animated doors, readable displays, and close-up interactable furniture as high-quality PBR meshes where necessary.

### High-quality splat source strategy

1. **Best for accuracy:** model a real set-quality Asteria bridge with exact planned geometry, fixtures and original labels. Render *many* sharp, consistent viewpoints from a path through the room using physically plausible lighting. Run a **trained** 3DGS pipeline (for example nerfstudio Splatfacto) on the multi-view render plus known camera poses, then clean/optimize in SuperSplat. Note that splatting can't create details absent from the high-quality source assets.
2. **Best for a quick high-quality visual exploration:** experiment with **World Labs Marble** generating an original science-ship bridge scene from a detailed prompt and consistent reference imagery or a 3D layout. Export `.spz` / PLY visuals plus its collision GLB, then test inside Spark. **Generative worlds may change the room proportions, door positioning, signage, and console arrangement**. Treat the generated output as a *concept candidate* until its topology can be validated against the canonical USS Asteria map. Marble may require paid access; no API call or charges are authorized by this experiment.
3. **Avoid:** multiplying existing synthetic triangles into Gaussian points and claiming photorealism, using a single still-image projection to fake a walkable 3D room, merging experimental AI assets into the approved bridge without comparison, or copying an Enterprise-D set plan.

## Reproducible test

From the TrekMUD repository root with Python packages installed from `ui/3d-preview-v4/asset-requirements.txt`:

```
python scripts/build_asteria_v4_assets.py --out experiments/asteria-3dgs/dist/models
python experiments/asteria-3dgs/generate_splat.py --glb experiments/asteria-3dgs/dist/models/asteria-bridge-shell.glb --out experiments/asteria-3dgs/dist/models/captain-chair.splat
python experiments/asteria-3dgs/tests/verify_splat.py experiments/asteria-3dgs/dist/models/captain-chair.splat
cd experiments/asteria-3dgs && npm ci && npm run build
```

Serve the `dist/` directory with a local HTTP server; open `?chair=splat`. The package lock will be captured from GitHub CI's first `npm install` and subsequently committed, after which the recipe will use `npm ci`.

Technical criteria: generated splats are finite and dimensionally aligned, the two rendered variants load without JS exceptions, WASD and viewpoint jumping work, no gameplay state changes, and the splat-enabled scene has no severe black screens or alpha/occlusion artifacts. A visible improvement requires **human comparison of real screenshots** and is NOT assumed.

## Research sources

- Spark: https://github.com/sparkjsdev/spark
- Spark loading: https://sparkjs.dev/docs/loading-splats/
- PlayCanvas SuperSplat: https://github.com/playcanvas/supersplat
- Nerfstudio Splatfacto: https://docs.nerf.studio/nerfology/methods/splat.html
- World Labs Marble: https://www.worldlabs.ai/blog/marble-world-model