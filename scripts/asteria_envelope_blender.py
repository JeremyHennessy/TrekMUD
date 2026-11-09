#!/usr/bin/env python3
"""Rebuild the complete original USS Asteria bridge ceiling and sidewall shell.

112 source-measured elliptical wall segments, 96 source-measured sloping roof
wedges. Replaces only 864 independently proven frozen V3 generator faces.
Scanned Poly Haven CC0 surface response, physically formed stepped sections,
captured service seams, subtle recessed warm overhead fixtures and ACTUAL
Cycles ambient-occlusion UV1. No game/UI/collision/camera changes, ever.
"""
from __future__ import annotations
import argparse,json,math,sys,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import asteria_command_blender as kit

PI=math.pi;TAU=2*PI
W,D=7.55,6.55
FROZEN="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
MESHES={}

def args():
 p=argparse.ArgumentParser()
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--materials",required=True,type=Path)
 p.add_argument("--command-materials",required=True,type=Path)
 p.add_argument("--source-report",required=True,type=Path)
 p.add_argument("--samples",type=int,default=28)
 p.add_argument("--resolution",type=int,nargs=2,default=[960,640])
 p.add_argument("--bake-ao",action="store_true")
 p.add_argument("--omit-radial-rails",action="store_true",help="QA only: isolate roof radial rail shading without touching the ceiling panels")
 p.add_argument("--stage20-zone",action="store_true",help="QA-only fully formed wall/soffit junction")
 p.add_argument("--no-render",action="store_true")
 return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def wpos(a,r,y):
 return (W*math.sin(a)*r,y,D*math.cos(a)*r)

def roof_y(r):
 return 4.38-(r-.36)/(.985-.36)*.66

def make(name,vertices,faces,material,uv0,uv1=None,flat=True):
 ob=kit.model(name,vertices,faces,material,uv0)
 if flat:
  for f in ob.data.polygons:f.use_smooth=False
 if uv1 is not None:
  layer=ob.data.uv_layers.new(name="AST_BAKED_ENVELOPE_UV")
  for face in ob.data.polygons:
   for li in face.loop_indices:
    i=ob.data.loops[li].vertex_index
    layer.data[li].uv=uv1[i]
 return ob

