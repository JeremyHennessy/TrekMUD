# USS Asteria — Deck 01 Main Bridge — isolated 3D v3 study

This path (`/3d-preview-v3/`) is an original starship bridge interior for the TrekMUD player ship **USS Asteria, NCC-63542**, Nebula-class, 2372. **It does not reproduce Enterprise-D's bridge.** The TNG-era practical-set visual language is an inspiration only.

## Immutable context

- Starting v1 bridge: `main@1bec688cc57c7cea6c2954460e7b35e7aa426574` / route `/3d/`.
- v2 visual prototype: `main@fe94ca1deb5b8b36b7cedd304c7a0aa8830e4863` / route `/3d-preview/`.
- Source game room: `AST-D01-BRIDGE`, Deck 1, restricted. The only approved explicit neighbor is `AST-D01-HUB-C` via a restricted edge. Side hatches are decorative, not in-game portals.
- This walkable visual model is separate from the MUD and **never changes campaign time, player position, access status or state**.

## Pass 03: hero-set geometry

- Uses a new `hero-v3.js` library of authored, continuously sampled surfaces with smoothly interpolated normals for chairs, command dais, both command pylons and the continuous swept flight island.
- Captain's chair: true curved double-wall upholstered backrest, seat pan and sculpted armrests instead of layered rectangular boxes; padded seams, forged swivel base and independent controls.
- Flight stations: re-profiled one-piece desk shell preserving original monitor UV placement.
- Lighting: physical inset ceiling diffuser housings and trim rather than isolated emissive patches.
- Uses existing `furniture.js` as a geometry fallback, `set-details.js` for nonhero details, and the independent WebGL renderer in `index.html`.
- Movement, rendering entry points, location ID and control affordances intentionally match v2.

### Verification and quality gates

`tests/asteria-3d-v3.test.cjs` checks stable room ID, v1/v2 isolation, identical collision and movement code, JS parsing and finite hero geometry.

GitHub PR validation runs the player PADD and campaign safety checks, opens the v3 page in software-WebGL Chromium, then captures 1440×900 views from **aft**, **command**, and **flight** positions. Visual approval requires reviewing these actual renders, not only successful code tests.

**Not yet photorealistic.** This stage improves authored silhouettes and surface normals. Real-time shadows, high-resolution authored PBR material textures, baked indirect illumination, and physical-device performance are separate follow-up gates. Do not merge into `/3d/` or `/3d-preview/` based only on code passing.
