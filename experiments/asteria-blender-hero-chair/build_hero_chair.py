#!/usr/bin/env python3
"""Original USS Asteria high-fidelity command chair concept asset.
Blender 4.x/5.x headless. Scene renders are quality evidence, not proof of real-time fidelity.
Creates an independently reviewable GLB and three Cycles studio images.
No actual TrekMUD campaign data is accessed, and no existing scene is modified.
"""
import bpy, math, sys, json, argparse, os
from mathutils import Vector
from math import sin, cos, pi

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--out',default='/tmp/asteria-chair');p.add_argument('--samples',type=int,default=32);opt=p.parse_args(args)
os.makedirs(opt.out,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
CH=[]
def track(o):
    if o not in CH:CH.append(o)
    return o

def material(name, color, metal=0.0, rough=.55, bump=.02, scale=170, sheen=0, coat=0):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    for n,v in [('Coat Weight',coat),('Sheen Weight',sheen)]:
      if n in bs.inputs:bs.inputs[n].default_value=v
    if bump:
      nodes=mat.node_tree.nodes;links=mat.node_tree.links
      noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
      noise.inputs['Detail'].default_value=2.6;noise.inputs['Roughness'].default_value=.57
      b=nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.004
      links.new(noise.outputs['Fac'],b.inputs['Height']);links.new(b.outputs['Normal'],bs.inputs['Normal'])
    return mat

leather=material('Asteria / plum fine woven upholstery',(.23,.18,.235),rough=.85,bump=.31,scale=270,sheen=.24)
stitched=material('Asteria / warm mauve seam piping',(.42,.31,.38),rough=.66,bump=.1,scale=230)
shell=material('Asteria / molded satin composite shell',(.16,.155,.20),metal=.07,rough=.35,bump=.06,scale=120,coat=.23)
bronze=material('Asteria / brushed satin rose bronze',(.40,.31,.285),metal=.82,rough=.30,bump=.08,scale=600)
metal=material('Asteria / pewter forged column',(.38,.40,.44),metal=.85,rough=.26,bump=.05,scale=540)
rubber=material('Asteria / control elastomer',(.055,.06,.08),rough=.78,bump=.2,scale=200)
glass=material('Asteria / smoked control glass',(.025,.036,.06),metal=.2,rough=.12,coat=.35)
carpet=material('Asteria / blue-grey carpet stage floor',(.20,.245,.295),rough=.98,bump=.4,scale=440)

def assign(o,mat):o.data.materials.append(mat);return o

def smooth(o):
    if o.type=='MESH':
      for face in o.data.polygons:face.use_smooth=True
    return o

def bevelled_box(name,loc,dims,mat,bevel=.04,segments=5):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=track(bpy.context.object);o.name=name
    o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
      mod=o.modifiers.new('machined rounded edges','BEVEL');mod.width=bevel;mod.segments=segments
      bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    assign(o,mat);return smooth(o)

def cylinder(name,loc,radius,depth,mat,verts=64,scale_x=1,scale_y=1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc)
    o=track(bpy.context.object);o.name=name;o.scale=(scale_x,scale_y,1)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('radius eased edges','BEVEL');bevel.width=min(.022,depth*.22);bevel.segments=4
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bevel.name)
    assign(o,mat);return smooth(o)

def tube(name,points,thickness,mat,res=5):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=24
    curve.bevel_depth=thickness;curve.bevel_resolution=res;curve.resolution_u=20
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for v,pt in zip(spline.points,points):v.co=(*pt,1)
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.convert(target='MESH');obj.select_set(False)
    track(obj);assign(obj,mat);return smooth(obj)

# Capsule-shaped original command-chair back. Orientation: +Y towards aft; -Y faces bridge viewer.
def backpoint(t,u,shift=0):
    # Sculpted shell bends away from the sitter near shoulders and crest.
    shoulder=.50*(.85+.17*sin(pi*t)-.09*t)
    x=shoulder*u*(.98+.02*cos(pi*u))
    z=.81+1.08*t
    y=.255+.23*t+.055*sin(pi*t)-.065*(1-u*u)+shift
    return (x,y,z)

