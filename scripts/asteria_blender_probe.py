#!/usr/bin/env python3
"""Read-only ray and material probe for the original Asteria chair-front render.

Load the saved Blender master first:
blender -b path/to/asteria-bridge-realism-stage.blend --python scripts/asteria_blender_probe.py -- --out path/to/chair-probe.json

Do not alter source meshes, materials, light rig or scene camera in this tool.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])


def material_details(mat):
    if not mat:
        return None
    props={"name":mat.name,"use_nodes":bool(mat.use_nodes)}
    if mat.use_nodes:
        shaders=[n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED"]
        if shaders:
            node=shaders[0]
            for socket in ("Base Color","Roughness","Metallic"):
                if socket in node.inputs:
                    value=node.inputs[socket].default_value
                    props[socket]=list(value) if hasattr(value,"__len__") else float(value)
                    props[socket+" source"]=[
                        link.from_node.name for link in mat.node_tree.links if link.to_socket==node.inputs[socket]
                    ]
    return props


def main():
    output=args().out
    scene=bpy.context.scene
    cam=bpy.data.objects.get("Asteria / chair")
    if cam is None or cam.type!="CAMERA":
        raise RuntimeError("Expected original Blender chair diagnostic camera is missing")
    frame=cam.data.view_frame(scene=scene)
    minx,maxx=min(p.x for p in frame),max(p.x for p in frame)
    miny,maxy=min(p.y for p in frame),max(p.y for p in frame)
    z=sum(p.z for p in frame)/len(frame)
    transform=cam.matrix_world.to_quaternion()
    origin=cam.matrix_world.translation
    graph=bpy.context.evaluated_depsgraph_get()
    data=[]
    # A 7×7 coverage probe plus the exact optical centre.
    coords=[-.30,-.20,-.10,0.,.10,.20,.30]
    for y in reversed(coords):
        for x in coords:
            direction=transform@Vector((x*(maxx-minx)*.5,y*(maxy-miny)*.5,z)).normalized()
            hit,location,normal,face_index,obj,matrix=scene.ray_cast(graph,origin,direction,distance=100.)
            result={"u":x,"v":y,"hit":bool(hit)}
            if hit:
                idx=obj.data.polygons[face_index].material_index if obj.type=="MESH" else 0
                mat=obj.material_slots[idx].material if obj.material_slots and idx<len(obj.material_slots) else None
                result.update({
                    "object":obj.name,
                    "material":mat.name if mat else None,
                    "polygonIndex":face_index,
                    "normalCameraDot":round(float((-direction).dot(normal)),4),
                    "distance":round((location-origin).length,4),
                })
            data.append(result)
    counts=Counter((s.get("material") or "<none>") for s in data if s.get("hit"))
    mats={m.name:material_details(m) for m in bpy.data.materials}
    report={
       "roomId":"AST-D01-BRIDGE",
       "camera":"Asteria / chair",
       "cameraLocation":list(origin),
       "rayHitMaterialCounts":dict(counts),
       "centreHit":next(s for s in data if s["u"]==0 and s["v"]==0),
       "grid":data,
       "materials":mats,
       "note":"Read-only diagnostic. This does not diagnose pixel color or change any rendering material.",
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("Chair centre ray:",json.dumps(report["centreHit"]))
    print("Material counts:",dict(counts))


if __name__=="__main__":
    main()
