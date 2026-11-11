# USS Asteria — V4 Cinematic Set Rebuild: engineering and art specification

**Status:** PLAN / NOT BUILT / NOT APPROVED  
**Source checkpoint:** `main@96a30261833666911447774027b19ce091585596` (November 6, 2026)  
**Target preview:** `/3d-preview-v4/` under the existing GitHub Pages deployment  
**Ship/room:** USS Asteria, NCC-63542, Nebula-class, 2372; `AST-D01-BRIDGE`, Deck 01

## 1. Why V4 is not a conventional pass

Screenshots from the actual v3 WebGL build show a credible navigable prototype but not convincing photographic scenery. The main limiting factors are: simplified chair/console/wall silhouettes; flat or uniformly shaded carpet, walls, and upholstery; baked-in/modeled UI rather than layered display glass; broadly uniform lighting without rich indirect bounce; a shallow starfield screen; and limited cinematic staging. Higher procedural triangle counts alone will not solve these issues.

**V4 is a new asset+rendering pipeline, not a re-skin of v3's custom WebGL 1 triangle builder.** Do not replace /3d/, /3d-preview/, or /3d-preview-v3/ during development.

## 2. Approved invariants

- Original `/3d/` baseline at `1bec688cc57c7cea6c2954460e7b35e7aa426574` remains untouched.
- Existing v2 baseline at `fe94ca1deb5b8b36b7cedd304c7a0aa8830e4863` remains untouched.
- Current v3 base at `96a30261833666911447774027b19ce091585596` remains untouched.
- Existing PADD UI, campaign state, story continuity, game rules, room topology and save files remain untouched.
- Stable room ID `AST-D01-BRIDGE` is the only modeled room. Its approved explicit neighbor is `AST-D01-HUB-C`; the aft access can be visually represented, but no new traversable door/room is assumed. Other hatches stay sealed/scenic.
- The 28-deck, four-pod-level architecture remains canonical **TrekMUD setting geography**, not a real-world or television blueprint claim.
- Presentation envelope starts from the current bridge's approximately 15.1 m × 13.1 m ellipse; this is an *existing model dimension*, not a verified Star Trek set dimension. Keep the major working zones and navigation logic, but allow collision volumes to be retested against new authored geometry.
- No script may write to RPG state. Scene controls are exploratory only.

## 3. Original design identity (do not recreate Enterprise-D)

A refined, functional 2372 science-exploration ship bridge: muted sand composite wall shells, plum/charcoal upholstered command furniture, satin bronze/pewter touch points, blue-grey textile carpet and low-gloss black instrumentation. Broad curved structural frames; reserved illumination; clearly separate flight, command and science zones. Subtle wear and plausible workmanship rather than overly futuristic LED strips or theme-park decoration.

Reference principles: built human-scale set, functional ergonomics, surfaces that react naturally to light, visible layering and structure, believable joints and scale. Avoid copied Enterprise-D bridge plan, uniforms, insignia, exact chairs, or copyrighted console graphic layouts.

## 4. Architecture

1. Create isolated `ui/3d-preview-v4/` source package with locally **bundled, pinned** Three.js and a reproducible lockfile, no runtime CDNs.
2. Target stable Three.js `WebGLRenderer` (WebGL 2) for baseline interoperability. Do not make experimental WebGPU a mandatory dependency. Evaluate optional WebGPU only after WebGL version passes.
3. Mesh assets authored in Blender or an equivalent genuine polygon-modeling workflow, exported as glTF 2.0/`.glb` with consistent transforms, named objects, UVs, materials, and glTF validation. The current execution container does **not** include Blender: first establish a reproducible authoring environment before claiming native .blend assets exist.
4. Use glTF PBR metallic/roughness workflow: base color, normal, packed roughness/metallic, AO and emission, with optional clearcoat for smoked instrument glass. Use correctly declared texture color spaces. Avoid flat procedural noise as a substitute for actual materials.
5. Use high-quality authored/baked indirect light and occlusion in fixed architecture, with restrained real-time key/practical lights, soft contact shadows and reflection probes/environment where feasible. glTF doesn't magically transfer Blender's area lights or lightmap UV assignments; handle baking, transport, and runtime material injection explicitly and test visually.
6. Load models through `GLTFLoader`, use mesh compression (Meshopt/Draco where validated), texture compression (KTX2/Basis) where supported. Maintain a lower-resolution mobile asset profile.
7. Maintain independent first-person navigation on room collision meshes/volumes with swept circle/capsule checks, camera clipping protection, physical eye height, door boundary guards and existing keyboard/touch interactions. Do not bind these to campaign movement.
8. Build a reproducible screenshot harness (Playwright or controlled Chromium) that captures **identical** positions, camera FOV, exposure and viewport sizes for V3 vs V4.

## 5. Ordered room-part implementation: one verifiable slice at a time