def surface(name,fn,rows,cols,mat,back=False):
    verts=[];faces=[]
    for i in range(rows+1):
      for j in range(cols+1):verts.append(fn(i/rows,-1+2*j/cols))
    for i in range(rows):
      for j in range(cols):
        a=i*(cols+1)+j;b=a+1;c=a+(cols+1);d=c+1
        faces.append((a,c,d,b) if back else (a,b,d,c))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
    track(o);assign(o,mat);return smooth(o)

# Strong silhouette first: continuous high-back outer shell, inner padded face and rolled edge.
surface('AST_Captain_Chair_Outer_CastShell',lambda t,u:backpoint(t,u,.105),60,44,shell,True)
surface('AST_Captain_Chair_Front_Leather',lambda t,u:backpoint(t,u,-.045),60,44,leather,False)
for side in [-1,1]:
    for j in range(48):
       t0=j/48;t1=(j+1)/48
       a=backpoint(t0,side,.105);b=backpoint(t1,side,.105)
       c=backpoint(t1,side,-.045);d=backpoint(t0,side,-.045)
       # Side wall four edges, not loose floating surfaces.
       surface_name=f'AST_Captain_Chair_SideRelief_{side}_{j:02d}'
       me=bpy.data.meshes.new(surface_name);me.from_pydata([a,b,c,d],[],[(0,1,2,3)]);me.update()
       obj=bpy.data.objects.new(surface_name,me);bpy.context.collection.objects.link(obj);track(obj);assign(obj,shell)
    pts=[backpoint(k/72,side,.07) for k in range(73)]
    tube(f'AST_Captain_Chair_Sewn_Back_Edge_{side}',pts,.013,bronze)
    pts=[backpoint(k/72,side*.96,-.050) for k in range(73)]
    tube(f'AST_Captain_Chair_Inner_Piping_{side}',pts,.009,stitched)

# Upholstery hand stitched vertical curved panels; subtle 3D seams, no flat decal.
for u in [-.55,-.26,.26,.55]:
    pts=[backpoint(.05+k*.90/55,u,-.053) for k in range(56)]
    tube(f'AST_Captain_Chair_Upholstery_SewnChannel_{int(u*100)}',pts,.0044,stitched,3)
for t in [.16,.43,.70,.94]:
    pts=[backpoint(t,-.85+k*1.7/46,-.055) for k in range(47)]
    tube(f'AST_Captain_Chair_Upholstery_CrossSeam_{int(t*100)}',pts,.004,stitched,2)

# Twin cushion rolls at lumbar and head support; seat pan has human-scale recess.
bevelled_box('AST_Captain_Chair_Seat_Cast_Pan',(0,-.12,.63),(1.06,.90,.22),shell,.10,9)
bevelled_box('AST_Captain_Chair_Seat_Padded_Leather',(0,-.13,.727),(.96,.81,.20),leather,.095,10)
bevelled_box('AST_Captain_Chair_Headrest_Leather',(0,.48,1.76),(.70,.14,.21),leather,.077,10)
bevelled_box('AST_Captain_Chair_Headrest_Trim',(0,.55,1.77),(.69,.035,.17),bronze,.012,5)

# Independent gracefully curved arm supports, with physically seated inset touchpads.
for sign in [-1,1]:
    x=sign*.595
    tube(f'AST_Captain_Chair_Forged_Armature_{sign}',[(x,.31,.36),(x,.25,.66),(x,.08,.88),(x,-.35,.90),(x,-.45,.79)],.044,metal)
    bevelled_box(f'AST_Captain_Chair_Armrest_Leather_{sign}',(x,-.16,.925),(.19,.61,.115),leather,.047,8)
    bevelled_box(f'AST_Captain_Chair_Arm_ControlScreen_{sign}',(x,-.20,.992),(.115,.33,.015),glass,.006,4)
    for j in range(7):
       mat=material(f'AST_Indicator_{sign}_{j}',(.09+(j%3)*.20,.24+(j%2)*.17,.33),rough=.8)
       bevelled_box(f'AST_Captain_Chair_Control_Key_{sign}_{j}',(x,-.32+j*.05,1.007),(.07,.026,.010),mat,.004,3)

