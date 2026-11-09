#!/usr/bin/env python3
"""Real furnished Cycles Stage23-vs-Stage28 roof macro A/B, not an empty studio.

Loads all five exact source-protected GLBs. Renders before/after by changing
only the visibility of the new 45 physically formed ROOF28 objects.
Never exports, writes, or changes the persistent game or walkable meshes.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import bpy
from mathutils import Vector

def xyz(p):
 return Vector((p[0],-p[2],p[1]))

def cam(name,position,target,lens=42):
 data=bpy.data.cameras.new(name)
 data.lens=lens
 obj=bpy.data.objects.new(name,data)
 bpy.context.collection.objects.link(obj)
 obj.location=xyz(position)
 obj.rotation_euler=(xyz(target)-obj.location).to_track_quat("-Z","Y").to_euler()
 return obj

def light(name,p,target,power,rgb,xy):
 data=bpy.data.lights.new(name,"AREA")
 data.energy=power
 data.color=rgb
 data.shape="RECTANGLE"
 data.size=xy[0];data.size_y=xy[1]
 obj=bpy.data.objects.new(name,data)
 bpy.context.collection.objects.link(obj)
 obj.location=xyz(p)
 obj.rotation_euler=(xyz(target)-obj.location).to_track_quat("-Z","Y").to_euler()
 return obj

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--site",required=True,type=Path)
 parser.add_argument("--report",required=True,type=Path)
 parser.add_argument("--out",required=True,type=Path)
 parser.add_argument("--resolution",type=int,nargs=2,default=[900,600])
 parser.add_argument("--samples",type=int,default=20)
 a=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
 a.out.mkdir(parents=True,exist_ok=True)
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 filenames=("asteria-v3-restored-pbr.glb",
            "asteria-hero-chair-candidate.glb",
            "asteria-command-set-candidate.glb",
            "asteria-three-original-pitch-rib-bays-04.glb",
            "asteria-realistic-architectural-envelope-08.glb")
 counts={}
 for name in filenames:
  f=a.site/name
  assert f.is_file(),f
  before=set(bpy.data.objects.keys())
  bpy.ops.import_scene.gltf(filepath=str(f.resolve()))
  new=set(bpy.data.objects.keys())-before
  counts[name]=len(new)
  assert len(new)>0,(name,"GLB did not import geometry")
 stage23=[obj for obj in bpy.data.objects if obj.type=="MESH" and "ZONE20" in obj.name]
 roof28=[obj for obj in bpy.data.objects if obj.type=="MESH" and "ROOF28" in obj.name]
 assert len(stage23)==44,("Stage23 unchanged source control missing",len(stage23))
 assert len(roof28)==45,("Stage28 macro ceiling missing",len(roof28))
 sc=bpy.context.scene
 sc.render.engine="CYCLES"
 sc.cycles.samples=a.samples
 sc.cycles.diffuse_bounces=3
 sc.cycles.max_bounces=6
 # The pinned Ubuntu Blender 4.0.2 runner lacks OpenImageDenoiser.
 # Keep Cycles native sampling intact, never silently substitute a synthetic image.
 if hasattr(sc.cycles,"use_denoising"):sc.cycles.use_denoising=False
 for layer in sc.view_layers:
  if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
 sc.view_settings.view_transform="AgX"
 sc.view_settings.look="AgX - Medium High Contrast"
 sc.view_settings.exposure=-.5
 sc.render.image_settings.file_format="PNG"
 sc.render.resolution_x=a.resolution[0]
 sc.render.resolution_y=a.resolution[1]
 sc.render.resolution_percentage=100
 world=bpy.data.worlds.new("Asteria physically furnished room and source assets")
 world.use_nodes=True;sc.world=world
 bg=world.node_tree.nodes.get("Background")
 bg.inputs["Color"].default_value=(.19,.21,.25,1)
 bg.inputs["Strength"].default_value=.32
 light("Furnished Cycles / roof soft key",(-4.3,5.6,1.4),
       (0,2.,0),860,(1,.88,.78),(5.2,4.1))
 light("Furnished Cycles / forward cool bounce",(4.2,4.9,-3.7),
       (0,2.2,-1.2),520,(.74,.85,1),(4.6,3.2))
 light("Furnished Cycles / aft rim",(0,3.5,5.2),
       (0,1.6,1.0),300,(1,.90,.82),(3.6,3.2))
 fixtures=json.loads(a.report.read_text())["stage20ManufacturedZone"]["lightingPositions"]
 assert len(fixtures)==6
 for i,p in enumerate(fixtures):
  light(f"ZONE20 / physical diffuser area emission {i}",p,
        (p[0]+2.,p[1]-1.6,p[2]),42,(1.,.87,.72),(.55,.13))
 cameras={
  "wall":cam("QA real furnished wall",(-2.6,1.67,-.5),(-7.05,1.9,-2.3),49),
  "aft":cam("QA real furnished aft",(-1.23,1.67,4.8),(0,.68,.73),37),
 }
 for mode in ("baseline","zone20"):
  for obj in roof28:obj.hide_render=(mode=="baseline")
  for name,camera in cameras.items():
   sc.camera=camera
   sc.render.filepath=str((a.out/f"stage20-furnished-cycles-{mode}-{name}.png").resolve())
   bpy.ops.render.render(write_still=True)
 for obj in roof28:obj.hide_render=False
 report={"id":"ASTERIA_STAGE28_CYCLES_TRUE_STAGE23_AB",
         "loadedFiveOriginalAndCandidateGLBs":list(counts),
         "importedObjectCounts":counts,"stage20ZoneMeshes":len(stage23),
          "stage28RoofMeshes":len(roof28),"stage23WallAssembliesSameInBoth":True,
         "cameras":list(cameras),"modes":["baseline","zone20"],
         "renderCount":4,"resolution":a.resolution,"samples":a.samples,
         "originalAssetsAndCameraIdentical":True,
          "onlyRoof28VisibilityChangesBetweenCyclesShots":True,
         "fullFurnishedStudioNotEmptyEnvelope":True,
         "browserLightingAndCyclesMayDiffer":True,
         "ownerArtApproved":False}
 (a.out/"stage20-furnished-cycles-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print("STAGE20_FULL_FURNISHED_CYCLES_AB",json.dumps(report))
if __name__=="__main__":main()
