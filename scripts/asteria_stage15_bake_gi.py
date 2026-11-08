#!/usr/bin/env python3
"""Stage15 opt-in real Cycles DIFFUSE / INDIRECT-only, multi-bounce lightmaps.

Loads the exact Stage12 .blend after Stage12 GLB export. DOES NOT change
geometry, PBR, UV, exported GLBs, old routes, game or controls. Uses its actual
wall and ceiling UV1 receiver sheets, original studio light rig and a clearly
labelled approximate floor reflector. These are experimental lighting samples,
not an assertion of full furnished-bridge or full-ship GI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

WALL = "Architecture / 112 source-fit interior acoustic wall AO receivers"
ROOF = "Architecture / exact 96 stepped acoustic ceiling radial sectors"
UV = "AST_BAKED_ENVELOPE_UV"


def options():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--size", type=int, default=1024)
    p.add_argument("--samples", type=int, default=24)
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def bake_receiver(obj, name, output, size, samples, bounces):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.diffuse_bounces = bounces
    scene.cycles.max_bounces = max(5, bounces + 2)
    scene.render.bake.use_clear = True
    scene.render.bake.margin = 4
    scene.render.bake.use_pass_color = False
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = True
    scene.render.bake.target = "IMAGE_TEXTURES"

    mat = obj.data.materials[0]
    assert mat and mat.use_nodes, name
    assert obj.data.uv_layers.get(UV), name
    image = bpy.data.images.new(
        f"STAGE15_ACTUAL_CYCLES_DIFFUSE_INDIRECT_{name.upper()}_{bounces}BOUNCE",
        width=size, height=size, alpha=False, float_buffer=False)
    image.generated_color = (0., 0., 0., 1.)
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.label = f"QA baked DIFFUSE INDIRECT {bounces} diffuse bounce(s)"
    tex.image = image
    for node in mat.node_tree.nodes:
        node.select = False
    tex.select = True
    mat.node_tree.nodes.active = tex
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    previous_uv = obj.data.uv_layers.active_index
    obj.data.uv_layers.active_index = list(obj.data.uv_layers).index(obj.data.uv_layers[UV])
    try:
        bpy.ops.object.bake(type="DIFFUSE")
        output.parent.mkdir(parents=True, exist_ok=True)
        image.filepath_raw = str(output.resolve())
        image.file_format = "PNG"
        image.save()
    finally:
        obj.data.uv_layers.active_index = previous_uv
        mat.node_tree.nodes.remove(tex)
        bpy.ops.object.select_all(action="DESELECT")
    assert output.is_file() and output.stat().st_size > 2000, output
    return {
        "file": output.name,
        "sizePixels": size,
        "samples": samples,
        "diffuseBounces": bounces,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "bytes": output.stat().st_size,
        "uvLayer": UV,
        "receiverTriangles": len(obj.data.polygons),
        "bakeType": "DIFFUSE",
        "passColor": False,
        "passDirect": False,
        "passIndirect": True,
    }


def main():
    a = options()
    assert 256 <= a.size <= 2048 and 8 <= a.samples <= 128
    scene = bpy.context.scene
    assert scene.render.engine == "CYCLES", "Stage12 saved scene must use Cycles"
    # Blender limits object datablock names to 63 bytes; the original wall
    # receiver name is truncated when the frozen Stage12 .blend is saved.
    # Match its fixed authored prefix AND its exact 224 original faces/UV1.
    wall_matches = [obj for obj in bpy.data.objects
                    if obj.type == "MESH" and obj.name.startswith(WALL[:48])
                    and len(obj.data.polygons) == 224 and obj.data.uv_layers.get(UV)]
    assert len(wall_matches) == 1, [(o.name,len(o.data.polygons)) for o in wall_matches]
    receivers = {"wall": wall_matches[0], "ceiling": bpy.data.objects.get(ROOF)}
    assert all(receivers.values()), receivers
    assert len(receivers["wall"].data.polygons) == 224
    assert len(receivers["ceiling"].data.polygons) == 576
    mesh_count = sum(obj.type == "MESH" for obj in scene.objects)
    scene.cycles.use_denoising = False
    a.out.mkdir(parents=True, exist_ok=True)
    record = {}
    for name, ob in receivers.items():
        uv = ob.data.uv_layers.get(UV)
        coords = [tuple(uv.data[li].uv) for face in ob.data.polygons for li in face.loop_indices]
        assert len(coords) == len(ob.data.polygons) * 3
        assert all(-.0001 <= u <= 1.0001 and -.0001 <= v <= 1.0001 for u, v in coords), name
        path = a.out / f"asteria-stage15-{name}-indirect.png"
        record[name] = bake_receiver(ob, name, path, a.size, a.samples, 3)
    # Independent resolution-limited ablation: a 1-bounce sample on exactly
    # the same receiver and UV island with the same physical Cycles scene.
    # Both outputs are retained; do NOT conflate noise with multi-bounce gain.
    one = bake_receiver(
        receivers["wall"], "wall-1bounce-control",
        a.out / "asteria-stage15-wall-1bounce-control.png", 256, 12, 1)
    three = bake_receiver(
        receivers["wall"], "wall-3bounce-probe",
        a.out / "asteria-stage15-wall-3bounce-probe.png", 256, 12, 3)
    proof = {
        "id": "ASTERIA_STAGE15_REAL_CYCLES_DIFFUSE_INDIRECT_ONLY",
        "scene": "pinned Stage12 Cycles architectural studio",
        "caveat": "The offline scene contains the architecture and approximate studio floor, not complete V3 furnishings.",
        "renderer": scene.render.engine,
        "geometryMeshesInBakeScene": mesh_count,
        "materialPBRPreserved": True,
        "generatedGeometry": False,
        "GISettings": {
            "diffuseBounces": 3, "colorPass": False,
            "directPass": False, "indirectPass": True,
            "explicitEmissiveOrFakeLightOverlay": False,
        },
        "targets": record,
        "ablation": {"oneBounce": one, "threeBounces": three},
        "noPhysicalIphoneVerification": True,
        "notPhotorealismOrArtApproved": True,
    }
    (a.out / "stage15-gi-provenance.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print("STAGE15_REAL_MULTIBOUNCE_GI_BAKE", json.dumps(proof), flush=True)


if __name__ == "__main__":
    main()