def build_wall(mat):
 # Original geometry: 112 source V3 curved perimeter modules, from
 # y=0 to y=3.75 at original radius r=1. The new manufactured surface
 # is split into shallow structural cartridges with *physical* end edges.
 # Adjacent original k22..24 acoustic fins stand IN FRONT at r~.94-.96.
 pos=[];faces=[];uv=[];ao=[]
 cols=16;rows=7
 assert cols*rows==112
 for k in range(112):
  a=k*TAU/112;b=(k+1)*TAU/112
  y0=.015;y1=3.745
  base=len(pos)
  for rr in (.997,1.007):
   for t,y in ((a,y0),(b,y0),(b,y1),(a,y1)):
    x,yy,z=wpos(t,rr,y)
    pos.append((x,yy,z))
    # Full-room continuous wall colour at correct measured scan scale.
    uv.append((t*(W+D)*.5/2.0,y/2.0))
    u=((k%cols)+(.03 if t==a else .97))/cols
    v=((k//cols)+(.025 if y==y0 else .975))/rows
    ao.append((u,v) if rr<1 else (2.,2.))
  # Distinct physically shaded surface and four capped sides, closed geometry
  # with no width-wise gaps in the underlying original room silhouette.
  faces.extend([
    (base,base+1,base+2),(base,base+2,base+3),
    (base+4,base+6,base+5),(base+4,base+7,base+6),
    (base,base+4,base+5),(base,base+5,base+1),
    (base+3,base+2,base+6),(base+3,base+6,base+7),
    (base,base+3,base+7),(base,base+7,base+4),
    (base+1,base+5,base+6),(base+1,base+6,base+2)
  ])
 # Preserve the existing source-verified inward facing winding. The
 # original 112 panel interior sheets are the ONLY AO receivers. Prior
 # combined 12-face cartridges gave the exterior/cap triangles shared
 # UV1 coordinates (or 2,2 sentinel), creating giant invalid UV triangles
 # that overwrote the wall AO atlas, making a false near-black bake.
 faces=[(first,third,second) for first,second,third in faces]
 assert len(faces)==112*12
 interior=[];backing=[]
 for k in range(112):
  group=faces[k*12:(k+1)*12]
  interior.extend(group[:2])  # original inner visible rectangle
  backing.extend(group[2:])   # exact same physical exterior and caps
 assert len(interior)==224 and len(backing)==1120
 ob=make("Architecture / 112 source-fit interior acoustic wall AO receivers",
         pos,interior,mat,uv,ao)
 # The backing still renders with the same CC0 PBR maps and precisely the
 # same faces, but has a SEPARATE material, so its exterior/cap UVs cannot
 # influence the interior AO or sample an unrelated baked occlusion atlas.
 outer_mat=mat.copy()
 outer_mat.name="Architecture / original 112 exterior shell and capped edges / PBR no AO"
 shell=make("Architecture / 112 exact outer wall shell and manufactured caps",
           pos,backing,outer_mat,uv,None)
 MESHES['wall']=ob
 MESHES['wallBacking']=shell
 # Modular horizontal joint relief is deliberately subtle. The far
 # acoustic/gallery equipment from V3 remains in front at original positions.
 for y,r,rad in ((.49,.991,.007),(3.12,.991,.007),(3.65,.991,.009)):
  points=[wpos(k*TAU/128,r,y) for k in range(129)]
  kit.pipe(f"Wall / preserved architectural horizontal joint / {y:.2f}",
           points,rad,MATS['satin_nickel'] if y==3.65 else MATS['gasket'],segments=2)
 return ob

def build_ceiling(mat,omit_radial_rails=False):
 # Each of 96 EXACT measured V3 wedge sectors is rebuilt as real sheet
 # material in 3 shallower, manufactured bands. The original inner ceiling
 # ring and other acoustic/cove detail are not removed.
 pos=[];faces=[];uv=[];ao=[]
 cols=16;rows=6
 assert cols*rows==96
 bands=[(.36,.565,0.,0.),(.565,.78,-.018,-.018),
        (.78,.985,0.,0.)]
 for k in range(96):
  a=k*TAU/96;b=(k+1)*TAU/96
  for j,(r0,r1,d0,d1) in enumerate(bands):
   base=len(pos)
   for angle,r,offset in ((a,r0,d0),(b,r0,d0),
                           (b,r1,d1),(a,r1,d1)):
    x,y,z=wpos(angle,r,roof_y(r)+offset)
    pos.append((x,y,z))
    uv.append((x/1.9,z/1.9))
    u=((k%cols)+(.015 if angle==a else .985))/cols
    v=((k//cols)+(j+(0.01 if r==r0 else .99))/3)/rows
    ao.append((u,v))
   faces.extend(((base,base+1,base+2),(base,base+2,base+3)))
 ob=make("Architecture / exact 96 stepped acoustic ceiling radial sectors",
         pos,faces,mat,uv,ao)
 MESHES['ceiling']=ob
 # Genuine dark aluminium captured seams at only every fourth radial
 # panel join, not fake white glow lines across the roof.
 for k in (() if omit_radial_rails else range(0,96,4)):
  a=k*TAU/96
  path=[wpos(a,r,roof_y(r)-.009)
        for r in (.40,.53,.62,.78,.89,.97)]
  kit.pipe(f"Ceiling / captured perimeter cassette rail {k:02d}",
           path,.011,MATS["satin_nickel"],segments=2)
 # Twelve fitted overhead fixtures held within existing wedge slopes;
 # restrained milky polycarbonate diffuser within physical metal housing.
 for k in range(0,96,8):
  a=(k+.5)*TAU/96
  r=.77
  center=wpos(a,r,roof_y(r)-.020)
  tangent=(math.cos(a),0,-math.sin(a))
  def across(scale,yoff):
   return (center[0]+tangent[0]*scale,center[1]+yoff,
           center[2]+tangent[2]*scale)
  kit.pipe(f"Ceiling / {k:02d} / shadow housing",
           [across(-.22,-.023),across(.22,-.023)],.034,MATS['gasket'],segments=3)
  kit.pipe(f"Ceiling / {k:02d} / diffuse built-in practical",
           [across(-.185,-.033),across(.185,-.033)],.019,MATS['light'],segments=3)
 return ob

def stage20_zone():
 """Stage27: one physically coherent forward bridge bulkhead and roof assembly.

 Exact frozen original V3 physical screen bounds are
 box(0,2.04,-6.38,7.2,3.15,.24), source blob 74a154ae...
 (x +-3.60; y .465..3.615); black viewport is narrower (6.43 m).
 Architectural trims stay outside the original black display. The
 Stage26 two-soffit trial is NOT inherited; this starts from Stage23.
 No user collision/UI/camera/command or original-face changes.
 """
 assert "stage20Objects" not in MESHES
 objects=[];lights=[]
 graphite=bpy.data.materials.new("FORWARD27 / graphite architectural reveal")
 graphite.use_nodes=True
 bsdf=graphite.node_tree.nodes.get("Principled BSDF")
 bsdf.inputs["Base Color"].default_value=(.12,.115,.122,1)
 bsdf.inputs["Metallic"].default_value=.32
 bsdf.inputs["Roughness"].default_value=.55
 def p(a,y,d):
  x=W*math.sin(a);z=D*math.cos(a)
  nx=-math.sin(a)/W;nz=-math.cos(a)/D
  scale=d/math.hypot(nx,nz)
  return (x+nx*scale,y,z+nz*scale)
 def add(name,verts,faces,uvs,mat):
  assert verts and faces and len(uvs)==len(verts),(name,len(verts),len(faces))
  ob=kit.model("ZONE20 / FORWARD27 / "+name,verts,faces,mat,uvs)
  objects.append(ob)
 def wall(name,k0,k1,y0,y1,mat,rim,core,cols=36,rows=12):
  a0=k0*TAU/112;a1=k1*TAU/112
  verts=[];uv=[];faces=[]
  for j in range(rows+1):
   t=j/rows;y=y0+(y1-y0)*t
   for i in range(cols+1):
    q=i/cols;a=a0+(a1-a0)*q
    edge=min(t,1-t,q,1-q)
    blend=min(1.,edge/.16);blend=blend*blend*(3-2*blend)
    verts.append(p(a,y,rim+(core-rim)*blend))
    uv.append((a*(W+D)*.5/1.6,y/1.65))
  stride=cols+1
  for j in range(rows):
   for i in range(cols):
    n=j*stride+i
    faces.extend(((n,n+1,n+stride+1),(n,n+stride+1,n+stride)))
  edge=([i for i in range(cols+1)]+
        [j*stride+cols for j in range(1,rows+1)]+
        [rows*stride+i for i in range(cols-1,-1,-1)]+
        [j*stride for j in range(rows-1,0,-1)])
  back=[]
  for n in edge:
   i=n%stride;j=n//stride
   a=a0+(a1-a0)*i/cols;y=y0+(y1-y0)*j/rows
   back.append(len(verts));verts.append(p(a,y,.023))
   uv.append((a*(W+D)*.5/1.6,y/1.65))
  for n in range(len(edge)):
   m=(n+1)%len(edge)
   faces.extend(((edge[n],edge[m],back[m]),(edge[n],back[m],back[n])))
  add(name,verts,faces,uv,mat)
 def roof(name,k0,k1,r0,r1,drop,mat,cols=12,rows=4):
  a0=k0*TAU/112;a1=k1*TAU/112
  verts=[];uv=[];faces=[]
  for j in range(rows+1):
   r=r0+(r1-r0)*j/rows
   for i in range(cols+1):
    a=a0+(a1-a0)*i/cols
    verts.append((W*math.sin(a)*r,roof_y(r)-drop,D*math.cos(a)*r))
    uv.append((W*math.sin(a)*r/1.9,D*math.cos(a)*r/1.9))
  stride=cols+1
  for j in range(rows):
   for i in range(cols):
    n=j*stride+i
    faces.extend(((n,n+1,n+stride+1),(n,n+stride+1,n+stride)))
  add(name,verts,faces,uv,mat)
 def formed_roof(name,k0,k1,profile,mat,steps=96,thickness=.028):
  """Watertight, physically capped, UV-mapped panoramic front ceiling."""
  assert len(profile)>=3 and steps>=40 and thickness>0
  a0=k0*TAU/112;a1=k1*TAU/112
  width=steps+1;band=len(profile);layer=width*band
  verts=[];uv=[];faces=[]
  for side in range(2):
   for rr,yy in profile:
    for i in range(width):
     a=a0+(a1-a0)*i/steps
     verts.append((W*math.sin(a)*rr,yy+side*thickness,D*math.cos(a)*rr))
     uv.append((a*W/1.8,yy/1.8))
  for j in range(band-1):
   for i in range(steps):
    n=j*width+i;m=n+width
    faces.extend(((n,n+1,m+1),(n,m+1,m)))
    faces.extend(((layer+n,layer+m+1,layer+n+1),
                  (layer+n,layer+m,layer+m+1)))
  edge=([i for i in range(width)]+
        [j*width+steps for j in range(1,band)]+
        [(band-1)*width+i for i in range(steps-1,-1,-1)]+
        [j*width for j in range(band-2,0,-1)])
  for i,n in enumerate(edge):
   m=edge[(i+1)%len(edge)]
   faces.extend(((n,m,layer+m),(n,layer+m,layer+n)))
  add(name,verts,faces,uv,mat)
 def screen_prism(name,x0,x1,yz_profile,mat):
  """Closed manufactured section extruded on exact preserved screen bounds."""
  assert x1>x0 and len(yz_profile)>=4
  n=len(yz_profile)
  verts=[];uv=[];faces=[]
  for x in (x0,x1):
   for zz,yy in yz_profile:
    verts.append((x,yy,zz))
    uv.append((x/1.55,yy/1.55))
  for i in range(n):
   k=(i+1)%n
   faces.extend(((i,k,n+k),(i,n+k,n+i)))
  for i in range(1,n-1):
   faces.append((0,i+1,i))
   faces.append((n,n+i,n+i+1))
  add(name,verts,faces,uv,mat)
 # Two broad formed sidewall fields replace SIX disconnected field,
 # fascia and plinth modules. The same architectural millimeter depth
 # is measured along the true 112-segment source ellipse.
 for k0,k1 in ((36,45),(67,76)):
  wall(f"one continuous PBR sidewall bulkhead / arc {k0}-{k1}",
       k0+.04,k1-.04,.68,3.07,MATS["wall"],.164,.073)
  wall(f"joined graphite service sill / arc {k0}-{k1}",
       k0+.04,k1-.04,.16,.55,graphite,.240,.208,cols=36,rows=4)
  wall(f"continuous scan-textured upper return / arc {k0}-{k1}",
       k0+.04,k1-.04,3.14,3.61,MATS["wall"],.162,.130,cols=36,rows=5)
 # All six original fixtures retain exact Stage23 measured placement and
 # intensity; making integrated geometry (not lighting tweaks) is the test.
 for idx,(k0,k1) in enumerate(((36,39),(39,42),(42,45),
                               (67,70),(70,73),(73,76))):
  mid=(k0+k1)/2.
  roof(f"recessed physical fixture housing {idx+1}",
       mid-.42,mid+.42,.89,.959,.118,graphite,cols=8,rows=3)
  roof(f"inset milky diffuser {idx+1}",
       mid-.31,mid+.31,.905,.945,.143,MATS["light"],cols=8,rows=2)
  a=mid*TAU/112;r=.922
  lights.append([round(W*math.sin(a)*r,5),round(roof_y(r)-.16,5),
                 round(D*math.cos(a)*r,5)])
 # Unlike the rejected Stage26 local cove, this is ONE entire forward
 # panoramic 40-sector formed ceiling reaching ACROSS the screen crown.
 formed_roof("panoramic ceiling-to-frontage formed acoustic shell",
             36.03,75.97,
             [(.985,roof_y(.985)-.104),(.974,roof_y(.974)-.105),
              (.955,roof_y(.955)-.097),(.935,roof_y(.935)-.097),
              (.910,roof_y(.910)-.099),(.883,roof_y(.883)-.105),
              (.852,roof_y(.852)-.108),(.825,roof_y(.825)-.108)],
             MATS["ceiling"])
 formed_roof("continuous physically captured narrow ceiling reveal",
             36.03,75.97,
             [(.979,roof_y(.979)-.129),(.975,roof_y(.975)-.130),
              (.971,roof_y(.971)-.132),(.966,roof_y(.966)-.130)],
             graphite,steps=96,thickness=.009)
 # Exact 2372-era V3 authored external viewscreen box centre and dimensions:
 # x[-3.6,3.6], y[.465,3.615], z[-6.5,-6.26]. Do not move or remove it.
 # New fitted manufacturing trims surround but never cross the preserved
 # dark display x[-3.215,3.215], y[.755,3.285] z~-6.115.
 screen_prism("full-width sculpted forward screen upper crown",
              -3.77,3.77,
              [(-6.55,3.47),(-6.54,3.56),(-6.48,3.655),
               (-6.38,3.686),(-6.27,3.679),(-6.15,3.615),
               (-6.14,3.53),(-6.36,3.47)],MATS["wall"])
 screen_prism("full-width integrated equipment/screen lower sill",
              -3.77,3.77,
              [(-6.54,.43),(-6.54,.53),(-6.47,.63),
               (-6.30,.67),(-6.17,.58),(-6.17,.43)],MATS["wall"])
 for side in (-1,1):
  x0,x1=(-3.82,-3.62) if side==-1 else (3.62,3.82)
  screen_prism(f"screen side-fitted full-height standing reveal {side}",
              x0,x1,
              [(-6.55,.55),(-6.55,3.55),(-6.47,3.62),
               (-6.29,3.62),(-6.21,3.53),(-6.21,.55)],
              MATS["satin_nickel"])
  x0,x1=(-3.59,-3.55) if side==-1 else (3.55,3.59)
  screen_prism(f"screen internal retained-margin shadowline {side}",
              x0,x1,
              [(-6.23,.66),(-6.23,3.49),
               (-6.17,3.49),(-6.17,.66)],graphite)
 screen_prism("screen crown lower captured black shadow joint",
              -3.62,3.62,
              [(-6.23,3.47),(-6.23,3.50),
               (-6.15,3.50),(-6.15,3.47)],graphite)
 # Connect outer flank edges to the original wall/backing in two height
 # segments, preserving the old geometry and surrounding walk paths.
 for k in (36,45,67,76):
  for y0,y1 in ((.16,1.65),(1.65,3.61)):
   wall(f"architectural edge column {k}-{y0}",k-.035,k+.035,
        y0,y1,MATS["satin_nickel"],.187,.176,cols=2,rows=4)
 assert len(objects)==35,len(objects)
 MESHES["stage20Objects"]=objects
 return {"bayCount":6,"originalSectors":[[36,45],[67,76]],
         "realManufacturedReturnedWallShells":2,"physicalSoffits":1,
         "integratedPracticalFixtures":6,"lightingPositions":lights,
         "maxInwardProjectionMeters":.24,"wallInsetDepthMeters":.091,
         "screenReference":{"outerCentre":[0,2.04,-6.38],
                            "outerSize":[7.2,3.15,.24],
                            "blackDisplayWidth":6.43},
         "sourceScan":"Poly Haven painted_plaster_wall CC0",
         "zoneMeshCount":len(objects),
         "continuousForwardSoffitSpans":1,
         "screenCrownAndBezelPieces":7,
         "rejectedStage26CoveNotInherited":True,
         "noGameOrCollisionWrites":True,"notVisualApproved":True}

def other_studio():
 scene=bpy.context.scene
 world=bpy.data.worlds.new("USS Asteria Stage08 / warm studio GI test")
 scene.world=world;world.use_nodes=True
 bg=world.node_tree.nodes.get("Background")
 bg.inputs["Color"].default_value=(.21,.225,.245,1)
 bg.inputs["Strength"].default_value=.38
 kit.light("Overhead broad softbox",(-4.3,5.6,1.4),
           (0,2,0),900,(1,.88,.76),(5.2,4.1))
 kit.light("Forward cool indirect proxy",(4.4,4.9,-3.9),
           (0,2.4,-1.3),520,(.75,.88,1),(4.5,3.1))
 kit.light("Aft warm set rebound",(0,3.2,5.5),
           (0,2,1),330,(1,.93,.86),(4.5,3.3))
 # The photographic floor reference is only a neutral Cycles light-bounce
 # surface and is NOT exported into the candidate as modified walking mesh.
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=6.3,depth=.08,
                                     location=(0,0,-.02))
 floor=bpy.context.object
 floor.name="QA ONLY / neutral approximate floor bounce, NOT exported"
 floor.scale=(1.14,1.14,1)
 mat=bpy.data.materials.new("QA ONLY / muted floor reflector")
 mat.diffuse_color=(.23,.21,.25,1)
 floor.data.materials.append(mat)
 return floor

def studio_cameras():
 # Cameras view physically existing V3 room coordinates in Y-up with the
 # exact independent Blender coordinate mapping, no in-game camera changes.
 return {
  'aft':kit.camera('QA / aft overview',(-1.23,1.67,4.80),
                   (0,1.9,-1.3),37),
  'forward':kit.camera('QA / forward view',(0,1.67,-1.3),
                       (0,2.75,-4.3),40),
  'wall':kit.camera('QA / material and wall study',(1.5,1.67,-1.25),
                    (5.1,2.0,-3.5),45),
  'ceiling':kit.camera('QA / ceiling architectural coffers',(-2.3,1.67,2.15),
                       (0,4.0,.1),43),
 }

def material(name,kind,root,rough,metal):
 return kit.build_material(name,"architectural_"+kind,rough,metal,root)

def make_emissive():
 mat=bpy.data.materials.new("Asteria / warm opal ceiling diffuser")
 mat.use_nodes=True
 bsdf=mat.node_tree.nodes.get("Principled BSDF")
 bsdf.inputs["Base Color"].default_value=(.8,.71,.64,1)
 bsdf.inputs["Roughness"].default_value=.69
 if "Emission Color" in bsdf.inputs:
  bsdf.inputs["Emission Color"].default_value=(1.,.81,.66,1)
  bsdf.inputs["Emission Strength"].default_value=1.4
 return mat

def actual_ao_bake(out):
 # A real Cycles ambient-occlusion bake on the full roof and wall envelope,
 # not a fake emissive-grey overlay or claim of multi-bounce GI.
 scene=bpy.context.scene
 scene.render.engine="CYCLES"
 scene.cycles.samples=24
 scene.render.bake.margin=3
 proofs={}
 for key in ("wall","ceiling"):
  ob=MESHES[key]
  uv=ob.data.uv_layers.get("AST_BAKED_ENVELOPE_UV")
  assert uv is not None
  mat=ob.data.materials[0]
  bitmap=bpy.data.images.new(f"ASTERIA_ACTUAL_CYCLES_{key.upper()}_AO",
                    width=1536,height=1536,alpha=False,float_buffer=False)
  bitmap.generated_color=(1,1,1,1)
  tex=mat.node_tree.nodes.new("ShaderNodeTexImage")
  tex.image=bitmap
  tex.label=f"Original Asteria actual Cycles {key} AO"
  uvnode=mat.node_tree.nodes.new("ShaderNodeUVMap")
  uvnode.uv_map="AST_BAKED_ENVELOPE_UV"
  mat.node_tree.links.new(uvnode.outputs["UV"],tex.inputs["Vector"])
  group=bpy.data.node_groups.get("glTF Settings")
  if group is None:group=bpy.data.node_groups.new("glTF Settings","ShaderNodeTree")
  if "Occlusion" not in [s.name for s in group.interface.items_tree]:
   group.interface.new_socket(name="Occlusion",in_out="INPUT",
                              socket_type="NodeSocketColor")
  holder=mat.node_tree.nodes.new("ShaderNodeGroup")
  holder.node_tree=group
  mat.node_tree.links.new(tex.outputs["Color"],holder.inputs["Occlusion"])
  # The global Cycles AO bake considers geometry across the whole enclosed
  # ship. The earlier unbounded bake made the entire room BLACK. Instead
  # render real local-ray AO with a measured 0.32 m spatial radius using
  # Cycles' native Ambient Occlusion shader, then bake its emission output.
  # This is still genuine ray-traced Cycles local AO, NOT indirect GI.
  output=next(n for n in mat.node_tree.nodes if n.type=="OUTPUT_MATERIAL")
  original_surface=output.inputs["Surface"].links[0].from_socket
  occluder=mat.node_tree.nodes.new("ShaderNodeAmbientOcclusion")
  occluder.inputs["Distance"].default_value=.32
  occluder.inputs["Color"].default_value=(1.,1.,1.,1.)
  occluder.samples=24
  light=mat.node_tree.nodes.new("ShaderNodeEmission")
  mat.node_tree.links.new(occluder.outputs["Color"],light.inputs["Color"])
  mat.node_tree.links.new(light.outputs["Emission"],output.inputs["Surface"])
  for node in mat.node_tree.nodes:node.select=False
  tex.select=True;mat.node_tree.nodes.active=tex
  bpy.ops.object.select_all(action="DESELECT")
  ob.select_set(True);bpy.context.view_layer.objects.active=ob
  ob.data.uv_layers.active=uv
  overlaid=MESHES.get("stage20Objects",[])
  assert all(not ob.hide_render for ob in overlaid)
  for ob in overlaid:ob.hide_render=True
  try:
   bpy.ops.object.bake(type="EMIT")
  finally:
   for ob in overlaid:ob.hide_render=False
   # Restore the ORIGINAL physically scanned Principled shader. The
   # temporary AO emission nodes are not part of the published model.
   mat.node_tree.links.new(original_surface,output.inputs["Surface"])
   mat.node_tree.nodes.remove(light)
   mat.node_tree.nodes.remove(occluder)
  path=out/f"asteria-envelope-{key}-real-cycles-ao.png"
  bitmap.filepath_raw=str(path.resolve())
  bitmap.file_format="PNG"
  bitmap.save();bitmap.pack()
  ob.data.uv_layers.active_index=0
  proofs[key]={"file":str(path),"textureSize":[1536,1536],
      "source":"real Blender Cycles Ambient Occlusion node baked to UV1 using 0.32m ray distance",
      "rayRadiusMeters":.32,"notIndirectGI":True}
 return proofs

def main():
 a=args()
 if a.samples<8 or min(a.resolution)<200:raise ValueError("Invalid visual test settings")
 proof=json.loads(a.source_report.read_text())
 assert proof["sourceV3Blob"]==FROZEN and proof["removedFaces"]==864
 assert [x["faces"] for x in proof["ranges"]]==[672,192]
 assert proof["floorCastRetained"] and proof["viewscreenAndStationMeshesRetained"]
 pbr=json.loads((a.materials/"envelope-material-provenance.json").read_text())
 assert pbr["id"]=="ASTERIA_ENVELOPE_SCANNED_PBR_08"
 base=json.loads((a.command_materials/"material-provenance.json").read_text())
 assert base["id"]=="ASTERIA-COMMAND-PBR-01"
 a.out.mkdir(parents=True,exist_ok=True)
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 kit.COMMAND=bpy.data.collections.new("USS ASTERIA / SOURCE EXACT ARCHITECTURAL ENVELOPE / 08")
 bpy.context.scene.collection.children.link(kit.COMMAND)
 global MATS
 MATS={
  "wall":material("Asteria / CC0 micro-scan / architectural wall","wall",a.materials,.67,.025),
  "ceiling":material("Asteria / CC0 micro-scan / stepped ceiling","ceiling",a.materials,.80,0),
  "satin_nickel":kit.build_material("Asteria / captured satin trim","satin_nickel",.38,.67,a.command_materials),
  "gasket":kit.build_material("Asteria / captured neutral gasket","console_gasket",.87,0,a.command_materials),
  "light":make_emissive(),
 }
 if a.stage20_zone and not a.omit_radial_rails:
  raise ValueError("Stage20 requires the exact Stage12 rail-free base")
 build_wall(MATS["wall"]);build_ceiling(MATS["ceiling"],a.omit_radial_rails)
 zone_evidence=stage20_zone() if a.stage20_zone else None
 studio_floor=other_studio()
 cameras=studio_cameras()
 sc=bpy.context.scene
 sc.render.engine="CYCLES"
 sc.cycles.samples=a.samples
 sc.cycles.diffuse_bounces=3
 sc.cycles.max_bounces=5
 sc.cycles.use_denoising=False
 for layer in sc.view_layers:
  if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
 sc.view_settings.view_transform="AgX"
 sc.view_settings.look="AgX - Medium High Contrast"
 sc.view_settings.exposure=-.6
 sc.render.resolution_x=a.resolution[0];sc.render.resolution_y=a.resolution[1]
 sc.render.resolution_percentage=100
 sc.render.image_settings.file_format="PNG"
 sc.camera=cameras["aft"]
 ao=actual_ao_bake(a.out) if a.bake_ao else None
 bpy.ops.wm.save_as_mainfile(
  filepath=str((a.out/"asteria-realistic-architectural-envelope-08.blend").resolve()))
 # Export only original authored architecture collection; floor and studio
 # lights are for offline light bounce, never part of live collision or game.
 for obj in list(kit.COMMAND.objects):
  if obj.type!="CURVE":continue
  bpy.ops.object.select_all(action="DESELECT")
  obj.select_set(True);bpy.context.view_layer.objects.active=obj
  bpy.ops.object.convert(target="MESH")
 meshes=[ob for ob in kit.COMMAND.objects if ob.type=="MESH"]
 assert len(meshes)==(30 if a.omit_radial_rails else 54)+(zone_evidence["zoneMeshCount"] if zone_evidence else 0),len(meshes)
 bpy.ops.object.select_all(action="DESELECT")
 for ob in meshes:ob.select_set(True)
 bpy.context.view_layer.objects.active=meshes[0]
 opts=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
 selection="use_selection" if "use_selection" in opts else "export_selected"
 bpy.ops.export_scene.gltf(
  filepath=str((a.out/"asteria-realistic-architectural-envelope-08.glb").resolve()),
  export_format="GLB",**{selection:True})
 if not a.no_render:
  for name,camera in cameras.items():
   sc.camera=camera
   sc.render.filepath=str((a.out/f"asteria-envelope-{name}.png").resolve())
   bpy.ops.render.render(write_still=True)
 report={
  "id":"ASTERIA_ARCHITECTURAL_ENVELOPE_08",
  "sourceV3Blob":FROZEN,"roomId":"AST-D01-BRIDGE",
  "exactOriginalWallFacesRemoved":672,
  "exactOriginalRoofFacesRemoved":192,
  "originalFloorViewscreensAndFurniturePreserved":True,
  "originalThreeBaysPreserved":True,
  "newWallPanels":112,"roofWedges":96,
  "formedRoofBandsPerWedge":3,"physicalPracticalHousings":12,
  "radialRailsEmitted":0 if a.omit_radial_rails else 24,
  "railIsolationExperiment":bool(a.omit_radial_rails),
  "originalPbrScan":pbr["scanPage"],
  "pbrLicense":pbr["license"],"PBRScanPhotoBased":True,
  "architecturalBakedAO":ao,"fullIndirectLightmapYetUnproven":True,
  "meshObjects":len(meshes),"stage20ManufacturedZone":zone_evidence,
  "renderedViewNames":[] if a.no_render else list(cameras),
  "noGameWrites":True,"visualApproved":False,
  "noPhysicalIphoneVerification":True,
  "stage":"isolated candidate, independent browser comparison required"
 }
 (a.out/"architectural-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print("ARCHITECTURAL_ENVELOPE_STAGE08",json.dumps(report))
if __name__=="__main__":main()
