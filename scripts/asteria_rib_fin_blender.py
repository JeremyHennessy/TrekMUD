#!/usr/bin/env python3
"""Sculpt a single real USS Asteria wall acoustic rib-and-fin cassette.

Opt-in visual experiment, based directly on the original 2372-era V3 wall
generator. Replaces ONLY 58 measured triangles of its wall decoration k=24.
The frozen ceiling wedges, wall substrate, original neighboring ribs, game,
collision and UI are not edited or remade. No rectangular opaque door slab.
"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import asteria_command_blender as kit

ORIGINAL="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
ROOM="AST-D01-BRIDGE"
W,D=7.55,6.55
A=(24+.5)*2*math.pi/64

def parse():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--materials",required=True,type=Path)
    p.add_argument("--command-materials",required=True,type=Path)
    p.add_argument("--source-report",required=True,type=Path)
    p.add_argument("--samples",type=int,default=28)
    p.add_argument("--resolution",type=int,nargs=2,default=[960,640])
    p.add_argument("--no-render",action="store_true")
    return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def wall(dx,y,r=.951):
    """Use V3's exact wallPos(a,r) and tangent (cos(a),-sin(a))."""
    return (math.sin(A)*W*r+math.cos(A)*dx, y,
            math.cos(A)*D*r-math.sin(A)*dx)

def slotted_fabric(name,x0,x1,y0,y1,mat,r=.963):
    # Four separately mounted little acoustic backing strips, not a big panel.
    # The surrounding original structural wall remains in place.
    verts=[wall(x0,y0,r),wall(x1,y0,r),
           wall(x1,y1,r),wall(x0,y1,r)]
    uvs=[(x0/.10,y0/.12),(x1/.10,y0/.12),
         (x1/.10,y1/.12),(x0/.10,y1/.12)]
    obj=kit.model(name,verts,[(0,1,2),(0,2,3)],mat,uvs)
    for f in obj.data.polygons:f.use_smooth=False
    return obj

def manufactured_fin(idx,dx,width,mat):
    # Genuinely sculpted closed curved cross-section: flat backed, crowned
    # front, chamfered shoulders and eased, tapering ends. Shaped in the
    # ORIGINAL tangent plane, not world-aligned door-prism boxes.
    y0,y1=.81,2.84
    stations=34
    lateral=[-1.,-.92,-.62,0.,.62,.92,1.]
    edge_profile=[.955,.951,.944,.936,.944,.951,.955]
    verts=[]
    uvs=[]
    for j in range(stations+1):
        y=y0+(y1-y0)*j/stations
        taper=min(1.,max(0.,(y-y0)/.087),max(0.,(y1-y)/.087))
        taper=max(0.,taper)**.7
        # Original stage geometry is deliberately asymmetric between ribs;
        # that is subtle manufacture, not geometric random distortion.
        crown_offset=(-1 if idx%2 else 1)*.0011
        for k,lat in enumerate(lateral):
            x=dx+lat*width/2
            r=.960+((edge_profile[k]+crown_offset)-.960)*taper
            verts.append(wall(x,y,r))
            uvs.append((x/.10,y/.12))
        # Back two corners have no visible overlap with adjacent V3 wall.
        for lat in (1.,-1.):
            x=dx+lat*width/2
            verts.append(wall(x,y,.970))
            uvs.append((x/.10,y/.12))
    ring=len(lateral)+2
    faces=[]
    for j in range(stations):
        start=j*ring
        for k in range(ring):
            l=(k+1)%ring
            a=start+k;b=start+l;c=start+ring+k;d=start+ring+l
            faces.extend(((a,b,c),(b,d,c)))
    for i in range(1,ring-1):
        faces.append((0,i+1,i))
        p=stations*ring
        faces.append((p,p+i,p+i+1))
    obj=kit.model(f"Acoustic rib {idx:02d} / sculpted full-depth manufactured crown",
                  verts,faces,mat,uvs)
    return obj

def anchored_strip(name,points,radius,material):
    return kit.pipe(name,points,radius,material,segments=2)

