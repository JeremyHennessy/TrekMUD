# Bridge geometry study — standalone delivery

This folder contains a **reference-guided, manually modeled 3D bridge interior** inspired by the original *Star Trek: The Next Generation* production footage. It is not an exact set scan and is not a successful photorealistic Gaussian-splat reconstruction.

It is published on a separate development branch to preserve the approved TrekMUD / USS Asteria application. **No Mudd game UI, campaign state, or existing viewer is changed by this experiment.**

## Open and use

- **`index.html`** — browser walkthrough with W/A/S/D, mouse-look and five fixed view presets. Fully self-contained (embedded geometry, generated textures and fallback images). Download the raw HTML file and open it in Chrome or Edge. Opening it in GitHub's source-code viewer does **not** run the app.
- **`bridge_reference_model.glb`** — independent editable 3D asset; load into Blender or another glTF-compatible application.
- **`Bridge_Model_Camera_Sweep.mp4`** — a short rendered sweep of the actual model.
- **`preview_hero.png`** — still rendered from the model.
- **`source/build_model.py`** — reproducible mesh and texture generation using Python, NumPy, Pillow and trimesh. Running the script writes a new GLB beside the script; it does not alter the published prebuilt file.
- **`source/viewer_template.html`** and **`source/pack_viewer.py`** — original browser-viewer authoring tools (packing also requires generated preview JPEGs).

## Verification

The four published binary artifacts are **byte-for-byte identical** to the locally generated files at publication (verified against Git blob SHA-1 hashes before referencing them in the branch).

The GLB was imported into an independent 3D renderer and viewed from multiple angles. The browser file previously passed JavaScript and 2D fallback tests, but its **WebGL 2 first-person walkthrough was not verified end-to-end** in the execution environment. If WebGL 2 is unavailable, the browser file shows verified rendered stills; it does not provide 3D movement in fallback mode.

## Scope, limitations and provenance

The set shapes, proportions, positions and details are interpretive rather than surveyed. There are no full-scene trained Gaussian splats in this package. No original film clips or television frames are redistributed in this branch; the preview images and MP4 were rendered from the modeled geometry. References to Star Trek are descriptive and do not imply affiliation with or endorsement by rights holders.

This branch is **not** the live GitHub Pages deployment. Its assets can be downloaded from GitHub, but GitHub's ordinary file-viewer cannot run an HTML app. Do not publish to the existing game's live Pages configuration or merge this into `main` until separately reviewed and authorized.