| Order | Asset / system | Scope | Done when |
| --- | --- | --- | --- |
| 0 | Source and browser pipeline | Three.js bundle, GLB scene loader, fixed camera baseline, local static server, optional offline cache | Loads a single GLB on desktop and phone-sized Chromium; valid glTF; no CDN; old routes unaffected |
| 1 | Architectural shell | Fully contoured oval walls; frames, deep reveals, structural ribs, floor/coving, ceiling coffers, sealed hatches, viewscreen surround | Five fixed camera captures show recognizable full-scale room geometry without gaps, mirrored faces, floating details or ungrounded seams |
| 2 | Command focal point | One original, sculpted captain's chair, visible back/seat padding, cast pedestal, ergonomically plausible armrests, real raised command dais and two enclosed consoles | Chair and podium read as manufactured objects in close-ups; no visible intersecting geometry; full walk path remains unobstructed |
| 3 | Flight station | Integrated curved flight/operations workstation; individually inset monitor glass; tactile keys; concealed structure; operator seats and believable foot/leg clearance | Forward and oblique cameras show true depth, no panels covered, consistent scale, no floating controls |
| 4 | Side science stations | Individually authored desks/wall terminals, recessed screen frames, side seating, set lighting, rear gallery structure | Side camera views show an understandable working set, not a row of duplicated blocks |
| 5 | Physical materials | Fabric weave and upholstery seams, matte composite, metal brushing, carpet fiber normals, rubber gaskets, low-gloss black glass and controlled fingerprints/wear | Material response differs convincingly under a moving light; no checkerboard UV seams or texture tiling issues |
| 6 | Lighting and exterior | Baked indirect bounce/ambient occlusion, practical fixture gradients, tempered shadow softness, restrained specular/environment reflections, believable exterior starbase depth | Aft, command, flight, side and close-up captures clearly demonstrate greater depth than V3 under matched framing |
| 7 | Movement, performance, release | Collision/nav checks, device quality profiles, asset provenance, packaging to new route | CI green, no regression to existing console or campaign, human side-by-side visual approval before V4 becomes an approved baseline |

**Design priority:** Orders 1–3 must look convincingly better *before* adding dozens of monitors or micro-details. A simpler high-quality hero set is preferable to an enormous artificial-looking scene.

## 6. Quality and release gates

### Visual, judged using actual renders
- Capture `aft`, `command`, `flight`, `science`, `viewer` at equal camera position, resolution, FOV and exposure for V3 and V4; add chair, console, panel and fixture close-ups.
- Manually inspect full-size screenshots for silhouette, material realism, shadow fidelity, believable scale, contact with floor, valid screen orientation, clipping, texture repetition, frame seams and highlights.
- Compare V3 and V4 **side by side**, with before/after filenames and version SHA. No claims of photorealism solely from automated success.
- Device screenshot at approximately 390 × 844 and a physical mobile browser before declaring mobile quality approved.

### Functional
- Static glTF validation, license/provenance inventory, no missing assets/404s; successful real-WebGL browser initialization on both viewport classes.
- Test keyboard walking, touch movement, camera rotation, resetting, collisions, doors, and loading state.
- Test that the browser never reads private GM data or writes campaign state.
- Re-run existing player-console, world topology, campaign and PADD CI tests; verify `/3d/`, `/3d-preview/`, `/3d-preview-v3/` remain byte-for-byte unchanged.

### Performance *targets*, not established measurements
- Aim at an interactive 60 fps desktop, 30 fps mid-range mobile; tune quality by device.
- Provisional compressed asset download target: <= 25 MB desktop, <= 12 MB mobile; refine after first scene benchmark.
- Avoid loading all future ship rooms into memory. Unload inactive GLB/textures and share reusable props.
- No release on workflow status alone: inspect actual image output and capture measured device frame times, memory and load costs.

## 7. First build slice to execute

**A.** Build the isolated Three.js/GLB minimal scene and automated render harness.  
**B.** Model only the high-fidelity bridge shell, command dais and one complete captain's chair.  
**C.** Apply at least four plausible authored PBR materials (carpet, upholstery, painted panel, brushed metal) and a small baked-light test.  
**D.** Produce three paired screenshots against V3; user sees images, not a claim that the change is better.  
**E.** Only after that gate, replace the full flight console and continue the remaining parts.

First-slice exit: a user can open the isolated V4 page and walk around a visually convincing, physically scaled shell with one true high-fidelity hero chair; screenshots and tests support the visual difference. No partial assets in production. This is a **plan**, not an assertion that V4 has been created.

## 8. Open technical blockers

- Blender binary is absent from the current local execution environment; select/install a deterministic art build environment first.
- The actual PBR texture source/license and baking path must be established, not invented. Document origin, licenses, resolution, compression and export tool version.
- Verify Three.js package version and Vite or alternate bundler in the isolated V4 worktree; do not upgrade the existing PADD.
- Verify glTF lightmaps, reflections and GPU performance in a real browser after implementation; no claims based on Blender viewport alone.