def seated_recess(name,dx,y,material):
    # Thin mounted flush hex/diamond detail lying in the original wall plane.
    p=[wall(dx-.012,y,.946),wall(dx,y-.010,.946),
       wall(dx+.012,y,.946),wall(dx,y+.010,.946)]
    return kit.model(name,p,[(0,1,2),(0,2,3)],material,
                     [(0,0),(.5,0),(1,0),(.5,1)])

def geometry(m):
    # Carefully retain original .53m module pitch and fine vertical rhythm.
    # Four acoustically damped lanes recess BEHIND five shaped vertical fins.
    centers=(-.202,-.101,0.,.101,.202)
    shellwidth=.042
    for i in range(4):
        between=(centers[i]+centers[i+1])/2
        # Only a 55mm textile lane, the source wall remains visible elsewhere.
        slotted_fabric(f"Acoustic lane {i} / woven material held behind fins",
                       between-.026,between+.026,.861,2.796,
                       m["acoustic_linen"],r=.964)
        for edge in (between-.029,between+.029):
            anchored_strip(f"Acoustic lane {i} / fine captured seam {edge:+.3f}",
               [wall(edge,y,.951) for y in (.87,1.45,2.0,2.78)],
               .0024,m["console_gasket"])
    for idx,dx in enumerate(centers):
        manufactured_fin(idx,dx,shellwidth,m["formed_pearl"])
        # Visible metal against actual curvature; no wide flat filler sheet.
        for side in (-1,1):
            x=dx+side*.024
            anchored_strip(f"Acoustic rib {idx} / captive satin rolled edge {side}",
              [wall(x,y,.949) for y in (.88,1.14,1.62,2.16,2.76)],
              .0028,m["satin_nickel"])
    # Original lateral wall ribs from V3 are untouched. Fine end retainers
    # replace only those belonging to old decor call; no extra full-height
    # frame and no dark cabinet perimeter/door threshold.
    for y in (.806,2.841):
        anchored_strip(f"Bay / restrained integrated horizontal end clamp {y:.3f}",
          [wall(x,y,.950) for x in (-.239,-.160,-.08,0.,.08,.16,.239)],
          .004,m["rose_bronze"])
    for dx in (-.244,.244):
        for y in (.87,1.82,2.76):
            seated_recess(f"Bay / original-pitch captive fastener {dx:+.3f}/{y:.2f}",
                          dx,y,m["satin_nickel"])

def lights_cameras():
    focus=wall(0,1.85,.94)
    world=bpy.data.worlds.new("Asteria QA / diffuse real Cycles bounce")
    world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.26,.255,.245,1)
    bg.inputs["Strength"].default_value=.35
    kit.light("Overhead warm practical",(2.9,4.12,-2.3),focus,720,
              (1.,.87,.77),(4.0,3.2))
    kit.light("Cooled near-screens reflection",(1.1,3.2,-5.2),focus,360,
              (.73,.84,1.),(2.3,2.2))
    kit.light("Broad command diffused bounce",(-2.6,3.1,2.2),focus,490,
              (1.,.94,.89),(4.0,2.8))
    return {
      "grazing":kit.camera("QA / oblique manufacturing depth",
                   (4.1,1.76,-2.68),focus,55),
      "front":kit.camera("QA / fine source wall pitch",
                   (3.3,1.75,-2.72),focus,52),
      "detail":kit.camera("QA / fin and felt physical detail",
                   (4.30,1.85,-3.56),wall(.02,1.9,.946),65),
    }

