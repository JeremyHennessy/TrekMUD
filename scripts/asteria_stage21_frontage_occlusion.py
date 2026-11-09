#!/usr/bin/env python3
"""Read-only Stage21 source-face sightline investigation; NOT a rendered art trial.

Trace exact untouched V3 triangles (minus the five already independently
measured replacement spans) at the real V5 studio camera projection. This
identifies retained-source faces in primary views, not the later GLB overlays.
The heatmaps are RAYCAST DIAGNOSTICS, not Chromium screenshots or art proof.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

FROZEN = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
N_FACES = 106988
VIEWS = {
    "aft": (-1.23, 4.80, .44, -.14),
    "command": (-2.32, 2.15, .22, -.14),
    "science": (-3.70, 2.76, 2.8, -.14),
    "envelopeWall": (-2.60, -.50, -1.18, -.14),
}
# These are the genuine browser camera positions and pitch from the original
# review harness. Keep the 65-degree perspective and 1280:800 aspect pinned.
FOV_Y = math.radians(65.)
ASPECT = 1280. / 800.
GRID_W, GRID_H = 28, 18


def ranges_from_source(directory):
    chair = json.loads((directory / "captain-chair-source-span.json").read_text())
    command = json.loads((directory / "command-section-source-spans.json").read_text())
    triple = json.loads((directory / "three-rib-bays-source-spans.json").read_text())
    envelope = json.loads((directory / "envelope-source-spans.json").read_text())
    for payload in (chair, command, triple, envelope):
        assert payload["sourceV3Blob"] == FROZEN
    spans = [
        {"name": "originalCaptainSeat", "start": chair["firstFaceIncluded"],
         "end": chair["lastFaceExcluded"]},
        *command["ranges"],
        *triple["ranges"],
        *envelope["ranges"],
    ]
    assert len(spans) == 1 + 3 + 3 + 2
    keep = np.ones(N_FACES, dtype=np.bool_)
    for row in spans:
        start, end = int(row["start"]), int(row["end"])
        assert 0 <= start < end <= N_FACES
        assert keep[start:end].all(), ("Overlapping frozen source exclusions", row)
        keep[start:end] = False
    assert int(keep.sum()) == 81050, ("Stage12 retained V3 faces changed", int(keep.sum()))
    assert sum(int(x["end"]) - int(x["start"]) for x in spans) == 25938
    return keep, spans


def ray_direction(u, v, yaw, pitch):
    # Three.js PerspectiveCamera(65, aspect=1.6), rotation YXZ with
    # camera.rotation.set(pitch, -yaw, 0). Pixel centres in normalized UV.
    x = (2. * u - 1.) * ASPECT * math.tan(FOV_Y / 2.)
    y = (1. - 2. * v) * math.tan(FOV_Y / 2.)
    z = -1.
    y1 = y * math.cos(pitch) - z * math.sin(pitch)
    z1 = y * math.sin(pitch) + z * math.cos(pitch)
    x2 = x * math.cos(yaw) - z1 * math.sin(yaw)
    z2 = x * math.sin(yaw) + z1 * math.cos(yaw)
    direction = np.array([x2, y1, z2], dtype=np.float32)
    return direction / np.linalg.norm(direction)


def trace_rays(vertices, face_ids, origin, dirs):
    """Double-sided Moller-Trumbore, one CPU source-triangle test per ray."""
    a = vertices[:, 0]
    edge1 = vertices[:, 1] - a
    edge2 = vertices[:, 2] - a
    s = origin - a
    qvec = np.cross(s, edge1)
    t_numer = np.einsum("ij,ij->i", edge2, qvec)
    records = []
    for d in dirs:
        pvec = np.cross(np.broadcast_to(d, edge2.shape), edge2)
        det = np.einsum("ij,ij->i", edge1, pvec)
        good = np.abs(det) > 1.e-7
        inv = np.divide(1., det, out=np.zeros_like(det), where=good)
        u = np.einsum("ij,ij->i", s, pvec) * inv
        v = (qvec @ d) * inv
        t = t_numer * inv
        valid = good & (u >= -1.e-5) & (v >= -1.e-5) & (u + v <= 1.00001) & (t > .07)
        nearest = np.where(valid, t, np.inf)
        idx = int(np.argmin(nearest))
        if not np.isfinite(nearest[idx]):
            records.append(None)
        else:
            records.append({"sourceFace": int(face_ids[idx]),
                            "rayDistanceMeters": round(float(nearest[idx]), 4)})
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("_v5_mesh_capture"))
    ap.add_argument("--out", type=Path, default=Path("_stage21_occlusion"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    keep, removed = ranges_from_source(args.source)
    hatch_proof = json.loads((args.source / "side-hatches-source-spans.json").read_text())
    assert hatch_proof["sourceV3Blob"] == FROZEN
    assert hatch_proof["originalV3FilesUnmodified"] is True
    assert hatch_proof["sourceAuthoringFunction"] == "sideHatch"
    port, starboard = hatch_proof["ranges"]
    assert port["name"] == "port" and starboard["name"] == "starboard"
    assert 0 < port["start"] < port["end"] == starboard["start"] < starboard["end"] < N_FACES
    # Exact original source callback proves both dominant near-wall facets
    # belong to the authored port-hatch call, not the overlay material.
    assert port["start"] <= 92848 < port["end"]
    assert port["start"] <= 92849 < port["end"]
    assert bool(keep[92848]) and bool(keep[92849])
    original = np.load(args.source / "positions.npy").astype(np.float32).reshape(-1, 3, 3)
    assert len(original) == N_FACES
    retained = original[keep]
    ids = np.flatnonzero(keep)
    mats = np.load(args.source / "materials.npy").reshape(-1)
    if len(mats) == N_FACES * 3:
        mats = mats.reshape(-1, 3)[:, 0]
    assert len(mats) == N_FACES, ("Original V3 material indices changed", len(mats))
    assert np.isfinite(retained).all()
    # Independent positive control: a face directly in front of the camera
    # must be hit; a nearer coplanar face wins; back faces still hit.
    triangles = np.array([[[-1,-1,-4],[1,-1,-4],[0,1,-4]],
                          [[-1,-1,-2],[1,-1,-2],[0,1,-2]]], dtype=np.float32)
    proof = trace_rays(triangles, np.array([100,101]),
                       np.array([0,0,0], dtype=np.float32),
                       [np.array([0,0,-1], dtype=np.float32)])
    assert proof[0]["sourceFace"] == 101 and abs(proof[0]["rayDistanceMeters"]-2)<1.e-5
    report = {
        "id": "ASTERIA_STAGE21_FROZEN_ORIGINAL_SOURCE_FACE_VISIBILITY",
        "originalV3SourceBlob": FROZEN,
        "stage12Baseline": "e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b",
        "retainedOriginalSourceFaces": int(keep.sum()),
        "preciseExcludedSourceRanges": removed,
        "exactOriginalSideHatchAuthoringRanges": hatch_proof,
        "originalRoomCollisionAndUIChanged": False,
        "pixelGrid": [GRID_W, GRID_H],
        "cameraProjection": {"verticalFovDegrees": 65, "aspect": ASPECT,
                             "cameraEyeY": 1.67, "pitchRadians": -.14},
        "notActualChromiumOrFinalStage20MeshRaycast": True,
        "doesNotIncludeReplacementChairCommandThreeBayOrEnvelopeGLBs": True,
        "views": {},
    }
    for name, (cx, cz, yaw, pitch) in VIEWS.items():
        origin = np.array([cx, 1.67, cz], dtype=np.float32)
        rays = [ray_direction((x+.5)/GRID_W, (y+.5)/GRID_H, yaw, pitch)
                for y in range(GRID_H) for x in range(GRID_W)]
        records = trace_rays(retained, ids, origin, rays)
        hits = [r for r in records if r]
        material_counts = Counter(str(int(round(float(mats[r["sourceFace"]]))))
                                  for r in hits)
        top_faces = Counter(r["sourceFace"] for r in hits)
        details = []
        for face, count in top_faces.most_common(18):
            vertex = original[face]
            details.append({
                "sourceFace": face,
                "sampledPixels": count,
                "originalMaterialId": int(round(float(mats[face]))),
                "triangleXYZMeters": np.round(vertex, 4).tolist(),
                "centroidXYZMeters": np.round(vertex.mean(axis=0), 4).tolist(),
            })
        report["views"][name] = {
            "camera": {"x": cx, "z": cz, "yaw": yaw, "pitch": pitch},
            "sourceSampleCount": len(records),
            "retainedSourceVisibleHits": len(hits),
            "sourceNoHitCount": len(records)-len(hits),
            "portHatchSourceVisibleSamples": sum(
                port["start"] <= r["sourceFace"] < port["end"] for r in hits),
            "starboardHatchSourceVisibleSamples": sum(
                starboard["start"] <= r["sourceFace"] < starboard["end"] for r in hits),
            "sourceMaterialSampleCounts": dict(material_counts.most_common()),
            "largestSampledSourceTriangles": details,
            "centerSample": records[(GRID_H//2)*GRID_W+(GRID_W//2)],
            "hits": records,
        }
        # Pixel-art heatmap encodes ray-hit material index ONLY.
        # It must never be confused with a real browser/Cycles screenshot.
        palette = [(28, 29, 40), (133, 101, 96), (204, 186, 159),
                   (111, 122, 133), (87, 116, 141), (161, 128, 92),
                   (60, 67, 93), (87, 104, 83), (200, 165, 107),
                   (180, 143, 171), (126, 158, 161)]
        pixels = []
        for r in records:
            pixels.append(palette[int(round(float(mats[r["sourceFace"]]))) % len(palette)]
                          if r else (12, 13, 24))
        im = Image.new("RGB", (GRID_W, GRID_H))
        im.putdata(pixels)
        im.resize((GRID_W*32, GRID_H*32), Image.Resampling.NEAREST).save(
            args.out / ("SOURCE_ONLY_NOT_BROWSER_" + name + ".png"))
        print("SOURCE_RAYCAST_VIEW", name, "hits", len(hits), "by_material",
              json.dumps(dict(material_counts.most_common())), flush=True)
    assert report["views"]["envelopeWall"]["portHatchSourceVisibleSamples"] >= 75, (
        report["views"]["envelopeWall"]["portHatchSourceVisibleSamples"])
    assert report["views"]["aft"]["sourceSampleCount"] == GRID_W * GRID_H
    (args.out / "stage21-source-face-occlusion-report.json").write_text(
        json.dumps(report, indent=2) + "\n")
    assert all(v["retainedSourceVisibleHits"] > 0 for v in report["views"].values())
    print("STAGE21_SOURCE_FACE_VISIBILITY_PROBE_PASS",
          json.dumps({k: v["retainedSourceVisibleHits"]
                      for k,v in report["views"].items()}), flush=True)


if __name__ == "__main__":
    main()
