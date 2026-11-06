# USS Asteria · Cinematic Bridge V4 · First Authored-Asset Build

**Status: Visual quality candidate. Not an approved baseline.**

This is a new, independent, walkable original USS Asteria Main Bridge (`AST-D01-BRIDGE`) for the TrekMUD fictional starship, year 2372. It uses a glTF 2.0 mesh asset pipeline, PBR materials, a pinned Three.js WebGL renderer and baked-in 3D console construction. This is **not** a replica of the Enterprise-D, nor proof of any canonical bridge floor plan.

## Sources and preservation

- Approved V1 route `/3d/`, V2 route `/3d-preview/`, V3 route `/3d-preview-v3/` must remain byte-for-byte untouched.
- Main TrekMUD map, PADD, character, chronicle, ship class, assignment and runtime state must not be changed.
- Source room ID `AST-D01-BRIDGE`, Deck 1, restricted; only approved topology neighbor `AST-D01-HUB-C`. Sealed service hatches are scenic. This browser exploration **does not move the player in the RPG.**
- V4 build branch originated at `main@96a30261833666911447774027b19ce091585596`.

## First implementation slice

- `scripts/build_asteria_v4_assets.py` (repository location) is an **offline, deterministic 3D geometry authoring script** using NumPy, trimesh and Pillow. It emits a single GLB containing approximately **416 named meshes and 61.6k triangles** with embedded PBR base-color, tangent-normal, metallic/roughness and AO textures. The source code is the editable construction definition. **No Blender `.blend` files are claimed**; true artist-authored Blender assets are a later fidelity gate.
- Sculpted curved captain's chair with physical fabric shell, piping, seat cushioning, arms, metal pedestal and hand controls. Full oval bridge shell, wall bays, inset panels, cove lighting, aft door, viewscreen surround, command platform, continuous swept flight desk, flight seating and science gallery are modeled as real geometry.
- Three.js `0.187.0` / `GLTFLoader` and esbuild `0.25.12`, bundled locally and version-pinned, without runtime CDN or production PADD dependency.
- ACES tone mapping, PBR materials, directional/point practical lighting, soft shadow maps on desktop, lower-cost mobile lighting. The exterior is an original 3D starbase view with depth, not an Enterprise replica.
- Existing first-person interaction semantics: WASD / arrow keys walking, drag to look, shift fast, R reset, station jumps, mobile virtual joystick; no campaign writes.

## Build and verification

The GitHub workflows install the exact pinned geometry-generation and JavaScript build dependencies in an **isolated build job**, generate `asteria-bridge-shell.glb`, bundle Three.js to `app.js`, publish the assets under `_site/3d-preview-v4/`, then run glTF/asset checks and headless Chromium WebGL screenshot tests. The original PADD generator runs independently and is not rewritten.

Visual gate: capture `aft`, `command`, `flight` and `science` at a matched field of view; compare real V3 and V4 screenshots with no changes to earlier versions. Verify in a physical desktop and phone browser before considering V4 visually approved. The initial software-WebGL screenshots prove renderability, not cinema-grade photorealism.

### Known limitations

- Although these are real glTF asset meshes with embedded PBR maps, the geometry and materials are **programmatically authored**, not hand-sculpted by a production artist. This is not claimed to equal final production-quality Blender work.
- Dynamic screen graphics are generated at runtime as canvas emissive surfaces and are not actual flight instruments.
- Real GI/lightmap baking, calibrated reflection capture, physically accurate optical response, scanned surfaces, asset compression and physical-device FPS remain next steps.
- Initial bridge dimensions derive from the existing approved *visual model*, not from a television set blueprint.

## Controls and observation

`/3d-preview-v4/?capture=aft|command|flight|science|viewer` provides repeatable camera poses and skips the opening modal for screenshot review. The debug read-only marker `window.__asteriaV4` exposes mesh count, triangle count, position and room identity. No game-state API is invoked.