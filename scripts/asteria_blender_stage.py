#!/usr/bin/env python3
"""Build a non-destructive Blender/Cycles Asteria realism reference scene.

Run through Blender's bundled Python, not ordinary CPython:
blender -b -t 8 --python scripts/asteria_blender_stage.py -- \
  --glb _site/3d-preview-v5/models/asteria-v3-restored-pbr.glb \
  --out _blender_asteria --samples 96 --view command

This file does not rewrite the source GLB, browser route, collision, or game state.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOM_ID = "AST-D01-BRIDGE"
SOURCE_V3_BLOB = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
# Camera coordinates are deliberately taken from the V5 scene, not re-imagined.
VIEWS = {
    "aft": (-1.23, 4.80, .44),
    "command": (-2.32, 2.15, .22),
    "flight": (0.0, -1.32, 0.0),
    "science": (-3.70, 2.76, 2.8),
}
EYE_Y = 1.67
# New render-only close-up: looking toward the original command chair from forward.
# It does not add or alter any in-game camera waypoint.
DETAIL_VIEWS = {"chair": (0.0, -0.85, math.pi)}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--glb", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--view", choices=[*VIEWS, *DETAIL_VIEWS, "all"], default="command")
    p.add_argument("--resolution", nargs=2, type=int, default=(1280, 800))
    p.add_argument("--no-render", action="store_true")
    # Blender passes its own flags before '--'.
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def world_position(x, y, z):
    """glTF Y-up (x,y,z) -> Blender Z-up (x,-z,y)."""
    return Vector((x, -z, y))


def make_area(name, position, target, power, color, size, size_y=None):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = power
    data.color = color
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size if size_y is None else size_y
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = world_position(*position)
    direction = world_position(*target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


def make_camera(name, x, z, yaw):
    camera_data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, camera_data)
    bpy.context.collection.objects.link(obj)
    obj.location = world_position(x, EYE_Y, z)
    # Original V3 forward direction at yaw=0 is world -Z in glTF coordinates.
    aim = world_position(x + math.sin(yaw) * 3, EYE_Y - .14, z - math.cos(yaw) * 3)
    obj.rotation_euler = (aim - obj.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "PERSP"
    camera_data.lens = 48 if name.endswith("chair") else 32
    camera_data.sensor_width = 36
    camera_data.clip_start = .05
    camera_data.clip_end = 160
    return obj


def imported_mesh_statistics(imported):
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("No imported scene meshes. Refusing to save an empty stage.")
    count = sum(len(o.data.polygons) for o in meshes)
    # V5's GLB has exactly the V3 face count, separated into material groups.
    if count != 106988:
        raise RuntimeError(f"Incorrect V3 geometry: {count} triangles, expected 106988")
    return meshes, count


def configure_scene(scene, samples, resolution):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    # The distro's Blender/Cycles package may lack OpenImageDenoiser entirely.
    # Avoid making reference rendering depend on an optional binary feature.
    scene.cycles.use_denoising = False
    for view_layer in scene.view_layers:
        if hasattr(view_layer, "cycles"):
            view_layer.cycles.use_denoising = False
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if hasattr(scene, "view_settings"):
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = bpy.data.worlds.new("Asteria soft ambient studio")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.14, .17, .21, 1)
    background.inputs["Strength"].default_value = .24
    scene.render.image_settings.color_mode = "RGBA"


def main():
    args = parse_args()
    if not args.glb.is_file():
        raise FileNotFoundError(f"Build the V5 GLB first: {args.glb}")
    if args.samples < 8 or min(args.resolution) < 64:
        raise ValueError("Samples/resolution below sanity threshold")
    args.out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
    imported = list(bpy.context.scene.objects)
    meshes, triangles = imported_mesh_statistics(imported)
    scene = bpy.context.scene
    configure_scene(scene, args.samples, args.resolution)

    # Large, soft practical-set lights; Cycles calculates real indirect bounce.
    # Lights are reference-render helpers only, not baked/browser runtime lights.
    make_area("Warm ceiling softbox", (-2.9, 4.20, 1.05),
              (0, .9, 1.05), 720, (1.0, .79, .66), 5.5, 3.2)
    make_area("Command key", (-4.55, 3.95, 1.0),
              (0, .9, .8), 350, (1.0, .86, .76), 2.8, 1.6)
    make_area("Flight gallery cool bounce", (4.9, 3.65, -3.1),
              (0, 1.15, -1.2), 260, (.65, .80, 1.0), 3.2, 2.0)
    make_area("Aft cove fill", (.15, 3.7, 4.4),
              (0, 1.2, 2.0), 220, (1.0, .78, .65), 3.4, 1.3)

    cameras = {name: make_camera("Asteria / " + name, *pose)
               for name, pose in {**VIEWS, **DETAIL_VIEWS}.items()}
    scene.camera = cameras["command"]
    blend_path = args.out / "asteria-bridge-realism-stage.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path.resolve()))
    views = list(VIEWS) if args.view == "all" else [args.view]
    if not args.no_render:
        for name in views:
            scene.camera = cameras[name]
            scene.render.filepath = str((args.out / f"asteria-cycles-{name}.png").resolve())
            bpy.ops.render.render(write_still=True)
    manifest = {
        "roomId": ROOM_ID,
        "sourceV3Blob": SOURCE_V3_BLOB,
        "sourceGlb": str(args.glb),
        "triangles": triangles,
        "importedMeshObjects": len(meshes),
        "engine": "CYCLES",
        "samples": args.samples,
        "renderedViews": [] if args.no_render else views,
        "note": "Lighting/material review only. No visual approval or baked browser lightmaps implied.",
    }
    (args.out / "stage-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
