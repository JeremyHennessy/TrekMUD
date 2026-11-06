# USS Asteria · 3D ship studio
A separate, opt-in, first-person browser walkthrough for the **TrekMUD** original USS Asteria (NCC-63542), a Nebula-class ship in 2372.

## Material and set realism pass 02 (in review)
The accepted starting point is the deployed Room 01 at commit `1bec688cc57c7cea6c2954460e7b35e7aa426574`. Pass 02 changes only the opt-in 3D route and its associated visual tests. The approved PADD interface, campaign status, and world topology are not changed.

- `set-details.js` adds more than 1,000 discrete pieces of physically modelled trim, fixtures, acoustic panels, seams, latches, controls, upholstery and service infrastructure in the existing space. The implementation is deterministic and uses no hidden campaign data.
- A filmic, energy-aware shader distinguishes carpet, painted composite, cast substrate, satin metal, upholstery, smoked instrument glass and internally lit display faces. This is a *physically inspired approximation*, not offline ray tracing or a path-traced physically accurate lighting simulation.
- The browser automatically falls back to the previous material shader if the new fragment program does not compile.
- The GitHub PR checks run static topology/geometry tests and attempt a real software-WebGL rendering smoke with an uploaded screenshot for visual review. Use `?studioCapture=1` on the 3D route to bypass the opening modal for screenshot capture.
- Hardware GPU performance, final light levels, handheld touch interaction and independent user approval remain open quality gates. **Do not call this photorealistic or approved without visual inspection.**

### Remaining realism limits
Accurate cinema-quality geometry will eventually need high-resolution artist-authored or scanned physically based materials, true rounded/chamfered furniture, professionally UV-mapped assets, physically plausible shadows/reflections, and a calibrated photographic reference. This modular pass preserves the fast, dependency-free WebGL foundation and does not claim to deliver those capabilities yet.

## Room 01 — Main Bridge
- Canonical campaign room ID: `AST-D01-BRIDGE` (Deck 1; command; restricted).
- The room is a **TrekMUD-original visual interpretation** inspired by the material, lighting, console and practical-set design language of *The Next Generation*. It is **not** a reproduction of the Enterprise-D or a claim about an on-screen Nebula-class bridge layout.
- Features modelled: elliptical command shell, raised command island, captain's chair and command-data pylons, continuous dual-seat flight island, panoramic forward viewer, science gallery, tactical relay, wall diagnostics, closed side hatches, ceiling coves, procedural set textures, in-world stars and docking structure, collision-limited first-person camera, mini deck plan, and desktop/mobile controls.
- Source topology: `world/asteria/topology.json`. The approved **only** explicit edge touching the bridge is the restricted connection `AST-D01-HUB-C ↔ AST-D01-BRIDGE`. Consequently the aft entrance is an **unopened command corridor access** to the hub. Closed side hatches are scenic, not established traversable connections.
- The entire room is procedural, built with local WebGL 1 code plus one same-origin set-dressing script; no third-party asset CDN, embedded video, outside models, or network permissions are required. A WebGL-capable browser/device **is** required.
- This page is **not an in-game movement command**. Walking here changes no campaign location, access clearance, stardate, or persistent RPG state. Existing player PADD routes and the campaign save remain unchanged.

## Controls
- Desktop: WASD / arrow keys to walk; click-drag to look; Shift for faster movement; R reset to aft access; H toggle HUD.
- Phone/tablet: left thumbpad to walk; drag scene to look; use station buttons to jump to view locations.
- Five station views: aft access, command, flight, science, forward view.

## Release and accuracy gates
- Browser JavaScript syntax and in-browser control flow have been tested; approximately 17,180 modelling triangles are generated, and keyboard movement plus mobile/desktop navigation handlers were exercised.
- Actual **WebGL rendering succeeded under software GPU rendering** in a visible Chromium session on Linux/Xvfb. Screenshots were inspected at both desktop and mobile viewport dimensions; initial lighting and camera issues were corrected. Navigation, station jumps, the intro and the minimap were exercised. This is a **first-pass visual model**, not final photorealistic set quality.
- Performance on a physical iPhone, real GPU framerate, detailed collision geometry and touch ergonomics remain **unverified**. User approval of geometry and presentation is still pending.
- This is Room 01; no additional rooms are claimed to exist. Future room geometry should keep the existing 200 stable public topology IDs and add only authorized room links, preserving existing UI and campaign state.

Open `3d/` under GitHub Pages, or open `index.html` in a modern WebGL browser.
