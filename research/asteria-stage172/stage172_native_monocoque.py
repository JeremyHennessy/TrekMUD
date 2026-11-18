"""Stage172 isolated monocoque candidate. Source-only Blender preview. NO DEPLOY.
This deliberately changes the camera-facing service geometry rather than Stage171 trim.
The original 89 locked meshes and approved player scene cannot be modified.
"""
import bpy,bmesh,hashlib,json,math
from mathutils import Vector
from pathlib import Path
OUT=Path('_stage168/output');OUT.mkdir(parents=True,exist_ok=True)
expect='9b988aaec53afa557011e5cba1addc19b1de6bf8f5d8bb6a7edc560ae8452f1c'
locked=[o for o in bpy.data.collections['01_LOCKED_ORIGINAL_89_MESHES'].objects if o.type=='MESH']
assert len(locked)==89
seed=bpy.data.objects['EDITABLE_STUDY_ONLY_ORIGINAL_76_FACE_SEED']
assert len(seed.data.polygons)==76
def sig(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(('%.9g %.9g %.9g;'%tuple(v.co)).encode())
 for f in o.data.polygons:h.update((','.join(map(str,f.vertices))+';').encode())
 h.update(('|'.join(m.name for m in o.data.materials if m)).encode())
 return h.hexdigest()
before={o.name:sig(o) for o in locked}
def B(x,y,z):return Vector((x,-z,y))
def G(v):return Vector((v.x,v.z,-v.y))
def mat(name,rgb,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
 b=m.node_tree.nodes.get('Principled BSDF')
 b.inputs['Base Color'].default_value=(*rgb,1)
 b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 return m
# All are unqualified nonphotographic STUDY materials.
mats=[
 mat('172_SHIELDED_GRAPHITE_CORE_NO_PHOTO_PBR',(.07,.083,.094),.46,.38),
 mat('172_CERAMIC_LOAD_CHEEKS_NO_PHOTO_PBR',(.71,.685,.62),.10,.34),
 mat('172_SATIN_UNDER_RIM_CRADLE_NO_PHOTO_PBR',(.30,.345,.37),.72,.28),
 mat('172_MATTE_RECESSED_CAVITY_NO_PHOTO_PBR',(.013,.018,.023),.25,.50)]
seed.data.materials.clear()
for m in mats:seed.data.materials.append(m)
bm=bmesh.new();bm.from_mesh(seed.data)
bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=10,use_grid_fill=True)
bm.to_mesh(seed.data);bm.free();seed.data.update()
inv=seed.matrix_world.inverted()
# Surface-sculpt the actual source casting, keeping its upper contact and lower
# service screening while producing a visibly narrower, load-bearing midsection.
for v in seed.data.vertices:
 p=G(seed.matrix_world@v.co)
 if p.y>=1.079:continue
 dx=p.x+1.26727; dz=p.z-.59117
 s=.034+.105*math.exp(-((p.y-.785)/.18)**2)
 p.x=-1.26727+dx*(1-s)
 p.z=.59117+dz*(1-s)
 shoulder=math.exp(-((p.y-1.023)/.043)**2)
 p.x+=dx*.022*shoulder;p.z+=dz*.022*shoulder
 v.co=inv@B(*p)
seed.data.update()
def cutter(name,center,r):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=B(*center))
 o=bpy.context.object;o.name=name;o.scale=(r[0],r[2],r[1])
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return o
def difference(o):
 mod=seed.modifiers.new('SCOOP_INSET_'+o.name,'BOOLEAN')
 mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=o
 bpy.context.view_layer.objects.active=seed
 bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(o,do_unlink=True)
# True non-through cavities above the protected service-door envelope.
difference(cutter('CAMERA_LEFT_OPEN_RECESS',(-1.735,.895,.625),(.195,.145,.285)))
difference(cutter('CAMERA_FRONT_OPEN_RECESS',(-1.265,.883,1.055),(.305,.125,.180)))
# Wide, solid, tapered, welded load cheeks; no unsupported rods, trim bands,
# exposed equipment or office-style legs. Coordinates are measured in metres.
def loft(name,rows,mode,idx):
 verts=[];faces=[]
 for row in rows:
  if mode=='side':
   y,lo,hi,out,inn=row
   ring=[(out,y,lo),(out,y,hi),(inn,y,hi),(inn,y,lo)]
  else:
   y,lo,hi,out,inn=row
   ring=[(lo,y,out),(hi,y,out),(hi,y,inn),(lo,y,inn)]
  verts.extend(B(*q) for q in ring)
 for k in range(len(rows)-1):
  a=k*4;b=(k+1)*4
  for j in range(4):faces.append((a+j,a+(j+1)%4,b+(j+1)%4,b+j))
 faces.extend([(3,2,1,0),tuple(4*(len(rows)-1)+j for j in range(4))])
 mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
 for m in mats:mesh.materials.append(m)
 for f in mesh.polygons:f.material_index=idx
 return ob
