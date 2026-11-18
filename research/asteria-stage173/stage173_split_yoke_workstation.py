"""Stage173 art-directed split-yoke experimental port command workstation.

ONE editable substitute for the 76-face source casting. Stage168 locks the other
89 original source meshes, the screen/controls, source cameras and the game.
This is source-only Cycles; NOT the playable bridge or an accepted product asset.
Material surfaces are intentionally unqualified studies; no photo-PBR assertion.
"""
import bpy, bmesh, hashlib, json, math
from pathlib import Path
from mathutils import Vector, Matrix

OUT=Path('_stage168/output')
OUT.mkdir(exist_ok=True,parents=True)
STUDIO=OUT/'ASTERIA_STAGE168_ORIGINAL_SOURCE_STUDIO_UNAPPROVED.blend'
assert STUDIO.is_file(), 'Pinned Stage168 native Blender source is unavailable'
bpy.ops.wm.open_mainfile(filepath=str(STUDIO.resolve()))
SEED=bpy.data.objects['EDITABLE_STUDY_ONLY_ORIGINAL_76_FACE_SEED']
LOCKED=[x for x in bpy.data.collections['01_LOCKED_ORIGINAL_89_MESHES'].objects if x.type=='MESH']
assert len(LOCKED)==89 and len(SEED.data.polygons)==76
SOURCE='9b988aaec53afa557011e5cba1addc19b1de6bf8f5d8bb6a7edc560ae8452f1c'
assert all(x['ASTERIA_SOURCE_SHA256']==SOURCE for x in LOCKED)
def signature(ob):
    h=hashlib.sha256()
    for v in ob.data.vertices:
        h.update(('%.9g %.9g %.9g;' % tuple(v.co)).encode())
    for poly in ob.data.polygons:
        h.update((','.join(map(str,poly.vertices))+';').encode())
    h.update('|'.join(m.name for m in ob.data.materials if m).encode())
    return h.hexdigest()
prior={o.name:signature(o) for o in LOCKED}
def B(x,y,z): return (x,-z,y)
def G(v): return (v.x,v.z,-v.y)
def mat(name,rgb,metal,rough):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*rgb,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Metallic'].default_value=metal
    p.inputs['Roughness'].default_value=rough
    return m
mats=[
    mat('173_BRUSHED_GRAPHITE_INTERIOR_STUDY_NOT_PHOTO_PBR',(.047,.057,.069),.65,.37),
    mat('173_PAINTED_CERAMIC_YOKE_STUDY_NOT_PHOTO_PBR',(.73,.725,.690),.30,.28),
    mat('173_SATIN_TITANIUM_NEAR_RIM_STUDY_NOT_PHOTO_PBR',(.26,.31,.34),.78,.24)]
