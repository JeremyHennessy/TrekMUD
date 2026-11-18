"""Stage174: bespoke carved pressure-saddle art STUDY for exact original port console.

Isolated source-only native Blender, not the browser/game or production asset.
Only the replaceable 76-face port casting duplicate is changed. All original 89
other meshes, approved control glass, switches and original cameras are locked.

This art study deliberately DISCARDS the rejected cabinet/shelf/triangular
web approach. One source-fitted curved pressure hull is sculpted from an
authored station-by-station section drawing. Deep geometric load-channel
reliefs turn inward rather than project shelves/arms outside the source rim.
The cavity is backed by solid structural material, so protected service
components are never exposed. Material studies are NOT photographic PBR.
"""
import bpy
import bmesh
import hashlib
import json
import math
from pathlib import Path
from mathutils import Matrix, Vector

OUT=Path('_stage168/output')
OUT.mkdir(parents=True,exist_ok=True)
STUDIO=OUT/'ASTERIA_STAGE168_ORIGINAL_SOURCE_STUDIO_UNAPPROVED.blend'
assert STUDIO.is_file()
bpy.ops.wm.open_mainfile(filepath=str(STUDIO.resolve()))
SOURCE='9b988aaec53afa557011e5cba1addc19b1de6bf8f5d8bb6a7edc560ae8452f1c'
locked=[o for o in bpy.data.collections['01_LOCKED_ORIGINAL_89_MESHES'].objects if o.type=='MESH']
seed=bpy.data.objects['EDITABLE_STUDY_ONLY_ORIGINAL_76_FACE_SEED']
assert len(locked)==89 and len(seed.data.polygons)==76
assert all(o.get('ASTERIA_SOURCE_SHA256')==SOURCE for o in locked)

def signature(obj):
    h=hashlib.sha256()
    for v in obj.data.vertices:
        h.update(('%.9g %.9g %.9g;'%tuple(v.co)).encode())
    for poly in obj.data.polygons:
        h.update((','.join(map(str,poly.vertices))+';').encode())
    h.update('|'.join(m.name for m in obj.data.materials if m).encode())
    return h.hexdigest()
locked_before={o.name:signature(o) for o in locked}

def g2b(x,y,z):
    return (x,-z,y)
def b2g(v):
    return (v.x,v.z,-v.y)
def material(name,base,metal,rough):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*base,1)
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*base,1)
    bs.inputs['Metallic'].default_value=metal
    bs.inputs['Roughness'].default_value=rough
    return m

# Material choices are visually judged studies; NONE are photo-scan qualified.
mats=[
    material('174_DEEP_SMOKED_GRAPHITE_NONPHOTO_STUDY',(.055,.069,.079),.42,.32),
    material('174_WARM_LIGHT_CERAMIC_PRESSURE_SHOULDER_NONPHOTO',(.53,.54,.54),.18,.32),
    material('174_MACHINED_SATIN_TITANIUM_LOAD_CHANNEL_NONPHOTO',(.21,.25,.27),.71,.25),
    material('174_DARK_RECESSED_SERVICING_SHADE_NONPHOTO',(.023,.033,.041),.30,.48),
]

# Hand-drawn 3D longitudinal design stations, in the SOURCE GLB's
# [x horizontal, y vertical, z depth] metric frame.
# Each station: (height, horizontal centre, half width, depth centre,
#                half depth). No external slab, free bracket or shelf.
# The full top section bears under the actual untouched instrument rim.
sections=[
    (.276,-1.300,.190,.613,.240),
    (.355,-1.302,.197,.606,.265),
    (.482,-1.308,.206,.601,.280),
    (.606,-1.307,.220,.596,.294),
    (.732,-1.295,.263,.593,.322),
    (.838,-1.288,.305,.595,.358),
    (.916,-1.279,.355,.602,.384),
    (.976,-1.278,.393,.602,.406),
    (1.017,-1.277,.412,.604,.416),
    (1.044,-1.275,.415,.604,.421),
    (1.063,-1.274,.416,.603,.422),
]
assert all(sections[i][0]<sections[i+1][0] for i in range(len(sections)-1))
N=80
# Use source-fitting rounded-square sections instead of office-rectangular
# panels. Designed left and forward sculpt pockets flow out under the rim.
def spow(v,p):
    return math.copysign(abs(v)**p,v)
