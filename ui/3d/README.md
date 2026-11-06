# USS Asteria · 3D ship studio
A separate, opt-in, first-person browser walkthrough for the **TrekMUD** original USS Asteria (NCC-63542), a Nebula-class ship in 2372.

## Room 01 — Main Bridge
- Canonical campaign room ID: `AST-D01-BRIDGE` (Deck 1; command; restricted).
- The room is a **TrekMUD-original visual interpretation** inspired by the material, lighting, console and practical-set design language of *The Next Generation*. It is **not** a reproduction of the Enterprise-D or a claim about an on-screen Nebula-class bridge layout.
- Features modelled: elliptical command shell, raised command island, captain's chair and command-data pylons, continuous dual-seat flight island, panoramic forward viewer, science gallery, tactical relay, wall diagnostics, closed side hatches, ceiling coves, procedural set textures, in-world stars and docking structure, collision-limited first-person camera, mini deck plan, and desktop/mobile controls.
- Source topology: `world/asteria/topology.json`. The approved **only** explicit edge touching the bridge is the restricted connection `AST-D01-HUB-C ↔ AST-D01-BRIDGE`. Consequently the aft entrance is an **unopened command corridor access** to the hub. Closed side hatches are scenic, not established traversable connections.
- The entire room is procedural, built with local WebGL 1 code; no asset CDN, embedded video, outside models, or network permissions are required. A WebGL-capable browser/device **is** required.
- This page is **not an in-game movement command**. Walking here changes no campaign location, access clearance, stardate, or persistent RPG state. Existing player PADD routes and the campaign save remain unchanged.

## Controls
- Desktop: WASD / arrow keys to walk; click-drag to look; Shift for faster movement; R reset to aft access; H toggle HUD.
- Phone/tablet: left thumbpad to walk; drag scene to look; use station buttons to jump to view locations.
- Five station views: aft access, command, flight, science, forward view.

## Release and accuracy gates
- Browser JavaScript syntax and in-browser control flow have been tested with a stub WebGL context; approximately 16,000 modelling triangles are generated, and keyboard movement plus mobile/desktop navigation handlers were exercised.
- The test environment **does not expose an actual WebGL context**, so a true hardware-rendered visual screenshot, GPU behavior, touch-device frame pacing, and visual fidelity remain **unverified**. Review on a real WebGL browser before treating appearance as approved.
- This is Room 01; no additional rooms are claimed to exist. Future room geometry should keep the existing 200 stable public topology IDs and add only authorized room links, preserving existing UI and campaign state.

Open `3d/` under GitHub Pages, or open `index.html` in a modern WebGL browser.