def main():
    a=parse()
    if a.samples<8 or min(a.resolution)<200:
        raise ValueError("Require actual well-resolved Cycles inspection")
    provenance=json.loads(a.source_report.read_text())
    assert provenance["sourceV3Blob"]==ORIGINAL
    assert provenance["selectedWallDecorK"]==24
    assert provenance["removedFaces"]==62
    byname={entry["name"]:entry for entry in provenance["ranges"]}
    assert byname["wallBayDecor24"]["faces"]==58
    assert byname["ceilingWedge36"]["faces"]==byname["ceilingWedge37"]["faces"]==2
    maps=json.loads((a.materials/"material-provenance.json").read_text())
    assert maps["id"]=="ASTERIA_RIB_FIN_MATERIALS_03"
    commandmaps=json.loads((a.command_materials/"material-provenance.json").read_text())
    assert commandmaps["id"]=="ASTERIA-COMMAND-PBR-01"
    a.out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    kit.COMMAND=bpy.data.collections.new("USS ASTERIA / ONE V3 ACOUSTIC RIB BAY / 03")
    bpy.context.scene.collection.children.link(kit.COMMAND)
    mats={
      "acoustic_linen":kit.build_material("Asteria V3 / woven acoustic textile","acoustic_linen",.89,0,a.materials),
      "formed_pearl":kit.build_material("Asteria V3 / pearl structural rib","formed_pearl",.69,.09,a.materials),
      "satin_nickel":kit.build_material("Asteria V3 / captured satin nickel","satin_nickel",.38,.67,a.command_materials),
      "rose_bronze":kit.build_material("Asteria V3 / barely warm face fastener","rose_bronze",.43,.56,a.command_materials),
      "console_gasket":kit.build_material("Asteria V3 / recessed neutral seal","console_gasket",.87,0,a.command_materials),
    }
    geometry(mats)
    views=lights_cameras()
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.samples=a.samples
    scene.cycles.max_bounces=5
    scene.cycles.diffuse_bounces=3
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
    scene.view_settings.view_transform="AgX"
    scene.view_settings.look="AgX - Medium High Contrast"
    scene.view_settings.exposure=-.55
    scene.render.resolution_x=a.resolution[0]
    scene.render.resolution_y=a.resolution[1]
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.camera=views["front"]
    bpy.ops.wm.save_as_mainfile(
        filepath=str((a.out/"asteria-original-pitch-rib-fin-bay-03.blend").resolve()))
    for curve in [ob for ob in kit.COMMAND.objects if ob.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        curve.select_set(True)
        bpy.context.view_layer.objects.active=curve
        bpy.ops.object.convert(target="MESH")
    meshes=[ob for ob in kit.COMMAND.objects if ob.type=="MESH"]
    assert len(meshes)>=35,len(meshes)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:ob.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    keys=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    select="use_selection" if "use_selection" in keys else "export_selected"
    bpy.ops.export_scene.gltf(
        filepath=str((a.out/"asteria-original-pitch-rib-fin-bay-03.glb").resolve()),
        export_format="GLB",**{select:True})
    if not a.no_render:
        for name,camera in views.items():
            scene.camera=camera
            scene.render.filepath=str((a.out/f"asteria-rib-fin-{name}.png").resolve())
            bpy.ops.render.render(write_still=True)
    report={
        "assetId":"ASTERIA_ORIGINAL_RIB_FIN_BAY_03",
        "roomId":ROOM,"frozenSource":ORIGINAL,
        "removedOriginalWallDecorFaces":58,
        "retainedOriginalCeilingWedgeFaces":4,
        "preservedOriginalWallSubstrate":True,
        "originalAdjacentStructuralRibsUnmodified":True,
        "noOpaqueDoorPanel":True,
        "numberOfCurvedManufacturedFins":5,
        "numberOfSeparateAcousticLanes":4,
        "meshObjects":len(meshes),
        "sourceMeasuredWallPitchMetres":.53,
        "renderedViews":[] if a.no_render else list(views),
        "noGameOrPlayerUIWrites":True,
        "noBakedGIClaim":True,"visualApproval":False,
        "knownLimits":["Material style is authored, not photography",
                       "Full room view not tested by this Blender script",
                       "Real iPhone GPU FPS unverified"]
    }
    (a.out/"rib-fin-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ASTERIA_RIB_FIN_SOURCE_FITTED_REPORT",json.dumps(report))
if __name__=="__main__":
    main()
