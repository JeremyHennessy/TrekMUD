# USS Asteria — original bridge layout viewer

**Purpose:** make the 117-component `asteria-bridge-chisel-blockout.glb` layout reference visible and navigable in a normal browser, like earlier Asteria previews.

**URL after release:** `/3d-layout/` in the existing GitHub Pages site.

This is an *original V3-inspired layout blockout*, not a photorealistic ship model and **not Gaussian splatting**. It provides human-scale room structure, an original command island, flight and science zoning, and the approved aft corridor entrance. The `.glb` bytes are embedded in the single offline-capable `index.html` file, which decodes the glTF 2.0 mesh positions, vertex colours and triangle indices and renders them through WebGL 1. No internet, runtime CDN or extra app is needed to view a local saved copy.

Room identity: `AST-D01-BRIDGE` (Deck 1). The approved only explicit topology edge is `AST-D01-HUB-C` ↔ `AST-D01-BRIDGE`; decorative hatches are not navigable destinations. This viewer does not read or change campaign state, role, access, story clock or PADD data.

Controls: **WASD / arrows** to move, **drag** to look, **Shift** faster, **R** reset; station buttons for aft, command, flight, science and forward view. Coarse-pointer touch devices show a left-hand virtual joystick and drag-to-look.

The self-contained page is intentionally independent of `/3d/`, `/3d-preview/`, `/3d-preview-v3/`, `/3d-preview-v4/`, and the experimental splat PR. The old approved scenes are not modified or deleted.

## Verification gates

- Decode the embedded `.glb` and confirm `117` scene mesh nodes, glTF 2.0, original room markers and geometry within the 15.1 × 13.1 m V3 reference envelope.
- Parse JavaScript and verify no external scripts or network imports.
- In actual software-WebGL Chromium, confirm the 3D scene initializes and capture desktop aft/command/flight plus mobile screenshots.
- Exercise W-key movement and station buttons. A green build or nonblank HTML is not on its own proof of 3D rendering.
- Keep screenshot and links explicitly marked as **layout study**, not a finished realistic Gaussian scene.