#!/usr/bin/env python3
"""Real fully furnished A/B Cycles renders of source hatch vs formed hatch.

Never produce fake photorealism claims from a Blender pass. Imports the actual
shared furniture/bridge shell/console/fins GLBs, both genuine original-V3
baseline/candidate GLBs, and the new real hatch GLB at identical viewpoints.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

def xyz(p):
 return Vector((p[0],-p[2],p[1]))
def camera(name,x,z,yaw,pitch):
 p=(x,1.67,z)
 target=(x+math.sin(yaw)*math.cos(pitch),
         1.67+math.sin(pitch),
         z-math.cos(yaw)*math.cos(pitch))
 data=bpy.data.cameras.new(name)
 data.lens=34.4 # 65deg vertical FOV approximately at 36mm standard film gate; used only for studio comparison
 obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
 obj.location=xyz(p);obj.rotation_euler=(xyz(target)-obj.location).to_track_quat("-Z","Y").to_euler()
 return obj
def area(name,p,target,power,color,size):
 data=bpy.data.lights.new(name,"AREA")
 data.energy=power;data.color=color;data.size=size
 obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
 obj.location=xyz(p);obj.rotation_euler=(xyz(target)-obj.location).to_track_quat("-Z","Y").to_euler()
def import_glb(path):
 assert path.is_file(),path
 before=set(bpy.data.objects.keys())
 bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
 names=set(bpy.data.objects.keys())-before
 objs=[bpy.data.objects[k] for k in names]
 meshes=[o for o in objs if o.type=="MESH"]
 assert meshes,(path,"no mesh in imported GLB")
 return meshes
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--base-site",required=True,type=Path)
 p.add_argument("--candidate-site",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--samples",type=int,default=24)
 p.add_argument("--resolution",type=int,nargs=2,default=[1000,640])
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
 a.out.mkdir(parents=True,exist_ok=True)
 source="asteria-v3-restored-pbr.glb"
 baseline=import_glb(a.base_site/source)
 candidate=import_glb(a.candidate_site/source)
 shared=[
  "asteria-hero-chair-candidate.glb",
  "asteria-command-set-candidate.glb",
  "asteria-three-original-pitch-rib-bays-04.glb",
  "asteria-realistic-architectural-envelope-08.glb",
 ]
 counts={name:len(import_glb(a.base_site/name)) for name in shared}
 hatches=import_glb(a.candidate_site/"asteria-stage22-formed-side-hatches.glb")
 assert len(hatches)>=80,len(hatches)
 scene=bpy.context.scene;scene.render.engine="CYCLES"
 scene.cycles.samples=a.samples;scene.cycles.diffuse_bounces=3
 scene.cycles.max_bounces=6
 if hasattr(scene.cycles,"use_denoising"):scene.cycles.use_denoising=False
 for layer in scene.view_layers:
  if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
 scene.view_settings.view_transform="AgX"
 scene.view_settings.look="AgX - Medium High Contrast"
 scene.view_settings.exposure=-.50
 scene.render.resolution_x=a.resolution[0]
 scene.render.resolution_y=a.resolution[1]
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 world=bpy.data.worlds.new("Stage22 source-identical physical bridge lighting")
 world.use_nodes=True;scene.world=world
 world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.20,.22,.25,1)
 world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.33
 area("Cycles / above command",(-4.3,5.6,1.4),(0,2.,0),860,(1,.88,.78),5.0)
 area("Cycles / forward cool",(4.2,4.9,-3.7),(0,2.,-1.2),520,(.74,.85,1),4.5)
 area("Cycles / aft",(0,3.5,5.2),(0,1.6,1),300,(1,.90,.82),3.6)
 views={
  "wall":camera("Exact original wall view",-2.6,-.5,-1.18,-.14),
  "aft":camera("Exact original aft view",-1.23,4.8,.44,-.14),
 }
 for mode in ("baseline","formedHatches"):
  for o in baseline:o.hide_render=(mode!="baseline")
  for o in candidate:o.hide_render=(mode=="baseline")
  for o in hatches:o.hide_render=(mode=="baseline")
  for v,c in views.items():
   scene.camera=c
   scene.render.filepath=str((a.out/f"stage22-real-furnished-{mode}-{v}.png").resolve())
   bpy.ops.render.render(write_still=True)
 for o in baseline+candidate+hatches:o.hide_render=False
 report={"id":"ASTERIA_STAGE22_FURNISHED_CYCLES_AB",
   "baselineV3Meshes":len(baseline),"candidateV3Meshes":len(candidate),
   "sharedModelMeshes":counts,"stage22HatchMeshes":len(hatches),
   "realGLBModelsImported":2+len(shared)+1,
   "cyclesSamples":a.samples,"renderCount":4,"cameraNames":list(views),
   "sameLightingAndFurnishedAssetAssemblies":True,
   "exactBrowserProjectionNotProvenInCycles":True,
   "artApproved":False}
 (a.out/"stage22-real-furnished-cycles-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print("STAGE22_FURNISHED_CYCLES_AB",json.dumps(report))
if __name__=="__main__":main()
