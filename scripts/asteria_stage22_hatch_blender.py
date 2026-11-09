#!/usr/bin/env python3
"""Stage22 opt-in physical port/starboard sealed-hatch GLB (ART TRIAL ONLY).

Replaces only the two exact 120-face V3 sideHatch(-1,0)/sideHatch(1,0)
drawing calls recorded by the same frozen source, NOT a spatial or material
crop. Preserves door placement, sealed-room meaning, room topology, camera,
player collisions and controls. CC0 scan only where provenance is documented;
engineered metals/gaskets are explicitly procedural original content.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import bpy
import asteria_command_blender as kit

FROZEN="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
def args():
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--architectural-materials",type=Path,required=True)
 p.add_argument("--command-materials",type=Path,required=True)
 p.add_argument("--source-report",type=Path,required=True)
 p.add_argument("--no-render",action="store_true")
 p.add_argument("--samples",type=int,default=48)
 return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def emissive(name,base,energy):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get("Principled BSDF")
 p.inputs["Base Color"].default_value=(*base,1)
 p.inputs["Roughness"].default_value=.52
 p.inputs["Metallic"].default_value=0
 if "Emission Color" in p.inputs:
  p.inputs["Emission Color"].default_value=(*base,1)
  p.inputs["Emission Strength"].default_value=energy
 return m

def build_hatch(sign,mats):
 """2.03m wide, 3.06m tall and source-matched sealed side doorway.

 x is cabin lateral, z spans the hatch from -1.3 to +.74.
 Camera-facing original source is near x=+/-6.845. The formed new field
 reaches +/-6.82; door is still sealed scenery and has no walkthrough link.
 """
 assert sign in (-1,1)
 side="PORT" if sign==-1 else "STARBOARD"
 z=-.28
 count_before=len(kit.COMMAND.objects)
 def add(tag,x,y,dz,dx,dy,dz_extent,material,bevel=.014):
  return kit.box(f"STAGE22 / {side} / {tag}",
      (sign*x,y,z+dz),(dx,dy,dz_extent),material,
      min(bevel,dx/3,dy/3,dz_extent/3))
 # A REAL assembled shell, not a single opaque rectangular slab.
 # Behind the formed door, original bridge wall envelope remains unchanged.
 add("cast perimeter back and closed mounting box",7.024,1.62,0,.15,3.055,2.02,mats["wall"],.035)
 # Long cast retaining rails define the door's outer frame.
 for zs,where in ((-.975,"left"),(.975,"right")):
  add(f"continuous {where} satin cast jamb",6.937,1.62,zs,.125,3.045,.095,mats["metal"],.028)
 for y,name in ((.146,"lower"),(3.103,"upper")):
  add(f"formed {name} full-width header",6.933,y,0,.137,.104,1.97,mats["metal"],.027)
 # Behind-door black edge with complete width; gaps are physical and bounded.
 add("recessed gasket backing",6.884,1.621,0,.079,2.815,1.82,mats["gasket"],.016)
 # Deep port/starboard channels and top/bottom compression seal.
 for zs,side_name in ((-.868,"left"),(.868,"right")):
  add(f"{side_name} recessed elastomer compression seal",
      6.835,1.615,zs,.046,2.68,.047,mats["gasket"],.008)
 for y,where in ((.264,"bottom"),(2.984,"top")):
  add(f"{where} gasket crosspiece",6.837,y,0,.049,.051,1.72,mats["gasket"],.009)
 # Two independent pressed composite leaves with deliberately recessed seam.
 # The intentionally shallow 4cm physical groove must remain visible in WebGL.
 for j,(zdelta,leaf) in enumerate(((-.429,"A"),(.429,"B"))):
  add(f"cast pressure door leaf {leaf}",6.811,1.610,zdelta,
      .071,2.580,.790,mats["ivory"],.030)
  # Physically proud polished facets and machined bevels, attached to each leaf.
  add(f"leaf {leaf} formed lower shadow plinth",6.770,.445,zdelta,
      .035,.115,.722,mats["graphite"],.016)
  add(f"leaf {leaf} upper pressed service inlay",6.771,2.468,zdelta,
      .026,.365,.691,mats["wall"],.022)
  # 3 full-length micro-molded acoustic channels, no painted lines.
  for index,offset in enumerate((-.226,0,.226)):
   add(f"leaf {leaf} concave long-channel {index}",
       6.769,1.504,zdelta+offset,.018,1.455,.029,
       mats["metal"] if index==1 else mats["gasket"],.006)
  # Finger recess, built from dark inset glass and 2 independent edge pieces.
  add(f"leaf {leaf} actuator recess",6.747,1.480,zdelta,
      .015,.170,.175,mats["gasket"],.012)
  add(f"leaf {leaf} mechanical latch tongue",6.727,1.482,zdelta,
      .018,.055,.074,mats["metal"],.010)
 # Central joint is a deep, continuous elastomer seal, not an open hole.
 add("center continuous separator seal",6.775,1.612,0,
     .055,2.560,.049,mats["gasket"],.009)
 # Milled top light housing and truly separate opal emitting insert.
 add("recessed upper practical graphite housing",6.776,2.985,0,
     .065,.102,1.555,mats["graphite"],.017)
 add("diffuse upper practical opal insert",6.731,2.987,0,
     .031,.047,1.376,mats["opal"],.009)
 # Below-door structural toe and actual small ventilation slots.
 add("pressed low service toe",6.812,.211,0,.089,.090,1.63,mats["graphite"],.018)
 for j in range(7):
  add(f"toe ventilation opening shadow {j}",6.758,.214,-.63+j*.21,
      .009,.021,.099,mats["gasket"],.004)
 # Secured housing fasteners: four visible fittings, no floating ornament.
 for zi in (-.792,.792):
  for yi in (.315,2.908):
   add(f"captured flush fastener {yi:.2f} {zi:.3f}",
       6.784,yi,zi,.016,.030,.030,mats["metal"],.006)
 # Narrow status indicators one per leaf, integrated and shallow.
 for zi in (-.43,.43):
  add(f"flush local annunciator {zi:.2f}",6.741,2.705,zi,
      .014,.022,.088,mats["opal"],.004)
 assert len(kit.COMMAND.objects)-count_before >=40
 return len(kit.COMMAND.objects)-count_before

def main():
 a=args();a.out.mkdir(parents=True,exist_ok=True)
 proof=json.loads(a.source_report.read_text())
 assert proof["sourceV3Blob"]==FROZEN and proof["originalV3FilesUnmodified"]
 assert proof["sourceAuthoringFunction"]=="sideHatch"
 assert [(v["name"],v["start"],v["end"],v["faces"]) for v in proof["ranges"]]==[
   ("port",92830,92950,120),("starboard",92950,93070,120)]
 kit.COMMAND=bpy.data.collections.new("USS ASTERIA / STAGE22 TWO FORMED SEALED HATCHES")
 bpy.context.scene.collection.children.link(kit.COMMAND)
 mats={
  "wall":kit.build_material("Hatch / Poly Haven CC0 scanned wall composite",
                             "architectural_wall",.67,.025,a.architectural_materials),
  "ivory":kit.build_material("Hatch / original powder ivory",
                            "powder_ivory",.72,.16,a.command_materials),
  "graphite":kit.build_material("Hatch / original powder graphite",
                               "powder_graphite",.67,.15,a.command_materials),
  "metal":kit.build_material("Hatch / original satin nickel",
                            "satin_nickel",.38,.67,a.command_materials),
  "gasket":kit.build_material("Hatch / original elastomer",
                             "console_gasket",.87,0,a.command_materials),
  "opal":emissive("Hatch / engineered translucent opal practical",(.84,.70,.57),.95)
 }
 counts={str(side):build_hatch(side,mats) for side in (-1,1)}
 objects=[o for o in kit.COMMAND.objects if o.type=="MESH"]
 assert len(objects)==sum(counts.values()) and len(objects)>=80
 assert all(o.data.uv_layers for o in objects),[o.name for o in objects if not o.data.uv_layers]
 # All output meshes remain in the exact original physical door footprints.
 for obj in objects:
  x,y,z=kit.xyz(0,0,0) if False else obj.location
  assert abs(obj.location.x)<=7.20
  assert -.02<=obj.location.z<=3.22 # Blender z = world y
  assert -1.45<=obj.location.y<=1.00 # Blender y = -world z
 bpy.context.view_layer.update()
 bpy.ops.wm.save_as_mainfile(filepath=str((a.out/"asteria-stage22-formed-side-hatches.blend").resolve()))
 bpy.ops.object.select_all(action="DESELECT")
 for ob in objects: ob.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 opts=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
 selector="use_selection" if "use_selection" in opts else "export_selected"
 bpy.ops.export_scene.gltf(filepath=str((a.out/"asteria-stage22-formed-side-hatches.glb").resolve()),
       export_format="GLB",**{selector:True})
 report={"id":"ASTERIA_STAGE22_TWO_SOURCE_EXACT_HATCHES","sourceV3Blob":FROZEN,
   "originalSourceHatchSpans":proof["ranges"],"replacedOriginalSourceFaces":240,
   "meshCount":len(objects),"meshesPerSide":counts,
   "materialSources":{"scan":"Poly Haven CC0 painted_plaster_wall via envelope-material-provenance.json",
     "metalAndPaint":"Original Asteria authored command PBR / no photo scan claim",
     "opal":"explicit engineered emissive material, not a photographic scan"},
   "sourceGeometryModified":False,"gameCollisionUIOrRoomGraphChanged":False,
   "selfDeclaredArtApproved":False,"realBrowserAndFurnishedCyclesPending":True}
 (a.out/"stage22-hatch-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print("STAGE22_FORMED_TWO_HATCHES_REPORT",json.dumps(report))
if __name__=="__main__": main()
