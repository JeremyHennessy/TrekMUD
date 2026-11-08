#!/usr/bin/env python3
"""Sculpt three neighboring USS Asteria wall acoustic rib-and-fin cassettes.

Opt-in visual experiment, based directly on the original 2372-era V3 wall
generator. Replaces ONLY 174 independently measured decoration triangles for k=22,23,24.
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
BAY_IDS=(22,23,24)
A=(23+.5)*2*math.pi/64

def parse():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--materials",required=True,type=Path)
    p.add_argument("--command-materials",required=True,type=Path)
    p.add_argument("--source-report",required=True,type=Path)
    p.add_argument("--samples",type=int,default=28)
    p.add_argument("--resolution",type=int,nargs=2,default=[960,640])
    p.add_argument("--no-render",action="store_true")
    p.add_argument("--bake-felt-ao",action="store_true",
                   help="QA-only: actual Cycles contact AO on 12 acoustic lanes, unique UV1 atlas")
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

def three_bays(mats):
    # Reuse the exact validated Stage03 rib/lane geometry without spatial
    # copying or Blender object transforms. Each module's reference plane
    # is recomputed from the ORIGINAL frozen V3 tangent and wall ellipse.
    # Materials are shared; GLB should deduplicate its 15 PBR images.
    global A
    preserved=A
    for k in BAY_IDS:
        A=(k+.5)*2*math.pi/64
        geometry(mats)
    A=preserved

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


def bake_felt_contact_ao(out,mats):
    """Actual Cycles AO bake on all 12 original-geometry acoustic lanes.

    Geometry, PBR base/normal/roughness maps and UV0 remain unchanged. Only
    the acoustic material receives ONE added UV1 AO texture. This is real
    local contact occlusion, NOT multi-bounce global illumination or a fake
    procedural grayscale shader.
    """
    lanes=sorted((ob for ob in kit.COMMAND.objects
                  if ob.type=="MESH" and
                  ob.name.startswith("Acoustic lane ") and
                  "woven material" in ob.name),
                 key=lambda ob: ob.name)
    assert len(lanes)==12,[o.name for o in lanes]
    scene=bpy.context.scene
    assert scene.render.engine=="CYCLES"
    scene.render.bake.margin=3
    # Keep the original untouched textile on the control route. Blender
    # instances a new material only for the flagged experiment.
    baked_mat=mats["acoustic_linen"].copy()
    baked_mat.name="ASTERIA / Cycles baked 12-lane acoustic felt AO"
    bitmap=bpy.data.images.new("ASTERIA_ACTUAL_CYCLES_FELT_CONTACT_AO",
                               width=1024,height=768,alpha=False,float_buffer=False)
    bitmap.generated_color=(1,1,1,1)
    tree=baked_mat.node_tree
    target=tree.nodes.new("ShaderNodeTexImage")
    target.image=bitmap
    target.label="Actual Cycles baked felt contact AO"
    # Each lane is mapped onto a distinct 256x256 atlas tile, preventing
    # overlaid bakes. Four strips across each of three measured V3 bays.
    uv_node=tree.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map="AST_BAKED_FELT_AO_UV"
    tree.links.new(uv_node.outputs["UV"],target.inputs["Vector"])
    group=bpy.data.node_groups.get("glTF Settings")
    if group is None:
        group=bpy.data.node_groups.new("glTF Settings","ShaderNodeTree")
    if "Occlusion" not in [t.name for t in group.interface.items_tree]:
        group.interface.new_socket(name="Occlusion",in_out="INPUT",
                                   socket_type="NodeSocketColor")
    holder=tree.nodes.new("ShaderNodeGroup")
    holder.node_tree=group
    tree.links.new(target.outputs["Color"],holder.inputs["Occlusion"])
    for node in tree.nodes:node.select=False
    target.select=True
    tree.nodes.active=target
    bpy.ops.object.select_all(action="DESELECT")
    for i,ob in enumerate(lanes):
        assert len(ob.data.vertices)==4,ob.name
        assert len(ob.data.polygons)==2,ob.name
        assert len(ob.data.uv_layers)==1,ob.name
        ob.data.materials[0]=baked_mat
        atlas=ob.data.uv_layers.new(name="AST_BAKED_FELT_AO_UV")
        # Keep an 8 pixel padding boundary within every 256x256 cell.
        x=i%4
        y=i//4
        mapping=((0,0),(1,0),(1,1),(0,1))
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                k=ob.data.loops[li].vertex_index
                a,b=mapping[k]
                atlas.data[li].uv=((x+(8/256 if a==0 else 1-8/256))/4,
                                   (y+(8/256 if b==0 else 1-8/256))/3)
        ob.data.uv_layers.active=atlas
        ob.select_set(True)
    bpy.context.view_layer.objects.active=lanes[0]
    bpy.ops.object.bake(type="AO")
    image=out/"asteria-three-bays-cycles-felt-contact-ao.png"
    bitmap.filepath_raw=str(image.resolve())
    bitmap.file_format="PNG"
    bitmap.save()
    bitmap.pack()
    # Crucial: revert UV0 as the active base-color/normal mapping before
    # exporting, while the AO shader references UV1 explicitly by name.
    for ob in lanes:
        ob.data.uv_layers.active_index=0
    return {"texture":str(image),"laneCount":len(lanes),
            "textureResolution":[1024,768],
            "uvAtlasGrid":[4,3],"source":"real Blender Cycles AO",
            "notTrueGlobalIllumination":True}

def main():
    a=parse()
    if a.samples<8 or min(a.resolution)<200:
        raise ValueError("Require actual well-resolved Cycles inspection")
    provenance=json.loads(a.source_report.read_text())
    assert provenance["sourceV3Blob"]==ORIGINAL
    assert provenance["selectedWallDecorK"]==[22,23,24]
    assert provenance["removedFaces"]==174
    byname={entry["name"]:entry for entry in provenance["ranges"]}
    assert list(byname)==['wallBayDecor22','wallBayDecor23','wallBayDecor24']
    assert all(byname[f"wallBayDecor{k}"]["faces"]==58 for k in BAY_IDS)
    assert provenance["ceilingWedgesRetained"] and provenance["otherGeometryUntouched"]
    maps=json.loads((a.materials/"material-provenance.json").read_text())
    assert maps["id"]=="ASTERIA_RIB_FIN_MATERIALS_03"
    commandmaps=json.loads((a.command_materials/"material-provenance.json").read_text())
    assert commandmaps["id"]=="ASTERIA-COMMAND-PBR-01"
    a.out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    kit.COMMAND=bpy.data.collections.new("USS ASTERIA / THREE ORIGINAL V3 ACOUSTIC RIB BAYS / 04")
    bpy.context.scene.collection.children.link(kit.COMMAND)
    mats={
      "acoustic_linen":kit.build_material("Asteria V3 / woven acoustic textile","acoustic_linen",.89,0,a.materials),
      "formed_pearl":kit.build_material("Asteria V3 / pearl structural rib","formed_pearl",.69,.09,a.materials),
      "satin_nickel":kit.build_material("Asteria V3 / captured satin nickel","satin_nickel",.38,.67,a.command_materials),
      "rose_bronze":kit.build_material("Asteria V3 / barely warm face fastener","rose_bronze",.43,.56,a.command_materials),
      "console_gasket":kit.build_material("Asteria V3 / recessed neutral seal","console_gasket",.87,0,a.command_materials),
    }
    three_bays(mats)
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
    bakedAO=bake_felt_contact_ao(a.out,mats) if a.bake_felt_ao else None
    bpy.ops.wm.save_as_mainfile(
        filepath=str((a.out/"asteria-three-original-pitch-rib-bays-04.blend").resolve()))
    for curve in [ob for ob in kit.COMMAND.objects if ob.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        curve.select_set(True)
        bpy.context.view_layer.objects.active=curve
        bpy.ops.object.convert(target="MESH")
    meshes=[ob for ob in kit.COMMAND.objects if ob.type=="MESH"]
    assert len(meshes)==105,len(meshes)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:ob.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    keys=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    select="use_selection" if "use_selection" in keys else "export_selected"
    bpy.ops.export_scene.gltf(
        filepath=str((a.out/"asteria-three-original-pitch-rib-bays-04.glb").resolve()),
        export_format="GLB",**{select:True})
    if not a.no_render:
        for name,camera in views.items():
            scene.camera=camera
            scene.render.filepath=str((a.out/f"asteria-three-rib-fin-{name}.png").resolve())
            bpy.ops.render.render(write_still=True)
    report={
        "assetId":"ASTERIA_THREE_ORIGINAL_RIB_FIN_BAYS_04",
        "roomId":ROOM,"frozenSource":ORIGINAL,
        "removedOriginalWallDecorFaces":174,
        "retainedOriginalCeilingWedgeFaces":4,
        "preservedOriginalWallSubstrate":True,
        "originalAdjacentStructuralRibsUnmodified":True,
        "noOpaqueDoorPanel":True,
        "numberOfCurvedManufacturedFins":15,
        "numberOfSeparateAcousticLanes":12,
        "meshObjects":len(meshes),
        "sourceMeasuredWallPitchMetres":.53,
        "selectedOriginalWallModules":list(BAY_IDS),
        "originalCeilingTrianglesRemoved":0,
        "renderedViews":[] if a.no_render else list(views),
        "noGameOrPlayerUIWrites":True,
        "noBakedGIClaim":True,"visualApproval":False,
        "knownLimits":["Material style is authored, not photography",
                       "Full room view not tested by this Blender script",
                       "Real iPhone GPU FPS unverified"]
    }
    if bakedAO:
        report["realBakedFeltContactAO"]=bakedAO
        report["preservedBaseNormalAndRoughness"]=True
        report["bakedAOMaterials"]="12 acoustic felt strips only"
    (a.out/"rib-fin-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ASTERIA_RIB_FIN_SOURCE_FITTED_REPORT",json.dumps(report))
if __name__=="__main__":
    main()
