# USS Asteria — first full-bridge hero-chair integration: review record

Status: **isolated experimental browser candidate, not a production release or photorealistic completion**.

## Exact preservation

The V3 HTML source Git blob `74a154ae62bccb0c16d03c2ecf791a64ab19ce81` remains unchanged. The source extractor's opt-in instrumentation captured the original draw-call boundaries without spatial guessing:

- Total original V3 bridge: **106,988 triangles**
- Seat/pedestal first face: **14,404**
- Seat/pedestal end-exclusive face: **30,676**
- Old chair faces removed from the candidate only: **16,272**
- Remaining original-bridge faces: **90,716**
- Independent Blender chair: **26,908** triangles (47 exported geometry objects)
- Total expected candidate scene: **117,624** triangles before optional helper contact-shadow planes

The original game-room ID remains `AST-D01-BRIDGE`, with no modification to campaign state, player PADD, topology or the movement/collision routine. The normal V5 asset exporter keeps its prior output unless `ASTERIA_V5_EXCLUDE_CAPTAIN_CHAIR=1` is explicitly supplied. That switch is mutually exclusive with repairing the original chair's winding, since the original chair is removed here.

## Reproducible independent output

Build target is an isolated review route `_site/3d-preview-v5-chair/`. This path is **not deployed or guaranteed externally available**.

The builder starts from the exact V3 source, removes the measured chair span, exports the rest as GLB and loads the previously checked Blender chair GLB with its CC0 scanned-fabric maps. Both assets are same-origin; no asset CDN or Poly Haven call occurs during browser playback. A separate camera named `chairReview` is for screenshot QA only, not a new campaign location or station.

## Real browser review evidence

GitHub Actions run `42445854125` successfully built the scene and rendered actual desktop and phone-sized Chromium/WebGL screenshots. They show:

- Aft access: the new hero chair occupies the correct command dais region with no obvious duplicated old chair.
- Front-facing inspection: physical armrests, individual keys and real fabric material display in-context, but the broad chair upholstery surfaces still look rigid and visibly computer-generated.
- Command-view camera: its forward scene remained visually unchanged in the central region, as expected, because the captain's chair is behind this viewpoint.
- 390 × 844 mobile-sized screenshot: the scene and navigation controls rendered; physical iPhone usability and GPU FPS remain untested.

The first browser QA workflow ended **red**, due to an over-broad whole-image threshold: the aft image difference averaged only about 0.989 over all 1280 × 800 pixels even though the chair changed visibly. A focused chair region (x 450–830, y 240–680) differs by about 5.09 per RGB channel; the central command scene region (x 400–900, y 150–650) did not differ. This observation supports replacing the test, not changing the chair geometry.

A second CI run now evaluates the focused chair region, unchanged command region and actual WASD/touch interaction. Its result must be checked before declaring browser QA success.

## Visual acceptance

**Not yet accepted for release.** The new 3D chair is materially richer than the V3 flat shell but not a realistic photographed furniture asset. The command bridge as a whole retains procedural walls, sparse set details and approximate lighting. One isolated chair replacement does not solve room photorealism.

No standalone public link or ChatGPT attachment is promised. Earlier links and images were repeatedly inaccessible in the user's UI. All results remain in the repository/workflow until a separately accessible preview is verified.
