# Asteria chair stitching A/B — rejected

Date: 2026-11-06. Recorded from **actual matched Blender/Cycles images**, not inferred from code.

Source: original V3 geometry (`74a154ae62bccb0c16d03c2ecf791a64ab19ce81`) imported via V5 GLB. Headless render [CI run 42300057139](https://github.com/JeremyHennessy/TrekMUD/actions/runs/42300057139), artifact `asteria-blender-cycles-stage-01`.

## Observation and decision

- Both baseline and overlay rendered at the same chair-front camera, 960×600, 24 samples, unchanged lighting and unchanged V3 base geometry. CI reported success and a nonzero image difference.
- The large front-facing seat/back panel appears nearly black in **both** renders. Do not assume this is the actual upholstery material until ray/asset inspection identifies the first wrong layer.
- Added stitch lines remain conspicuous and appear too far above the chair face rather than integrated into fabric. Measured image difference covers less than 1% of pixels and does not constitute visual improvement.
- **Decision: REJECT** this stitched overlay. It was removed from the Blender script, workflow and source branch. No V1–V5 public route or game files were modified.

## Focused next diagnostic

Trace the centre and nearby pixels of the dark chair panel back through the Blender ray-hit material, imported glTF material group, normals and V3 source material ID. Do not solve by arbitrarily brightening the entire scene or changing the original chair geometry. Keep the front camera as a read-only inspection aid. Any material fix must be separately tested on the same view and against unchanged bridge viewpoints.
