"""Stage171: NONRELEASE source-fitted native Blender sculpt of original port casting.
The 89 original command objects, gameplay assets, and published files are reference only.
Source-camera previews are isolated Blender studies, not game Chromium acceptance.
"""
import bpy, bmesh, hashlib, json, math, os
from pathlib import Path
from mathutils import Vector

OUT=Path('_stage168/output'); OUT.mkdir(parents=True, exist_ok=True)
SOURCE=Path(os.environ['ASTERIA_COMMAND_PATH'])
EXPECT='9b988aaec53afa557011e5cba1addc19b1de6bf8f5d8bb6a7edc560ae8452f1c'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECT
locked=[x for x in bpy.data.collections['01_LOCKED_ORIGINAL_89_MESHES'].objects if x.type=='MESH']
assert len(locked)==89,len(locked)
seed=bpy.data.objects['EDITABLE_STUDY_ONLY_ORIGINAL_76_FACE_SEED']
assert len(seed.data.polygons)==76

def signature(obj):
    m=obj.data
    h=hashlib.sha256()
    for v in m.vertices: h.update(('%.9g %.9g %.9g;'%tuple(v.co)).encode())
    for p in m.polygons: h.update((','.join(str(k) for k in p.vertices)+';').encode())
    h.update(('|'.join(mat.name for mat in m.materials if mat)).encode())
    return h.hexdigest()
before={x.name:signature(x) for x in locked}

def in_gltf(p):
    return Vector((p.x,p.z,-p.y))
def to_blender(p):
    return Vector((p.x,-p.z,p.y))

coords=[in_gltf(seed.matrix_world@v.co) for v in seed.data.vertices]
assert -1.75<min(v.x for v in coords)<-1.70
assert 1.104<max(v.y for v in coords)<1.106
assert .13<min(v.z for v in coords)<.16

# Deliberately sculpt the actual 76-face closed casting, not a desk, loft or frame.
bm=bmesh.new();bm.from_mesh(seed.data)
bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=9,use_grid_fill=True)
bm.to_mesh(seed.data);bm.free();seed.data.update()
back=seed.matrix_world.inverted()
changed=0
for v in seed.data.vertices:
    p=in_gltf(seed.matrix_world@v.co)
    height=p.y
    if height>=1.079:continue  # original upper contact geometry remains fixed
    dx=p.x+1.267;dz=p.z-.5905
    rr=math.hypot(dx,dz)
    if rr<.01:continue
    ang=math.atan2(dz,dx)
    toward=(-.558*dx+.830*dz)/rr
    exposure=.72+.28*max(-.25,toward)
    near_rim=-.027*math.exp(-((height-1.025)/.024)**2)
    shoulder=.038*math.exp(-((height-.925)/.077)**2)
    waist=-.032*math.exp(-((height-.705)/.145)**2)
    foot=.014*math.exp(-((height-.35)/.10)**2)
    incision_height=.981+.018*math.sin(2.0*ang+.7)
    incision=-.012*math.exp(-((height-incision_height)/.013)**2)*max(0,toward)
    cheek=.024*math.exp(-((height-.958)/.075)**2)*math.exp(-((ang-2.15)/.62)**2)
    delta=(near_rim+shoulder+waist+foot+incision+cheek)*exposure
    p.x+=delta*dx/rr;p.z+=delta*dz/rr
    v.co=back@to_blender(p)
    changed+=1
seed.data.update()
assert changed>200,changed

bpy.ops.object.select_all(action='DESELECT')
seed.hide_select=False;seed.select_set(True)
bpy.context.view_layer.objects.active=seed
bevel=seed.modifiers.new('CAST_TOOL_RADIUS_4MM','BEVEL')
bevel.width=.004;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.56
bpy.ops.object.modifier_apply(modifier=bevel.name)
for p in seed.data.polygons:p.use_smooth=True

# Studio placeholder shaders are explicitly not photographic or PBR-qualified.
def paint(name,base,metal,rough):
    m=bpy.data.materials.new(name);m.diffuse_color=(*base,1);m.use_nodes=True
    shader=m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*base,1)
    shader.inputs['Metallic'].default_value=metal
    shader.inputs['Roughness'].default_value=rough
    return m