# Independent broad base, foot bearings and concealed column.
cylinder('AST_Captain_Chair_Cast_Pedestal',(0,.035,.11),.30,.22,metal,80)
cylinder('AST_Captain_Chair_Bearing_Sleeve',(0,.035,.28),.17,.13,bronze,64)
cylinder('AST_Captain_Chair_Swivel_Column',(0,.035,.43),.094,.31,metal,56)
for sign in [-1,1]:
    bevelled_box(f'AST_Captain_Chair_Stabilizer_Foot_{sign}',(sign*.28,-.06,.14),(.32,.40,.055),shell,.018,4)

# A subtle aft service seam and rear decorative lugs are grounded in the shell.
for j in range(9):
    x=-.27+j*.0675;y=.476;z=1.12
    cylinder(f'AST_Captain_Chair_Cast_Inspection_Dot_{j}',(x,y,z),.012,.015,bronze,18)

# Minimal stage ONLY for rendering; excluded from GLB export.
bevelled_box('STUDIO_floor',(0,0,-.075),(7,7,.15),carpet,.012,3)
# Camera views use measured chair dimensions but are studio composition previews.
def target_camera(name,loc,target,lens=46):
    camera=bpy.data.objects.get('STUDIO_camera')
    if not camera:
      bpy.ops.object.camera_add(location=loc);camera=bpy.context.object;camera.name='STUDIO_camera';bpy.context.scene.camera=camera
    camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='PERSP';camera.data.lens=lens

def area(name,loc,energy,color,shape,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((0,0,1.0))-o.location).to_track_quat('-Z','Y').to_euler()

area('STUDIO_key_softbox',(-3.2,3.8,5.5),700,(1.0,.83,.72),'DISK',5)
area('STUDIO_fill_panel',(3.7,-2.0,4.1),530,(.70,.80,1.0),'DISK',4)
area('STUDIO_overhead_softbox',(0,0,5.8),330,(1.0,.96,.91),'DISK',4.3)
area('STUDIO_rim_light',(2.3,3.1,3.8),180,(1.0,.68,.47),'DISK',2.8)
world=bpy.context.scene.world or bpy.data.worlds.new('Asteria studio environment')
world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.19,.21,.26,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
bpy.context.scene.world=world
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=opt.samples
# The Ubuntu Blender package has no OpenImageDenoiser; use raw CPU Cycles.
if hasattr(scene.cycles,'use_denoising'):scene.cycles.use_denoising=False
scene.render.resolution_x=1180;scene.render.resolution_y=790;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
try:scene.view_settings.view_transform='AgX'
except Exception:scene.view_settings.view_transform='Filmic'
try:scene.view_settings.look='Medium High Contrast'
except Exception:pass
# glTF chairs only, never export light fixtures/floor/camera.
bpy.ops.object.select_all(action='DESELECT')
for o in CH:
    if o and o.name in bpy.data.objects:o.select_set(True)
if CH:bpy.context.view_layer.objects.active=CH[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(opt.out,'asteria-command-chair.glb'),export_format='GLB',use_selection=True)
bpy.ops.object.select_all(action='DESELECT')

for view,loc,target,lens in [
 ('aft',(2.5,4.3,2.23),(0,0,1.02),43),
 ('front',(-2.4,-3.9,2.05),(0,0,1.05),43),
 ('side',(3.4,.25,1.92),(0,.10,1.02),48),
]:
    target_camera('STUDIO_camera',loc,target,lens)
    scene.render.filepath=os.path.join(opt.out,f'chair-{view}.png')
    bpy.ops.render.render(write_still=True)

report={'model':'USS ASTERIA original captain chair', 'room':'AST-D01-BRIDGE','stage':'experimental authored asset',
        'blender_version':bpy.app.version_string,'chair_objects':len(CH), 'render_samples':opt.samples,
        'outputs':['asteria-command-chair.glb','chair-aft.png','chair-front.png','chair-side.png'],
        'warning':'Rendered Cycles source stills are NOT the same as real-time browser glTF output.'}
with open(os.path.join(opt.out,'manifest.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))