# This design uses two hand-drawn curved structural *plates*, not a shelf,
# beam ring, exposed pipe, grooved cabinet, or Stage172 CSG cavity.
# The left plate is a true arch in the (y,z) plane, tapered into the source rim.
# The front plate is a different bowed load-web in the (x,y) plane.
# A slim dark shield, located behind both, hides protected service apparatus.
def meshobj(name,verts,faces,material):
    mesh=bpy.data.meshes.new(name+'_editable_mesh')
    mesh.from_pydata([B(*v) for v in verts],[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:mesh.materials.append(m)
    for poly in mesh.polygons:poly.material_index=material
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();mesh.update()
    return ob
def plate(name,polygon,plane,a,b,material):
    # Each true concave profile is a closed welded plate with a sculpted
    # load-bearing outline. Its opening is not an applied decorative groove.
    n=len(polygon)
    if plane=='YZ':
        v=[(x,y,z) for x in (a,b) for (y,z) in polygon]
    else:
        v=[(x,y,z) for z in (a,b) for (x,y) in polygon]
    f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    for i in range(n):
        j=(i+1)%n
        f.append((i,j,n+j,n+i))
    return meshobj(name,v,f,material)
def shield(name,rows):
    # Hand-shaped chamfered, continuously narrowed graphite service screen.
    # Width and depth are derived from the original 76-face source footprint.
    v=[]
    for y,cx,w,zlo,zhi in rows:
        ch=min(.033,w*.27,(zhi-zlo)*.22)
        ring=[(cx-w+ch,zlo),(cx+w-ch,zlo),(cx+w,zlo+ch),
              (cx+w,zhi-ch),(cx+w-ch,zhi),(cx-w+ch,zhi),
              (cx-w,zhi-ch),(cx-w,zlo+ch)]
        v.extend([(x,y,z) for x,z in ring])
    n=8
    f=[tuple(range(n-1,-1,-1))]
    for k in range(len(rows)-1):
        for i in range(n):
            j=(i+1)%n
            f.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    f.append(tuple((len(rows)-1)*n+i for i in range(n)))
    return meshobj(name,v,f,0)
pieces=[]
# Shadowed service shield sits behind both visible braces. Unbroken body is
# intentional: the known locked rear door/toe cannot be exposed by cutouts.
pieces.append(shield('173_RECESSED_GRAPHITE_SERVICE_SHIELD',[
    (.245,-1.275,.145,.50,.82),
    (.35,-1.290,.156,.50,.83),
    (.55,-1.280,.165,.495,.84),
    (.78,-1.255,.235,.445,.87),
    (.985,-1.270,.305,.392,.935),
    (1.045,-1.270,.344,.36,.970)]))
# Left large under-rim tension arch, designed as a tapered, *open* C/S blade.
# Its concave inner return makes a source-visible deep recess at camera-facing
# left x=-1.70 instead of the previous full cream office-cabinet side.
pieces.append(plate('173_LEFT_CRESCENT_LOAD_WEB',[
    (.275,.575),(.38,.54),(.57,.57),(.745,.655),
    (.885,.782),(1.011,.90),(1.066,.944),
    (1.064,.31),(1.041,.268),(.985,.32),
    (.941,.395),(.850,.493),(.710,.542),
    (.525,.49),(.348,.44),(.273,.465)
], 'YZ',-1.713,-1.617,1))
# Front web pulls from the untouched command rim toward a centrally anchored
# load spine; front face is intentionally much narrower below the rim.
pieces.append(plate('173_FRONT_DIAGONAL_LOAD_WEB',[
    (-1.655,1.064),(-1.025,1.064),(-1.014,1.028),
    (-1.145,.969),(-1.252,.851),(-1.323,.724),
    (-1.353,.544),(-1.339,.260),(-1.456,.260),
    (-1.459,.522),(-1.505,.724),(-1.589,.875),
    (-1.678,.968)
], 'XY',.938,1.029,1))
# Structural under-rim sleeve; barely extends below controls, no projecting
# shelf or giant overhang. Ties both broad webs directly to upper load surface.
pieces.append(shield('173_THIN_ABOVE_WEB_UPPER_CONTACT',[
    (1.007,-1.271,.402,.30,1.020),
    (1.064,-1.271,.416,.284,1.040)]))
for poly in pieces[-1].data.polygons: poly.material_index=2
# Compact base interface joins the yoke arms without table-like feet.
pieces.append(shield('173_CENTRAL_LOW_THRUST_ANCHOR',[
    (.225,-1.315,.175,.49,.865),
    (.333,-1.305,.195,.48,.868)]))
for poly in pieces[-1].data.polygons: poly.material_index=1
# Work only on the editable source duplicate, never alter the 89 originals.
SEED.data=bpy.data.meshes.new('STAGE173_SCULPT_UNIFIED_MESH')
SEED.matrix_world=Matrix.Identity(4)
for m in mats: SEED.data.materials.append(m)
first=pieces.pop(0)
SEED.data=first.data.copy()
bpy.data.objects.remove(first,do_unlink=True)
# Preserve material layout across EXACT union.
for piece in pieces:
    assert [m.name for m in piece.data.materials]==[m.name for m in SEED.data.materials]
    mod=SEED.modifiers.new('STAGE173_STRUCTURE_UNION_'+piece.name,'BOOLEAN')
    mod.operation='UNION'
    mod.solver='EXACT'
    mod.object=piece
    bpy.context.view_layer.objects.active=SEED
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(piece,do_unlink=True)
# Small manufactured edge radii on genuinely curved structure, never
# ornamental horizontal strips or exposed pipes.
bpy.ops.object.select_all(action='DESELECT')
SEED.select_set(True)
bpy.context.view_layer.objects.active=SEED
bevel=SEED.modifiers.new('173_ENGINEERED_EDGE_8MM','BEVEL')
bevel.width=.008
bevel.segments=3
bevel.limit_method='ANGLE'
bevel.angle_limit=.49
bpy.ops.object.modifier_apply(modifier=bevel.name)
# If a union fails to connect, the manifold report is not enough: report count
# of independent shells. Reject any split disconnected floating geometry.
bm=bmesh.new();bm.from_mesh(SEED.data)
bm.verts.ensure_lookup_table()
seen=set();shells=0
for v in bm.verts:
    if v.index in seen: continue
    shells+=1
    stack=[v]
    while stack:
        cur=stack.pop()
        if cur.index in seen:continue
        seen.add(cur.index)
        for e in cur.link_edges:
            nxt=e.other_vert(cur)
            if nxt.index not in seen:stack.append(nxt)
nonmanifold=sum(not e.is_manifold for e in bm.edges)
face_count=len(bm.faces)
bm.free()
assert shells==1,('Art source has floating disconnected geometry',shells)
assert nonmanifold==0,('Art source not manifold',nonmanifold)
# Actual UV0/UV1 layout is for study only; UV1 not lightmap baked.
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(island_margin=.009)
bpy.ops.object.mode_set(mode='OBJECT')
uv=SEED.data.uv_layers.active
assert uv is not None
uv.name='UV0'
uv1=SEED.data.uv_layers.new(name='UV1_STUDY_UNBAKED')
for i in range(len(SEED.data.loops)):uv1.data[i].uv=uv.data[i].uv
assert all(signature(o)==prior[o.name] for o in LOCKED), 'PROTECTED_ORIGINAL_89_CHANGED'
ys=[G(SEED.matrix_world@v.co)[1] for v in SEED.data.vertices]
assert max(ys)<1.081,('SEED EXTENDS INTO PROTECTED CONTROL',max(ys))
SEED.name='STAGE173_SPLIT_YOKE_FLAGSHIP_ART_HOLD'
SEED['SOURCE_SHA256']=SOURCE
SEED['ART_NOT_APPROVED']=True
SEED['NO_PHOTOGRAPHIC_PBR']=True
scene=bpy.context.scene
scene['ASTERIA_ART_VERDICT']='HOLD: real desktop+mobile imagery must be judged'
scene['ASTERIA_RELEASE_AUTHORIZED']=False
scene['ASTERIA_IS_BROWSER_SCENE']=False
blend=OUT/'STAGE173_SPLIT_YOKE_EDITABLE_UNAPPROVED.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
scene.cycles.samples=16
scene.view_layers[0].cycles.use_denoising=False
for name,cam,w,h in [
    ('STAGE173_DESKTOP_NATIVE_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',1280,800),
    ('STAGE173_MOBILE_NATIVE_NOT_BROWSER','ORIGINAL_COMMAND_POSE_DO_NOT_MOVE',390,844),
    ('STAGE173_SIDE_NATIVE_NOT_BROWSER','SCULPT_INSPECTION_SIDE_ONLY',1200,900)]:
    scene.camera=bpy.data.objects[cam]
    scene.render.resolution_x=w
    scene.render.resolution_y=h
    scene.render.resolution_percentage=100
    scene.render.filepath=str((OUT/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
report={'stage':173,'source_sha256':SOURCE,'locked_original_meshes_identical':89,
  'editable_source_meshes':1,'connected_shells':shells,'candidate_faces':face_count,
  'nonmanifold_edges':nonmanifold,'UV0':True,'UV1_UNBAKED':True,
  'photographic_pbr_qualified':False,'browser_ab_verified':False,
  'release':False,'art_verdict':'HOLD pending genuine source-camera desktop/mobile/side art judgement',
  'design':'Art-directed split-yoke structural web with recessed solid service shield. No shelves, decorative trim or pipes.'}
(OUT/'stage173-report.json').write_text(json.dumps(report,indent=2))
print('STAGE173_NATIVE_STUDY_ONLY',json.dumps(report))
