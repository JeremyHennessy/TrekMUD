#!/usr/bin/env python3
"""Isolated original USS Asteria starboard forward wall/ceiling-bay geometry study.

Review-only GLB, .blend and real Cycles stills. The frozen V3 wall and ceiling
are NOT removed. This does not publish a new page or change game/client code.
Physical layout is taken from the V3 ellipse (W=7.55, D=6.55) and ceiling
slope, not a remembered Enterprise set. Only one bay is modelled.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asteria_command_blender as kit

ROOM="AST-D01-BRIDGE"
SOURCE="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
W,D=7.55,6.55
A=2.42
PI=math.pi

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--materials",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--samples",type=int,default=24)
    p.add_argument("--resolution",nargs=2,type=int,default=[900,600])
    p.add_argument("--no-render",action="store_true")
    return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def at(angle, r, y):
    return (W*math.sin(angle)*r, y, D*math.cos(angle)*r)

def tangent(angle):
    x,z=W*math.cos(angle),-D*math.sin(angle)
    n=math.hypot(x,z)
    return x/n,z/n

TX,TZ=tangent(A)
ROT=math.atan2(TZ,TX)

def offset(dx,y,r=.940):
    x,_,z=at(A,r,y)
    return (x+TX*dx,y,z+TZ*dx)

def box(name,dx,y,r,width,height,depth,material,radius=.012):
    return kit.box(name,offset(dx,y,r),(width,height,depth),material,
                   roundover=radius,rotation=ROT)

def line(name,pts,r,material):
    return kit.pipe(name,pts,r,material,segments=3)

def signed_panel(name,left,right,bottom,top,r,material):
    points=[offset(left,bottom,r),offset(right,bottom,r),
            offset(right,top,r),offset(left,top,r)]
    # Tangent cross vertical points outward; the visible face looks inward.
    ob=kit.model(name,points,[(0,2,1),(0,3,2)],material,
                 [(0,0),(1,0),(1,1),(0,1)])
    for poly in ob.data.polygons:poly.use_smooth=False
    return ob

def fastener(name,point,radial,material):
    # Tiny visible screw aligned to the true ellipse normal, not upright
    # cylinders misleadingly floating off a vertical wall.
    origin=Vector(kit.xyz(*point))
    direction=Vector(kit.xyz(*radial))-Vector(kit.xyz(0,0,0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.010,depth=.009,
                                        location=origin)
    ob=kit.put(bpy.context.object);ob.name=name
    ob.rotation_euler=direction.to_track_quat("Z","Y").to_euler()
    ob.data.materials.append(material)
    return ob

def ceiling_y(r):
    return 4.38-(r-.36)/(.985-.36)*.66-.065

def roof_plate(name,lo,hi,inner,outer,material,lower=.0):
    corners=[at(lo,inner,ceiling_y(inner)-lower),
             at(hi,inner,ceiling_y(inner)-lower),
             at(hi,outer,ceiling_y(outer)-lower),
             at(lo,outer,ceiling_y(outer)-lower)]
    ob=kit.model(name,corners,[(0,1,2),(0,2,3)],material,
                 [(0,0),(1,0),(1,1),(0,1)])
    for f in ob.data.polygons:f.use_smooth=False
    return ob

def build(m):
    # All details remain within the starboard forward wall segment where
    # V3 places acoustic bays (a=2.42, away from doors and viewscreen).
    # Surface radius .929-.954 sits inside original .95 decorated wall and
    # outside the V3 blocked() walkable radius sqrt(.845) ~= .919.
    box("Bay / structural deep powder-coated chassis",0,1.94,.954,
        1.44,2.59,.072,m["powder_graphite"],.035)
    box("Bay / reveal-side shadow gasket",0,1.94,.947,
        1.31,2.41,.048,m["console_gasket"],.021)
    box("Bay / formed laminated main panel",0,1.94,.940,
        1.235,2.30,.036,m["powder_ivory"],.039)
    signed_panel("Bay / fine-grain flush acoustic face",-.567,.567,.94,2.94,
                 .934,m["powder_ivory"])
    # Structural cassettes, edge caulking, captured glass-like light channel,
    # separate service-door seam and real, regularly spaced hardware.
    for side in (-1,1):
        dx=side*.624
        box(f"Bay / {side:+d} / satin outer stile",dx,1.94,.936,
            .043,2.34,.036,m["satin_nickel"],.014)
        line(f"Bay / {side:+d} / inset elastomer seal",
             [offset(dx-side*.062,y,.930) for y in (.87,1.48,2.20,2.96)],
             .006,m["console_gasket"])
        for y in (.90,1.51,2.13,2.89):
            point=offset(dx,y,.929)
            fastener(f"Bay / {side:+d} / flush captive fastener {y:.2f}",
                     point,(-math.sin(A),0,-math.cos(A)),m["rose_bronze"])
    # Machined horizontal reveals: restrained, no arbitrary glowing stripes.
    for y in (1.12,2.42):
        line(f"Bay / recessed horizontal gasket {y:.2f}",
             [offset(x,y,.930) for x in (-.54,-.26,.25,.54)],
             .008,m["console_gasket"])
    for k in range(7):
        y=.73+k*.046
        box(f"Bay / low air-exchange vent / slot {k:02d}",
            0,y,.930,.86,.014,.016,m["powder_graphite"],.005)
    # Contoured acoustic/maintenance insets, separated from the wall body.
    for dx in (-.35,0,.35):
        signed_panel(f"Bay / acoustic relief {dx:+.2f}",
            dx-.11,dx+.11,1.55,2.25,.929,m["powder_ivory"])
    box("Bay / physical bottom service rail",0,.63,.944,
        1.31,.10,.10,m["satin_nickel"],.024)
    box("Bay / upper light housing",0,3.025,.937,
        1.25,.088,.078,m["powder_graphite"],.02)
    box("Bay / diffused warm practical diffuser",0,3.035,.934,
        1.13,.018,.027,m["powder_ivory"],.006)
    # Preserve exact V3 wedge ceiling slope (4.38 m at r .36 to 3.72 at
    # r .985). Two formed sloped cast sections, gaskets, light cassette,
    # segmented acoustic infill and physically mounted fasteners.
    lo,hi=A-.105,A+.105
    roof_plate("Ceiling / formed outer shell",lo,hi,.49,.92,
               m["powder_graphite"])
    roof_plate("Ceiling / low-sheen white flush panel",
               lo+.014,hi-.014,.53,.87,m["powder_ivory"],.016)
    for angle in (lo+.012,hi-.012):
        line(f"Ceiling / curved seam at {angle:.3f}",
             [at(angle,r,ceiling_y(r)-.024) for r in (.53,.64,.75,.89)],
             .009,m["satin_nickel"])
    for i in range(5):
        r=.56+i*.060
        roof_plate(f"Ceiling / separate moulded acoustic cassette {i}",
                   lo+.035,hi-.035,r,r+.033,
                   m["powder_ivory"],.032)
    roof_plate("Ceiling / recessed electrical diffuser",
               lo+.030,hi-.030,.89,.913,m["satin_nickel"],.035)
    for i in range(5):
        aa=lo+.026+(hi-lo-.052)*i/4
        p=at(aa,.90,ceiling_y(.90)-.053)
        fastener(f"Ceiling / captured quarter-turn clip {i}",p,
                 (0,-1,0),m["rose_bronze"])

def lights_and_cameras():
    world=bpy.data.worlds.new("BAKE STUDIO neutral indirect enclosure")
    bpy.context.scene.world=world;world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.25,.245,.255,1)
    bg.inputs["Strength"].default_value=.40
    focus=at(A,.940,2.33)
    kit.light("Soft ceiling grazing key",(0.9,4.7,-1.2),focus,680,
              (1,.88,.81),(3.6,2.8))
    kit.light("Aft reflected side softbox",(3.0,3.2,1.4),focus,410,
              (.77,.87,1),(2.6,3.0))
    kit.light("Forward wall wash",(1.3,3.8,-5.6),focus,170,
              (1,.91,.82),(1.7,2.0))
    return {
      "wall":kit.camera("QA / wall bay",(1.40,2.08,-.74),
                        at(A,.940,1.96),48),
      "ceiling":kit.camera("QA / ceiling bay",(1.70,2.60,-.8),
                           at(A,.70,3.94),40),
      "commandSightline":kit.camera("QA / V3 command waypoint",
                                    (-2.32,1.67,2.15),focus,32),
    }

def main():
    a=args()
    if a.samples<8 or min(a.resolution)<128:raise ValueError("Unsafe rendering settings")
    provenance=json.loads((a.materials/"material-provenance.json").read_text())
    assert provenance["id"]=="ASTERIA-COMMAND-PBR-01"
    a.out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    kit.COMMAND=bpy.data.collections.new("USS ASTERIA / STARBOARD WALL BAY / ISOLATED 01")
    bpy.context.scene.collection.children.link(kit.COMMAND)
    styles={"powder_ivory":(.72,.16),"powder_graphite":(.67,.15),
            "satin_nickel":(.38,.67),"rose_bronze":(.43,.56),
            "console_gasket":(.87,0)}
    mats={name:kit.build_material("Asteria / wall bay / "+name,name,*values,a.materials)
          for name,values in styles.items()}
    build(mats)
    cameras=lights_and_cameras()
    sc=bpy.context.scene
    sc.render.engine="CYCLES"
    sc.cycles.samples=a.samples
    sc.cycles.max_bounces=5
    sc.cycles.diffuse_bounces=3
    sc.render.resolution_x=a.resolution[0]
    sc.render.resolution_y=a.resolution[1]
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    sc.view_settings.view_transform="AgX"
    sc.view_settings.look="AgX - Medium High Contrast"
    sc.view_settings.exposure=-.6
    bpy.ops.wm.save_as_mainfile(
        filepath=str((a.out/"asteria-wall-ceiling-bay-candidate.blend").resolve()))
    for curve in [o for o in kit.COMMAND.objects if o.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        curve.select_set(True);bpy.context.view_layer.objects.active=curve
        bpy.ops.object.convert(target="MESH")
    objects=[o for o in kit.COMMAND.objects if o.type=="MESH"]
    assert len(objects)>35,len(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    properties=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    selection="use_selection" if "use_selection" in properties else "export_selected"
    bpy.ops.export_scene.gltf(
        filepath=str((a.out/"asteria-wall-ceiling-bay-candidate.glb").resolve()),
        export_format="GLB",**{selection:True})
    if not a.no_render:
        for key,camera in cameras.items():
            sc.camera=camera
            sc.render.filepath=str((a.out/f"asteria-bay-{key}.png").resolve())
            bpy.ops.render.render(write_still=True)
    report={
        "id":"ASTERIA_WALL_CEILING_BAY_01",
        "roomId":ROOM,"sourceV3Blob":SOURCE,
        "frozenSourceUnmodified":True,"gameAndUiUnchanged":True,
        "existingGeometryReplaced":False,
        "visualApproval":False,
        "targetSectorRadians":[round(A-.105,3),round(A+.105,3)],
        "panelRadiusRange":[.929,.954],
        "wallBlockedRadiusThreshold":round(math.sqrt(.845),3),
        "ceilingMatchesFrozenSlope":True,
        "numberOfWallBays":1,"meshObjects":len(objects),
        "renderViews":[] if a.no_render else list(cameras),
        "lightingClaim":"Cycles still-render direct and indirect bounce only; no baked GI or live bridge integration yet",
        "limitations":["Not yet rendered in context","No user visual approval",
                       "Original V3 room is unchanged"]
    }
    (a.out/"bay-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ASTERIA_BAY_SOURCE_CANDIDATE",json.dumps(report),flush=True)

if __name__=="__main__":
    main()