cream=paint('STUDY_WARM_CERAMIC_CAST_NO_PHOTO_PBR',(.71,.687,.63),.18,.32)
satin=paint('STUDY_SATIN_INTEGRATED_SHOULDER_NO_PHOTO_PBR',(.23,.27,.29),.72,.29)
dark=paint('STUDY_CLOSED_GRAPHITE_RECESS_NO_PHOTO_PBR',(.045,.054,.062),.34,.45)
seed.data.materials.clear()
for material in (cream,satin,dark):seed.data.materials.append(material)
for p in seed.data.polygons:
    center=in_gltf(seed.matrix_world@p.center)
    c=center-Vector((-1.267,center.y,.5905))
    forward=(-.558*c.x+.830*c.z)/max(.001,math.hypot(c.x,c.z))
    if .994<center.y<1.024 and forward>.0:p.material_index=2
    elif .898<center.y<.95 and forward>-.35:p.material_index=1
    else:p.material_index=0

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.012)
bpy.ops.object.mode_set(mode='OBJECT')
uv0=seed.data.uv_layers.active
assert uv0 is not None
uv0.name='UV0'
uv1=seed.data.uv_layers.new(name='UV1_STUDY_NOT_BAKED')
for i in range(len(seed.data.loops)):uv1.data[i].uv=uv0.data[i].uv
bm=bmesh.new();bm.from_mesh(seed.data)
nonmanifold=sum(1 for edge in bm.edges if not edge.is_manifold)
faces=len(bm.faces);bm.free()
assert nonmanifold==0,('nonmanifold sculpt',nonmanifold)
assert all(signature(x)==before[x.name] for x in locked),'A locked source object changed'
assert seed.data.uv_layers.get('UV0') and seed.data.uv_layers.get('UV1_STUDY_NOT_BAKED')
seed.name='STAGE171_CLOSED_SOURCE_SCULPT_NOT_APPROVED'
seed['ASTERIA_ART_VERDICT']='UNASSESSED — isolation preview only'
seed['SOURCE_COMMAND_SHA256']=EXPECT
seed['PHOTOGRAPHIC_PBR_VERIFIED']=False
scene=bpy.context.scene
scene['ASTERIA_ART_VERDICT']='HOLD / native Blender candidate pending human image inspection'
scene['ASTERIA_FULL_BROWSER_EQUIVALENCE']=False
scene['ASTERIA_RELEASE_AUTHORIZED']=False
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'STAGE171_SCULPT_EDITABLE_UNAPPROVED.blend').resolve()))
scene.cycles.samples=16
scene.view_layers[0].cycles.use_denoising=False
for name,camera,width,height in (
 ('STAGE171_SCULPT_DESKTOP_BLENDER_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',1280,800),
 ('STAGE171_SCULPT_MOBILE_BLENDER_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',390,844),
 ('STAGE171_SCULPT_SIDE_BLENDER_NOT_BROWSER','SCULPT_INSPECTION_SIDE_ONLY',1200,900),
):
    scene.camera=bpy.data.objects[camera]
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.filepath=str((OUT/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
report={'stage':171,'source_sha256':EXPECT,'unmodified_original_meshes':len(locked),
 'reworked_existing_port_geometry':True,'changed_subdivided_vertices':changed,
 'candidate_faces':faces,'nonmanifold_edges':nonmanifold,
 'editable_native_blend':True,'original_source_modified':False,
 'UV0':True,'UV1_STUDY_ONLY_NOT_BAKED':True,'photographic_PBR_qualified':False,
 'isolated_blender_source_preview_only':True,'full_furnished_chromium_and_cycles_AB':False,
 'art_verdict':'HOLD, NOT ACCEPTED','release':False}
(OUT/'stage171-source-sculpt-report.json').write_text(json.dumps(report,indent=2))
print('STAGE171_SOURCE_SCULPT_CREATED',json.dumps(report))