def bell(a,mu,sigma):
    d=(a-mu+math.pi)%(2*math.pi)-math.pi
    return math.exp(-(d/sigma)**2)
vertices=[]
for y,cx,hw,cz,hd in sections:
    for j in range(N):
        theta=math.tau*j/N
        xx=spow(math.cos(theta),.79)
        zz=spow(math.sin(theta),.79)
        x=cx+hw*xx
        z=cz+hd*zz
        # Real swept negative-space geometry carved INTO the closed shell:
        # camera-facing left saddle relief, strongest in the visible upper
        # half; gentle service return at the forward corner.
        pocket=bell(theta,math.pi,.51)*math.exp(-((y-.836)/.184)**2)
        fore=bell(theta,math.pi/2,.55)*math.exp(-((y-.864)/.155)**2)
        x+=.101*pocket
        z-=.061*fore
        # Broad actual load-shoulder, integral and tucked BELOW control rim.
        # This subtle outward flare starts immediately at the upper contact.
        shoulder=math.exp(-((y-1.041)/.031)**2)
        x+=(.008*shoulder if xx>0 else -.008*shoulder)
        z+=(.006*shoulder if zz>0 else -.006*shoulder)
        vertices.append(g2b(x,y,z))
faces=[]
materials=[]
# Closed lower cap; top cap is closed and fully BELOW the protected buttons.
faces.append(tuple(reversed(range(N))))
materials.append(0)
for k in range(len(sections)-1):
    y0=sections[k][0];y1=sections[k+1][0]
    for j in range(N):
        nxt=(j+1)%N
        faces.append((k*N+j,k*N+nxt,(k+1)*N+nxt,(k+1)*N+j))
        th=math.tau*(j+.5)/N
        is_left=bell(th,math.pi,.51)>.32 and .66<y1<.997
        is_front=bell(th,math.pi/2,.55)>.38 and .71<y1<.98
        if y0>=1.017:
            materials.append(2)
        elif y0>=.976:
            materials.append(1)
        elif is_left:
            materials.append(3)
        elif is_front:
            materials.append(2)
        else:
            materials.append(0)
faces.append(tuple((len(sections)-1)*N+j for j in range(N)))
materials.append(2)
assert len(faces)==len(materials)

mesh=bpy.data.meshes.new('174_PRESSURE_SADDLE_SCULPT_EDITABLE_SOURCE_MESH')
mesh.from_pydata(vertices,[],faces)
mesh.update()
for m in mats:
    mesh.materials.append(m)
for p,idx in zip(mesh.polygons,materials):
    p.material_index=idx
    p.use_smooth=(len(p.vertices)==4)
bm=bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
mesh.update()

seed.data=mesh
seed.matrix_world=Matrix.Identity(4)
seed.name='STAGE174_SCULPTURAL_PRESSURE_SADDLE_ART_HOLD'
bpy.ops.object.select_all(action='DESELECT')
seed.hide_select=False
seed.select_set(True)
bpy.context.view_layer.objects.active=seed
# Manufactured 4mm edge roll restricted to actual structural sharp edges,
# not decorative repetitive bands.
bevel=seed.modifiers.new('174_MANUFACTURED_STRUCTURAL_EDGE_RADIUS','BEVEL')
bevel.width=.004
bevel.segments=3
bevel.limit_method='ANGLE'
bevel.angle_limit=.65
bpy.ops.object.modifier_apply(modifier=bevel.name)
bm=bmesh.new()
bm.from_mesh(seed.data)
bm.verts.ensure_lookup_table()
seen=set();shells=0
for v in bm.verts:
    if v.index in seen:
        continue
    shells+=1
    todo=[v]
    while todo:
        cur=todo.pop()
        if cur.index in seen:
            continue
        seen.add(cur.index)
        todo.extend(e.other_vert(cur) for e in cur.link_edges if e.other_vert(cur).index not in seen)
