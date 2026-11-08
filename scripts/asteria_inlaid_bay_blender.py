#!/usr/bin/env python3
"""Source-fitted original USS Asteria acoustic wall bay and two ceiling wedges.

Geometry replaces ONLY the frozen V3 decoration draw call k=24 and the two
original ceiling wedge draw calls k=36,37 captured in memory by the exact-V3
extractor. No user-facing controls, game/room IDs or source arrays are edited.
This is a visual experiment, not an approved photorealistic model.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import asteria_command_blender as kit

ROOM="AST-D01-BRIDGE"
SOURCE="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
W,D=7.55,6.55
PI=math.pi
ANGLE=24.5*2*PI/64
CEILING_A=36*2*PI/96
CEILING_B=38*2*PI/96

def args():
    a=argparse.ArgumentParser()
    a.add_argument("--materials",type=Path,required=True)
    a.add_argument("--source-report",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--samples",type=int,default=20)
    a.add_argument("--resolution",nargs=2,type=int,default=[960,640])
    a.add_argument("--no-render",action="store_true")
    return a.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def wall(dx,y,r=.953):
    # Exact same authored tangent used in frozen V3 set-details.js.
    return (math.sin(ANGLE)*W*r+math.cos(ANGLE)*dx,y,
            math.cos(ANGLE)*D*r-math.sin(ANGLE)*dx)

def ceiling(a,r,delta=-.002):
    # Exact source V3 original wedge rises 0.66 between .985 and .36.
    y=4.38-(r-.36)/(.985-.36)*.66+delta
    return (math.sin(a)*W*r,y,math.cos(a)*D*r)

def mesh(name,points,faces,material,uvs=None):
    return kit.model(name,points,faces,material,uvs)

def strip(name,points,material,width=.007):
    return kit.pipe(name,points,width,material,segments=3)

def panel_quad(name,left,right,bottom,top,r,material):
    p=[wall(left,bottom,r),wall(right,bottom,r),
       wall(right,top,r),wall(left,top,r)]
    return mesh(name,p,[(0,1,2),(0,2,3)],material,
                [(0,0),(1,0),(1,1),(0,1)])

def panel_solid(name,left,right,bottom,top,back_r,front_r,material):
    # Source-aligned closed skin, real depth without protruding into walkway.
    low=[wall(left,bottom,back_r),wall(right,bottom,back_r),
         wall(right,top,back_r),wall(left,top,back_r)]
    high=[wall(left,bottom,front_r),wall(right,bottom,front_r),
          wall(right,top,front_r),wall(left,top,front_r)]
    p=low+high
    faces=[(4,5,6),(4,6,7),(0,2,1),(0,3,2)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,j+4),(i,j+4,i+4)))
    return mesh(name,p,faces,material)

def wall_bay(m):
    # Unlike the rejected trial, only the ACTUAL original 0.53-meter-wide V3
    # decor k=24 is replaced. Neighbor wall, structural ribs, vents and trims
    # remain untouched. Structural base wall behind r=1 also remains in place.
    panel_solid("Wall / original pitch / moulded ivory cartridge",
                -.255,.255,.73,2.90,.972,.956,m["powder_ivory"])
    # Three broad acoustic faces are recessed exactly inside the original bay.
    # Horizontal cassette segmentation avoids a giant rectangular fake door.
    for n,(lower,upper) in enumerate(((.83,1.31),(1.375,2.215),(2.285,2.80))):
        panel_quad(f"Wall / inset acoustic skin {n}",
                   -.224,.224,lower,upper,.953,m["powder_ivory"])
        strip(f"Wall / flush horizontal gasket {n}",
              [wall(x,lower-.012,.950) for x in (-.220,-.11,0,.11,.220)],
              m["console_gasket"],.0035)
    # Edges follow the ORIGINAL floor-to-ceiling module pitch, not widened
    # beyond the neighboring structural ribs. Small metal details remain subtle.
    for dx in (-.251,.251):
        strip(f"Wall / captive vertical seam {dx:+.3f}",
              [wall(dx,y,.947) for y in (.76,1.10,1.75,2.32,2.86)],
              m["satin_nickel"],.004)
        for y in (.855,1.365,2.24,2.78):
            # A real seated circular fastener, recessed behind the face edge.
            kit.bolt(f"Wall / plated flush fastener {dx:+.3f} {y:.3f}",
                     *wall(dx,y,.955),m["satin_nickel"],r=.009)
    for y in (.763,2.87):
        strip(f"Wall / bounded horizontal bead {y:.3f}",
              [wall(x,y,.948) for x in (-.252,-.14,0,.14,.252)],
              m["rose_bronze"],.005)
    # No fake bright screen; quietly integrated practical above the bay.
    panel_quad("Wall / top ivory polycarbonate diffuser",
               -.193,.193,2.820,2.849,.947,m["powder_ivory"])
    # Narrow ventilation breaks up flatness, without becoming a door grille.
    for k in range(7):
        y=.786+k*.018
        strip(f"Wall / machined supply slot {k}",
              [wall(x,y,.945) for x in (-.165,0,.165)],
              m["console_gasket"],.0025)

def roof_patch(m):
    # Two exact frozen V3 roof sectors have been deleted by source face index.
    # Author a conforming curved replacement at EXACT original wedge angles:
    # a=[2.35619449,2.48709418], r=[.36,.985]. No floating rectangular slab.
    for j in range(10):
        a0=CEILING_A+(CEILING_B-CEILING_A)*j/10
        a1=CEILING_A+(CEILING_B-CEILING_A)*(j+1)/10
        for k in range(8):
            r0=.36+(.985-.36)*k/8
            r1=.36+(.985-.36)*(k+1)/8
            points=[ceiling(a0,r0),ceiling(a1,r0),
                    ceiling(a1,r1),ceiling(a0,r1)]
            mesh(f"Ceiling / source-fit moulded radial section {j}-{k}",
                 points,[(0,1,2),(0,2,3)],m["roof_matched_original"],
                 [(0,0),(1,0),(1,1),(0,1)])
    # Real very shallow trim at boundaries, warm ivory body remains the visual.
    # Avoid dark exterior rectangle seen in rejected first experiment.
    for a in (CEILING_A+.003,CEILING_B-.003):
        strip(f"Ceiling / inset longitudinal join {a:.4f}",
              [ceiling(a,r,-.007) for r in (.41,.50,.62,.75,.87,.94)],
              m["satin_nickel"],.004)
    for k in range(6):
        r=.56+k*.057
        a0=CEILING_A+.016
        a1=CEILING_B-.016
        strip(f"Ceiling / low relief acoustic transverse join {k}",
              [ceiling(a0+(a1-a0)*i/8,r,-.008) for i in range(9)],
              m["powder_ivory"],.005)
    for r in (.460,.838):
        strip(f"Ceiling / inset structural seam {r:.3f}",
              [ceiling(CEILING_A+.009+(CEILING_B-CEILING_A-.018)*i/16,r,-.009)
               for i in range(17)],
              m["rose_bronze"],.0037)

def cameras():
    focus=wall(0,2.02,.954)
    kit.light("Warm suspended bridge practical",(2.5,4.45,-2.4),
              focus,830,(1,.89,.80),(3.8,2.8))
    kit.light("Sky cool reflection",(1.2,4.20,-5.1),
              focus,420,(.76,.85,1),(2.7,2.0))
    kit.light("Aft diffuse set bounce",(-3.3,3.4,2.3),
              focus,470,(1,.90,.84),(3.0,2.0))
    return {
      "wall":kit.camera("QA / one acoustic cartridge",(2.20,2.10,-1.72),
                        focus,46),
      "ceiling":kit.camera("QA / wedge ceiling",(2.2,2.10,-1.72),
                           ceiling((CEILING_A+CEILING_B)/2,.72),44),
      "combined":kit.camera("QA / bridge-scale impression",(-2.32,1.67,2.15),
                            (2.45,2.60,-3.2),39)
    }

def main():
    a=args()
    if a.samples<8 or min(a.resolution)<128:raise ValueError("Invalid Cycles acceptance settings")
    provenance=json.loads(a.source_report.read_text())
    assert provenance['sourceV3Blob']==SOURCE
    assert provenance['removedFaces']==62
    assert set(x['name'] for x in provenance['ranges'])=={
      'wallBayDecor24','ceilingWedge36','ceilingWedge37'}
    assert provenance['selectedWallDecorK']==24
    mreport=json.loads((a.materials/"material-provenance.json").read_text())
    assert mreport['id']=="ASTERIA-COMMAND-PBR-01"
    a.out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    kit.COMMAND=bpy.data.collections.new("USS ASTERIA / EXACT INLAID BAY / STAGE 02")
    bpy.context.scene.collection.children.link(kit.COMMAND)
    presets={"powder_ivory":(.72,.16),"satin_nickel":(.38,.67),
             "rose_bronze":(.43,.56),"console_gasket":(.87,0)}
    m={n:kit.build_material("Asteria / source-fit bay / "+n,n,*p,a.materials)
       for n,p in presets.items()}
    # Roof-only PBR calibration: the frozen original V3 wedge was colored
    # 0xd3c9bd, then converted sRGB->linear and raised to .85 in the V5
    # exporter. Retain the identical authored roughness/normal maps but use
    # its measured original ceiling pigment instead of the darker procedural
    # "powder_ivory" base scan. No shape or game/UI changes.
    roof=kit.build_material("Asteria / roof / exact frozen V3 cream",
                             "powder_ivory",.72,.16,a.materials)
    bsdf=roof.node_tree.nodes.get("Principled BSDF")
    original_links=list(bsdf.inputs["Base Color"].links)
    assert len(original_links)==1
    roof.node_tree.links.remove(original_links[0])
    def source_v3_linear(byte):
        v=byte/255.
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    matched=tuple(source_v3_linear(v)**.85 for v in (0xd3,0xc9,0xbd))
    bsdf.inputs["Base Color"].default_value=(*matched,1.)
    m["roof_matched_original"]=roof
    wall_bay(m)
    roof_patch(m)
    scene=bpy.context.scene
    scene.world=bpy.data.worlds.new("Neutral ship set diffuse ambiance")
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.24,.22,.21,1)
    bg.inputs["Strength"].default_value=.45
    views=cameras()
    scene.render.engine="CYCLES"
    scene.cycles.samples=a.samples
    scene.cycles.max_bounces=5
    scene.cycles.diffuse_bounces=3
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
    scene.view_settings.view_transform="AgX"
    scene.view_settings.look="AgX - Medium High Contrast"
    scene.view_settings.exposure=-.65
    scene.render.resolution_x=a.resolution[0]
    scene.render.resolution_y=a.resolution[1]
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.camera=views["wall"]
    bpy.ops.wm.save_as_mainfile(
        filepath=str((a.out/"asteria-inlaid-bay-stage02.blend").resolve()))
    for curve in [o for o in kit.COMMAND.objects if o.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        curve.select_set(True)
        bpy.context.view_layer.objects.active=curve
        bpy.ops.object.convert(target="MESH")
    objects=[o for o in kit.COMMAND.objects if o.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    options=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    selection="use_selection" if "use_selection" in options else "export_selected"
    bpy.ops.export_scene.gltf(
        filepath=str((a.out/"asteria-inlaid-bay-stage02.glb").resolve()),
        export_format="GLB",**{selection:True})
    if not a.no_render:
        for name,cam in views.items():
            scene.camera=cam
            scene.render.filepath=str((a.out/f"asteria-inlaid-{name}.png").resolve())
            bpy.ops.render.render(write_still=True)
    report={
      "assetId":"ASTERIA_INLAID_WALL_CEILING_STAGE02","roomId":ROOM,
      "frozenV3SourceBlob":SOURCE,"sourceFaceExclusionCount":62,
      "sourceWallBayK":24,"sourceCeilingIndices":[36,37],
      "sourceWallAngle":ANGLE,"sourceRoofAngles":[CEILING_A,CEILING_B],
      "existingStructuralWallRetained":True,"noGameUiOrWalkwayEdits":True,
      "isAnExactFaceReplacement":True,
      "meshObjects":len(objects),
      "renderViews":[] if a.no_render else list(views),
      "lighting":"Original editable Cycles multiple diffuse bounces in isolated scene only",
      "notBakedGlobalIllumination":True,"visualApproval":False,
      "limitations":["Not in-context tested","No photorealism demonstrated",
                     "Physical iPhone GPU not tested"]
    }
    (a.out/"inlaid-bay-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("INLAID_BAY_STAGE02_ASSET",json.dumps(report),flush=True)

if __name__=="__main__":
    main()