side=loft('172_SIDE_LOAD_CHEEK',[
 (1.067,.31,.998,-1.711,-1.625),(1.015,.40,.985,-1.718,-1.632),
 (.935,.51,.955,-1.718,-1.620),(.835,.65,.875,-1.699,-1.611),
 (.690,.665,.835,-1.664,-1.560),(.510,.665,.795,-1.635,-1.545),
 (.340,.675,.785,-1.624,-1.535)],'side',1)
front=loft('172_FRONT_LOAD_BUTTRESS',[
 (1.065,-1.67,-1.28,1.024,.945),(1.014,-1.625,-1.295,1.033,.941),
 (.931,-1.573,-1.305,1.023,.923),(.822,-1.49,-1.325,1.001,.910),
 (.686,-1.460,-1.324,.970,.884),(.510,-1.458,-1.330,.957,.862),
 (.341,-1.457,-1.340,.953,.850)],'front',1)
cradle=loft('172_STRUCTURAL_UNDER_RIM_SATIN_CRADLE',[
 (1.071,-1.688,-.854,1.035,.941),
 (1.033,-1.679,-.870,1.026,.933),
 (1.001,-1.663,-.892,1.001,.908)],'front',2)
for o in (side,front,cradle):
 mod=seed.modifiers.new('UNION_'+o.name,'BOOLEAN')
 mod.operation='UNION';mod.solver='EXACT';mod.object=o
 bpy.context.view_layer.objects.active=seed
 bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
seed.hide_select=False;seed.select_set(True);bpy.context.view_layer.objects.active=seed
bevel=seed.modifiers.new('CAST_EDGE_RADIUS_6MM','BEVEL')
bevel.width=.006;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.55
bpy.ops.object.modifier_apply(modifier=bevel.name)
for f in seed.data.polygons:
 q=G(seed.matrix_world@f.center)
 side_d=((q.y-.895)/.16)**2+((q.z-.625)/.31)**2
 front_d=((q.y-.883)/.15)**2+((q.x+1.265)/.33)**2
 if (q.x< -1.57 and side_d<.95 and q.y>.72) or (q.z>.86 and front_d<.88 and q.y>.72):
  f.material_index=3
 f.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.008)
bpy.ops.object.mode_set(mode='OBJECT')
uv=seed.data.uv_layers.active;assert uv is not None
uv.name='UV0'
uv1=seed.data.uv_layers.new(name='UV1_NOT_BAKED_STUDY')
for i in range(len(seed.data.loops)):uv1.data[i].uv=uv.data[i].uv
bm=bmesh.new();bm.from_mesh(seed.data)
nonmanifold=sum(1 for edge in bm.edges if not edge.is_manifold)
faces=len(bm.faces);bm.free()
assert nonmanifold==0,nonmanifold
assert all(sig(o)==before[o.name] for o in locked),'protected source modified'
assert max(G(seed.matrix_world@v.co).y for v in seed.data.vertices)<1.11
seed.name='STAGE172_MONOCOQUE_UNAPPROVED'
seed['ORIGINAL_COMMAND_SHA256']=expect
seed['SOURCE_ONLY_NOT_BROWSER']=True
seed['NO_PHOTO_PBR_NO_RELEASE']=True
scene=bpy.context.scene
scene['ASTERIA_ART_VERDICT']='HOLD pending real visual review'
scene['ASTERIA_RELEASE_AUTHORIZED']=False
scene['ASTERIA_FULL_BROWSER_EQUIVALENCE']=False
source_file=OUT/'STAGE172_MONOCOQUE_NATIVE_EDITABLE_UNAPPROVED.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(source_file.resolve()))
scene.cycles.samples=16
scene.view_layers[0].cycles.use_denoising=False
for name,cam,w,h in (
 ('STAGE172_DESKTOP_BLENDER_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',1280,800),
 ('STAGE172_MOBILE_BLENDER_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',390,844),
 ('STAGE172_SIDE_BLENDER_NOT_BROWSER','SCULPT_INSPECTION_SIDE_ONLY',1200,900)):
 scene.camera=bpy.data.objects[cam]
 scene.render.resolution_x=w;scene.render.resolution_y=h
 scene.render.resolution_percentage=100
 scene.render.filepath=str((OUT/(name+'.png')).resolve())
 bpy.ops.render.render(write_still=True)
report={'stage':172,'source_sha256':expect,'locked_original_meshes_identical':89,
 'candidate_faces':faces,'nonmanifold_edges':nonmanifold,
 'UV0':True,'UV1_UNBAKED':True,'photographic_pbr_qualified':False,
 'full_browser_ab':False,'release':False,
 'art_verdict':'HOLD: source-camera visual rejection/selection required'}
(OUT/'stage172-report.json').write_text(json.dumps(report,indent=2))
print('STAGE172_UNAPPROVED_NATIVE',json.dumps(report))