nonmanifold=sum(not edge.is_manifold for edge in bm.edges)
face_count=len(bm.faces)
bm.free()
assert shells==1,('DISCONNECTED_SOURCE_HULL',shells)
assert nonmanifold==0,('NONMANIFOLD_SOURCE_HULL',nonmanifold)

# Ensure actual source-fit: all experimental sculpt points remain below
# instrument rim, and inside measured source footprint, with no giant wings.
points=[b2g(seed.matrix_world@v.co) for v in seed.data.vertices]
mins=[min(p[i] for p in points) for i in range(3)]
maxs=[max(p[i] for p in points) for i in range(3)]
assert mins[0]>-1.735 and maxs[0]<-.79,(mins,maxs)
assert mins[1]>.25 and maxs[1]<1.078,(mins,maxs)
assert mins[2]>.13 and maxs[2]<1.06,(mins,maxs)
assert all(signature(o)==locked_before[o.name] for o in locked),'PROTECTED_89_MESH_CHANGE'

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.011)
bpy.ops.object.mode_set(mode='OBJECT')
uv0=seed.data.uv_layers.active
assert uv0 is not None
uv0.name='UV0'
uv1=seed.data.uv_layers.new(name='UV1_UNBAKED_STUDY')
for i in range(len(seed.data.loops)):
    uv1.data[i].uv=uv0.data[i].uv
assert len(seed.data.uv_layers)==2
seed['SOURCE_SHA256']=SOURCE
seed['ART_NOT_APPROVED']=True
seed['SOURCE_ONLY_NO_BROWSER']=True
seed['PHOTOGRAPHIC_PBR_QUALIFIED']=False
scene=bpy.context.scene
scene['ASTERIA_ART_VERDICT']='HOLD - judge authentic source camera desktop and mobile'
scene['ASTERIA_RELEASE_AUTHORIZED']=False
scene['ASTERIA_BROWSER_RUNTIME_TESTED']=False
path=OUT/'STAGE174_EDITABLE_PRESSURE_SADDLE_UNAPPROVED.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()))
scene.cycles.samples=16
scene.view_layers[0].cycles.use_denoising=False
for name,cam,w,h in [
    ('STAGE174_DESKTOP_NATIVE_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',1280,800),
    ('STAGE174_MOBILE_NATIVE_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',390,844),
    ('STAGE174_SIDE_NATIVE_NOT_BROWSER','SCULPT_INSPECTION_SIDE_ONLY',1200,900)]:
    scene.camera=bpy.data.objects[cam]
    scene.render.resolution_x=w
    scene.render.resolution_y=h
    scene.render.resolution_percentage=100
    scene.render.filepath=str((OUT/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
report={
    'stage':174,'editable_original_mesh':52,'locked_original_meshes_identical':89,
    'candidate_faces':face_count,'connected_shells':shells,
    'nonmanifold_edges':nonmanifold,'source_fit_min':mins,'source_fit_max':maxs,
    'UV0':True,'UV1_UNBAKED':True,'photographic_pbr_qualified':False,
    'browser_ab_verified':False,'art_verdict':'HOLD: genuine visual A/B required',
    'release':False,'source_sha256':SOURCE,
    'design':'Authored seamless dark-pressure-hull saddle, inward sculpted near-rim relieved channels, fully shielded service return'
}
(OUT/'stage174-report.json').write_text(json.dumps(report,indent=2))
print('STAGE174_UNAPPROVED_NATIVE_SCULPT_REPORT',json.dumps(report))
