# USS Asteria — layout-guided photographic-splat production brief

**Preparation only. No World Labs generation, API request, export purchase or charge has occurred.**

## Exact technical identity and provenance

- USS Asteria, NCC-63542, original TrekMUD player ship, late-24th-century exploration and science vessel, 2372.
- Visual-only source location `AST-D01-BRIDGE` (main bridge, Deck 1, restricted); approved graph connection only to `AST-D01-HUB-C` (aft central corridor hub).
- Approved V1–V4 routes unchanged. Prefer V3 composition over V4's flat architectural panels. Don't replicate or claim exact Star Trek: The Next Generation Enterprise-D television set design.
- Conditioning blockout: `asteria-bridge-chisel-blockout.glb` generated from `generate_chisel_blockout.py`. It contains 117 coarse, named geometry elements with a 15.1 m × 13.1 m elliptical envelope, ~3.9 m maximum height, one command island and central chair, curved forward flight station, two raised science wings, aft corridor opening, panoramic forward viewscreen, sealed side hatches.
- Exact dimensions are **V3 model coordinates**, not officially documented Nebula-class set measurements.

## Chisel scene guidance (original environment)

> A cinematic, physically plausible original 2372-era deep-space science starship bridge, USS Asteria NCC-63542. Follow the imported 3D layout closely: a warm, oval command deck with raised central commander platform and one sculpted plum-grey upholstered captain chair, two compact command control pylons, a shallow continuous curved forward flight console with two operators' seats, two raised aft science-analysis wings, one broad panoramic forward viewscreen looking across a deep-space research docking complex, a central aft command corridor doorway, sealed port and starboard side hatches. Preserve believable crew-scale clearances, panel and furniture dimensions, precise wall layout and visible architectural continuity. Materials: textured warm ivory molded acoustic/composite shells with deep inset structural ribs and detailed wall joints, dark blue-grey carpet with tiny woven fibers, satin pewter structural railings, bronze-toned edge fittings, subtle leather/suede fabric upholstery with realistic padding and seam stitching, recessed dark smoked-glass instrument surfaces with restrained teal, amber and pale lavender displays. Physically believable practical light sources in recessed ceiling coves, indirect ceiling bounce, dark recesses, natural contact shadows and subtle surface wear, more restrained than a theatrical science-fiction theme park. Professionally constructed multi-camera television set, human-eye-height interior photography. Geometry must remain continuous and convincingly built at all walking angles. No people, copyrighted insignia, copied Enterprise-D chair or bridge plan, exaggerated neon tubes, cutaway rooms, floating geometry, or text overlays.

## Asset and approval checks

1. Use existing GLB as a **coarse layout guide**, not as the final visual mesh. If Chisel cannot preserve its curved wall or room topology, reject that generation instead of changing the approved ship map to match it.
2. Capture identical camera views near `aft (-1.38,1.69,4.91, yaw .40)`, `command (-2.48,1.69,2.60, yaw .20)`, `flight (0,1.69,-1.56,yaw 0)`, `science (-4.75,1.69,2.10, yaw 2.63)` plus seat close-ups. Avoid comparing matched camera names if generated coordinate systems change; solve world alignment first.
3. Reject output if window/signage appears painted in 2D, doors relocate, furniture shifts into walking routes, station surfaces blur under proximity, collision proxy is missing, prominent floaters remain, or splat artifacts expose invisible voids when approached.
4. Require a local export of the splat (.spz/.ply) and separate collider (.glb) before browser integration. Confirm rights and usage terms. Never point public Asteria app at a third-party hosted world or call an API at runtime.
5. Keep the **approved existing collider** authoritative unless specifically authorized to alter the room topology. Visual scene may be splatted; interactive consoles and legible textual controls should remain real 3D objects and live surfaces.
6. Optimize to `.sog` using SuperSplat/`splat-transform` only after high-quality source approval. Measure desktop and mobile FPS, file size, GPU memory, load time, and screenshot consistency. A faster or more photorealistic still does not mean the walkable scene is successful.

## Access/cost boundary

World Labs Marble currently advertises free world generations, but **splat export and low-resolution collider export require Standard or better**. Do not spend or subscribe without separate user authorization. Chisel is an experimental editing feature and detailed layout adherence is not guaranteed. The asset-export/visual review steps are conditional on authorized account access.

Official sources:
- https://www.worldlabs.ai/blog/marble-world-model
- https://marble.worldlabs.ai/pricing
- https://github.com/sparkjsdev/spark
- https://developer.playcanvas.com/user-manual/gaussian-splatting/editing/supersplat/