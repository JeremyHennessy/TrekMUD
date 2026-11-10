#!/usr/bin/env python3
"""Model USS Asteria's exact-fit command platform + two console pylons in Blender.

Independent, NON-PRODUCTION 3D asset. Source footprint, furniture and frozen
V3 model/room IDs are preserved. The PBR screens use original V3 atlas pixels.
Sample:
 blender -b -t 4 --python-exit-code 1 --python scripts/asteria_command_blender.py -- \
   --out _asteria_command_01 --materials _asteria_command_maps --samples 32 \
   --view all --bake-ao

Cycles ambient occlusion is baked on the **command carpet top only**, and
exported as a glTF occlusion texture on UV1 if supported by the Blender addon.
This is contact AO, not a full Cycles multi-bounce global-illumination bake.
"""
from __future__ import annotations
import argparse,json,math,sys,hashlib
from pathlib import Path

import bpy
from mathutils import Vector

PI=math.pi
CMD_ROOM="AST-D01-BRIDGE"
ORIGINAL_V3="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"

def xyz(x,y,z):
    """Room glTF Y-up (x,y,z) -> Blender Z-up (x,-z,y)."""
    return Vector((x,-z,y))

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--materials",type=Path,required=True)
    p.add_argument("--samples",type=int,default=32)
    p.add_argument("--view",choices=["aft","command","console","overhead","all"],default="all")
    p.add_argument("--resolution",nargs=2,type=int,default=[1000,700])
    p.add_argument("--bake-ao",action="store_true")
    p.add_argument("--correct-screen-uv",action="store_true",help="A/B corrected V3 console text orientation")
    p.add_argument("--no-render",action="store_true")
    p.add_argument("--stage32-cast-support",action="store_true",help="Opt-in isolated Stage32 art only")
    return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def put(ob):
    for collection in tuple(ob.users_collection):collection.objects.unlink(ob)
    COMMAND.objects.link(ob)
    return ob

def model(name,vertices,faces,material,uvs=None):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(xyz(*v)) for v in vertices],[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    COMMAND.objects.link(obj)
    mesh.materials.append(material)
    for f in mesh.polygons:
        f.use_smooth=True
    if uvs:
        uv=mesh.uv_layers.new(name="AST_PBR_UV")
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                index=mesh.loops[li].vertex_index
                uv.data[li].uv=uvs[index]
    return obj

def box(name,origin,extent,material,roundover=.018,rotation=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(*origin))
    ob=put(bpy.context.object);ob.name=name
    # Original depth (Z) maps to Blender's Y axis.
    ob.dimensions=(extent[0],extent[2],extent[1])
    ob.rotation_euler.z=-rotation
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    b=ob.modifiers.new("Manufactured edge radius","BEVEL")
    b.width=min(roundover,extent[0]/3,extent[1]/3,extent[2]/3)
    b.segments=4
    ob.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return ob

def lathe(name,layers,material,center_z=1.11,count=128):
    """Layered oval moulded cast piece at fixed V3 y/rx/rz positions."""
    verts=[]
    for y,rx,rz in layers:
        for i in range(count):
            a=2*PI*i/count
            verts.append((rx*math.cos(a),y,center_z+rz*math.sin(a)))
    faces=[]
    for ring in range(len(layers)-1):
        for i in range(count):
            j=(i+1)%count;a=ring*count+i;b=ring*count+j
            c=(ring+1)*count+i;d=(ring+1)*count+j
            faces.extend([(a,b,c),(b,d,c)])
    for i in range(1,count-1):
        faces.append((0,i+1,i))
    end=(len(layers)-1)*count
    for i in range(1,count-1):
        faces.append((end,end+i,end+i+1))
    return model(name,verts,faces,material)

def disk(name,y,rx,rz,material,count=160):
    verts=[(0,y,1.11)]
    for i in range(count):
        a=2*PI*i/count
        verts.append((rx*math.cos(a),y,1.11+rz*math.sin(a)))
    faces=[(0,1+(i+1)%count,1+i) for i in range(count)]
    uvs=[((x+2)/4,(z+.65)/3.5) for x,_,z in verts]
    ob=model(name,verts,faces,material,uvs)
    # Dedicated UV1 for baked AO. This has zero overlapping area on the
    # top polygon, unlike projecting every object into a shared UV atlas.
    uv=ob.data.uv_layers.new(name="AST_BAKED_AO_UV")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            index=ob.data.loops[li].vertex_index
            uv.data[li].uv=uvs[index]
    return ob

def pipe(name,points,r,material,segments=3):
    cu=bpy.data.curves.new(name,"CURVE")
    cu.dimensions="3D";cu.bevel_depth=r;cu.bevel_resolution=segments
    sp=cu.splines.new("POLY");sp.points.add(len(points)-1)
    for v,p in zip(sp.points,points):
        v.co=(*xyz(*p),1)
    cu.materials.append(material)
    ob=bpy.data.objects.new(name,cu);COMMAND.objects.link(ob)
    return ob

def rod(name,start,end,r,material):
    p=xyz(*start);q=xyz(*end)
    length=(q-p).length
    if length<.001:raise ValueError("Rod must have length")
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=length,location=(p+q)/2)
    ob=put(bpy.context.object);ob.name=name
    ob.rotation_euler=(q-p).to_track_quat("Z","Y").to_euler()
    ob.data.materials.append(material)
    for polygon in ob.data.polygons:polygon.use_smooth=True
    return ob

def bolt(name,x,y,z,material,r=.011):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=.008,location=xyz(x,y,z))
    ob=put(bpy.context.object);ob.name=name
    ob.data.materials.append(material)
    return ob

def build_material(name,source,rough,metal,root):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value=rough
    bsdf.inputs["Metallic"].default_value=metal
    files={k:root/(source+"_"+k+".png") for k in ("base","normal","orm")}
    for path in files.values():
        if not path.is_file():raise FileNotFoundError(path)
    for key,path in files.items():
        image=bpy.data.images.load(str(path.resolve()),check_existing=True)
        if key!="base":image.colorspace_settings.name="Non-Color"
        image.pack()
        tex=mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image=image
        tex.label="Original Asteria PBR "+key
        tex.extension="REPEAT"
        if key=="base":
            mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
        elif key=="normal":
            n=mat.node_tree.nodes.new("ShaderNodeNormalMap")
            n.inputs["Strength"].default_value=.38
            mat.node_tree.links.new(tex.outputs["Color"],n.inputs["Color"])
            mat.node_tree.links.new(n.outputs["Normal"],bsdf.inputs["Normal"])
        elif key=="orm":
            sep=mat.node_tree.nodes.new("ShaderNodeSeparateColor")
            sep.mode="RGB"
            mat.node_tree.links.new(tex.outputs["Color"],sep.inputs["Color"])
            mat.node_tree.links.new(sep.outputs["Green"],bsdf.inputs["Roughness"])
            mat.node_tree.links.new(sep.outputs["Blue"],bsdf.inputs["Metallic"])
    return mat

def display_material(name,texture_file):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value=0.
    bsdf.inputs["Roughness"].default_value=.35
    tex=m.node_tree.nodes.new("ShaderNodeTexImage")
    image=bpy.data.images.load(str(texture_file.resolve()),check_existing=True)
    image.pack()
    tex.image=image
    m.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        m.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value=.4
    return m

def make_pylon(side,mats,correct_screen_uv=False,stage32=False):
    """Exact-position closed composite electronics pedestal: ±1.27, z=.58."""
    x0=side*1.27;z0=.58;rot=side*.24
    co,si=math.cos(rot),math.sin(rot)
    def P(a,y,b):
        return (x0+a*co-b*si,y,z0+a*si+b*co)
    if stage32:
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from asteria_stage32_command_asset import build as build_stage32
        build_stage32(side,model,pipe,mats)
    else:
        # Eight-corner tapered pressure-formed housing with rounded planar corners.
        profiles=[(.266,.31,.310,.330),(.322,.362,.359,.380),(.94,.390,.372,.395),
                  (1.077,.372,.375,.375),(1.105,.365,.372,.375)]
        verts=[]
        for h,w,forward,rear in profiles:
            r=.061
            corners=[(-w+r,-forward),(w-r,-forward),(w,-forward+r),
                     (w,rear-r),(w-r,rear),(-w+r,rear),
                     (-w,rear-r),(-w,-forward+r)]
            verts.extend(P(a,h,b) for a,b in corners)
        faces=[]
        for layer in range(len(profiles)-1):
            for j in range(8):
                v=layer*8+j;n=layer*8+(j+1)%8
                u=(layer+1)*8+j;o=(layer+1)*8+(j+1)%8
                faces.extend(((v,n,u),(n,o,u)))
        for j in range(1,7):
            faces.append((0,j+1,j))
            end=(len(profiles)-1)*8
            faces.append((end,end+j,end+j+1))
        model(f"Command / {side} / moulded eight-corner closed cast pedestal",
              verts,faces,mats["powder_ivory"])
        # Standalone structural gussets, service access panel and toe relief.
        x,y,z=P(0,.29,.02)
        box(f"Command / {side} / recessed toe support",(x,y,z),(.52,.105,.56),
            mats["powder_graphite"],.025,rot)
        x,y,z=P(0,.45,.312)
        box(f"Command / {side} / rear service door",(x,y,z),(.53,.42,.023),
            mats["powder_graphite"],.014,rot)
    # Top molded surface, elastomer gasket, physical glass with V3 screen
    # content at exactly the original systems 03/05 atlas coordinates.
    x,y,z=P(0,1.115,-.01)
    box(f"Command / {side} / instrument rim",(x,y,z),(.737,.066,.770),
        mats["satin_nickel"],.042,rot)
    x,y,z=P(0,1.155,-.01)
    box(f"Command / {side} / smoky glass gasket",(x,y,z),(.651,.018,.675),
        mats["console_gasket"],.023,rot)
    span=.598;depth=.585
    vertices=[
        P(-span/2,1.165,-depth/2),
        P(span/2,1.165,-depth/2),
        P(span/2,1.165,depth/2),
        P(-span/2,1.165,depth/2),
    ]
    face=model(f"Command / {side} / original atlas screen",
       vertices,[(0,2,1),(0,3,2)],mats["screen_left" if side==-1 else "screen_right"],
       ([(0,1),(1,1),(1,0),(0,0)] if correct_screen_uv else [(0,0),(1,0),(1,1),(0,1)]))
    for poly in face.data.polygons:poly.use_smooth=False
    # A single physically mounted top lip and tactile control strips.
    trim=[P(-.302+i*.030,1.176,-.335) for i in range(21)]
    pipe(f"Command / {side} / tactile satin front rim",trim,.011,mats["rose_bronze"])
    for j in range(7):
        a=-.275+j*.087
        x,y,z=P(a,1.189,.340)
        box(f"Command / {side} / tactile switch {j}",(x,y,z),
            (.052,.012,.030),mats["satin_nickel"] if j%3 else mats["rose_bronze"],
            .006,rot)
    for xdir in (-1,1):
        for b in (-.30,.29):
            x,y,z=P(xdir*.32,1.165,b)
            bolt(f"Command / {side} / fastener {xdir}:{b}",x,y,z,mats["satin_nickel"])
    if not stage32:
        x,y,z=P(0,.46,-.374)
        pipe(f"Command / {side} / light-seam recess",
             [P(-.29,.38,-.386),P(.29,.38,-.386)],.008,mats["satin_nickel"])

def build_command(mats,correct_screen_uv=False,stage32=False):
    # All geometry respects the measured V3 oval footprint and y=.28 top.
    lathe("Plinth / lower integrated side skirt",[
       (.018,1.72,1.42),(.055,1.80,1.49),(.185,1.85,1.54),
       (.238,1.84,1.53),(.261,1.79,1.48)],mats["powder_graphite"])
    lathe("Plinth / upper radius rolled shoulder",[
       (.242,1.85,1.54),(.259,1.81,1.51),(.277,1.78,1.47)],
       mats["satin_nickel"])
    global PLATFORM_TOP
    PLATFORM_TOP=disk("Plinth / original command carpet top",.281,1.765,1.46,
                      mats["plum_carpet"])
    # Inset copper trim and restrained flush fasteners around 360-degree
    # moulding; no floating rail above the commanding chair sight line.
    for name,y,rx,rz,radius,material in [
        ("Plinth / restrained satin outer bead",.275,1.837,1.53,.010,"rose_bronze"),
        ("Plinth / upper inset reveal",.288,1.76,1.46,.006,"satin_nickel"),
        ("Plinth / lower cast shadow seam",.073,1.805,1.50,.007,"console_gasket"),
    ]:
        path=[(rx*math.cos(i*2*PI/128),y,1.11+rz*math.sin(i*2*PI/128))
              for i in range(129)]
        pipe(name,path,radius,mats[material],segments=3)
    for i in range(28):
        a=i*2*PI/28
        x=1.818*math.cos(a);z=1.11+1.512*math.sin(a)
        bolt(f"Plinth / seated edge fastener {i}",x,.276,z,mats["satin_nickel"],.009)
    # Curved approach tread lines live INSIDE the original oval footprint.
    # This does not alter the MUD collision/step navigation logic.
    for n,(y,rx,rz) in enumerate(((.110,1.81,1.50),(.205,1.77,1.465))):
        points=[]
        for i in range(49):
            t=(i/48*2-1)*.68
            points.append((rx*math.sin(t),y,1.11-rz*math.cos(t)))
        pipe(f"Plinth / forward approach tread seam {n}",points,.013,
             mats["rose_bronze"] if n else mats["satin_nickel"])
    # Original side rail footprint. Structural posts and handrail are
    # actual cylinders, not emissive curves on a floor.
    for side in (-1,1):
        waypoints=[(side*1.68,.298,1.51),(side*1.79,.310,1.91),
                   (side*1.67,.294,2.18)]
        high=[(x,.790+(.08 if i==1 else .0),z) for i,(x,_,z) in enumerate(waypoints)]
        for j,low in enumerate(waypoints):
            rod(f"Rail {side} / forged post {j}",low,high[j],.021,
                mats["satin_nickel"])
            x,_,z=high[j]
            bolt(f"Rail {side} / post cap {j}",x,high[j][1]+.012,z,mats["rose_bronze"],.022)
        pipe(f"Rail {side} / hand-rest cast bronze tube",high,.022,mats["rose_bronze"])
        pipe(f"Rail {side} / lower structural cable",
             [(x,y+.10,z) for x,y,z in waypoints],.009,mats["satin_nickel"])
    make_pylon(-1,mats,correct_screen_uv,stage32=stage32)
    make_pylon(1,mats,correct_screen_uv,stage32=stage32)

def camera(name,position,aim,lens):
    data=bpy.data.cameras.new(name)
    data.lens=lens
    data.sensor_width=36
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.location=xyz(*position)
    ob.rotation_euler=(xyz(*aim)-ob.location).to_track_quat("-Z","Y").to_euler()
    return ob

def light(name,position,aim,power,rgb,size):
    data=bpy.data.lights.new(name,"AREA")
    data.energy=power
    data.color=rgb
    data.shape="RECTANGLE"
    data.size=size[0];data.size_y=size[1]
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.location=xyz(*position)
    ob.rotation_euler=(xyz(*aim)-ob.location).to_track_quat("-Z","Y").to_euler()
    return ob

def studio():
    floor=bpy.data.materials.new("RENDER STUDIO dark background")
    floor.diffuse_color=(.20,.20,.23,1)
    bpy.ops.mesh.primitive_plane_add(size=2,location=xyz(0,-.026,1.11))
    ob=bpy.context.object
    ob.name="RENDER STUDIO FLOOR - NOT EXPORTED"
    ob.scale=(8,8,8)
    ob.data.materials.append(floor)
    bpy.context.scene.world=bpy.data.worlds.new("Warm set indirect ambient")
    world=bpy.context.scene.world;world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.25,.22,.24,1)
    bg.inputs["Strength"].default_value=.35
    light("Warm ceiling key",(-3.7,4.2,2.9),(0,.9,1.11),780,(1,.83,.7),(4.1,3.2))
    light("Diffuse cool command bounce",(4.0,3.2,-1.8),(0,1.1,.4),360,(.70,.83,1),(2.8,2.0))
    light("Aft practical studio softbox",(0,3.3,5.1),(0,.8,1.11),360,(1,.92,.81),(3.8,2.8))
    return {
      "aft":camera("QA / aft",(-1.23,1.67,4.80),(0,.68,.73),37),
      "command":camera("QA / command",(-2.32,1.67,2.15),(-.22,1.07,.50),42),
      "console":camera("QA / port instrument",(-1.75,1.66,2.10),(-1.27,1.08,.58),62),
      "overhead":camera("QA / over-platform",(0,3.85,.20),(0,.20,1.11),37),
    }

def bake_platform_ao(out,mats):
    # Concrete Cycles AO baking, NOT full indirect diffuse irradiance. A
    # unique secondary UV layer on only the oval platform top avoids all
    # cross-object bake UV collisions.
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.samples=20
    scene.render.bake.margin=4
    ob=PLATFORM_TOP
    uv=ob.data.uv_layers.get("AST_BAKED_AO_UV")
    if uv is None:raise RuntimeError("No independent AO UV channel")
    ob.data.uv_layers.active=uv
    bitmap=bpy.data.images.new("ASTERIA_PLATFORM_REAL_CYCLES_AO",width=512,height=512,
                               alpha=False,float_buffer=False)
    bitmap.generated_color=(1,1,1,1)
    mat=mats["plum_carpet"]
    target=mat.node_tree.nodes.new("ShaderNodeTexImage")
    target.image=bitmap
    target.label="Cycles actual baked platform AO"
    uvmap=mat.node_tree.nodes.new("ShaderNodeUVMap")
    uvmap.uv_map="AST_BAKED_AO_UV"
    mat.node_tree.links.new(uvmap.outputs["UV"],target.inputs["Vector"])
    for node in mat.node_tree.nodes:node.select=False
    target.select=True;mat.node_tree.nodes.active=target
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.bake(type="AO")
    file=out/"asteria-command-platform-baked-ao.png"
    bitmap.filepath_raw=str(file.resolve())
    bitmap.file_format="PNG"
    bitmap.save()
    bitmap.pack()
    # glTF Settings extension node causes Blender exporter to use UV1
    # for occlusionTexture. Renderer can inspect glTF and bind as aoMap.
    group=bpy.data.node_groups.get("glTF Settings")
    if group is None:
        group=bpy.data.node_groups.new("glTF Settings","ShaderNodeTree")
    if "Occlusion" not in [s.name for s in group.interface.items_tree]:
        group.interface.new_socket(name="Occlusion",in_out="INPUT",
                                   socket_type="NodeSocketColor")
    holder=mat.node_tree.nodes.new("ShaderNodeGroup")
    holder.node_tree=group
    mat.node_tree.links.new(target.outputs["Color"],holder.inputs["Occlusion"])
    return file

def main():
    a=args()
    if a.samples<8 or min(a.resolution)<128:raise ValueError("Invalid QA settings")
    source=json.loads((a.materials/"material-provenance.json").read_text())
    assert source['id']=="ASTERIA-COMMAND-PBR-01"
    a.out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    global COMMAND
    COMMAND=bpy.data.collections.new("USS ASTERIA / COMMAND ARCHITECTURE / CANDIDATE 01")
    bpy.context.scene.collection.children.link(COMMAND)
    defs={
      "powder_ivory":(.72,.16),"powder_graphite":(.67,.15),
      "satin_nickel":(.38,.67),"rose_bronze":(.43,.56),
      "plum_carpet":(.92,0),"console_gasket":(.87,0)
    }
    mats={name:build_material("Asteria / command / "+name,name,*properties,a.materials)
          for name,properties in defs.items()}
    mats["screen_left"]=display_material("Asteria / V3 command overview screen",
        a.materials/"v3_command_overview_screen.png")
    mats["screen_right"]=display_material("Asteria / V3 systems screen",
        a.materials/"v3_systems_control_screen.png")
    build_command(mats,correct_screen_uv=a.correct_screen_uv,stage32=a.stage32_cast_support)
    views=studio()
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.samples=a.samples
    scene.cycles.use_denoising=False
    for layer in scene.view_layers:
        if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
    scene.view_settings.view_transform="AgX"
    scene.view_settings.look="AgX - Medium High Contrast"
    scene.view_settings.exposure=-.7
    scene.render.resolution_x=a.resolution[0]
    scene.render.resolution_y=a.resolution[1]
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.camera=views["aft"]
    bake_path=None
    if a.bake_ao:
        bake_path=bake_platform_ao(a.out,mats)
    # Editable source remains before converting the spline rails to meshes.
    bpy.ops.wm.save_as_mainfile(
        filepath=str((a.out/"asteria-command-set-candidate.blend").resolve()))
    for curve in [o for o in COMMAND.objects if o.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        curve.select_set(True);bpy.context.view_layer.objects.active=curve
        bpy.ops.object.convert(target="MESH")
    objects=[o for o in COMMAND.objects if o.type=="MESH"]
    assert len(objects)>30
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    opts=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    selection="use_selection" if "use_selection" in opts else "export_selected"
    assert selection in opts
    bpy.ops.export_scene.gltf(
        filepath=str((a.out/"asteria-command-set-candidate.glb").resolve()),
        export_format="GLB",**{selection:True})
    names=list(views) if a.view=="all" else [a.view]
    if not a.no_render:
        for name in names:
            scene.camera=views[name]
            scene.render.filepath=str((a.out/f"asteria-command-{name}.png").resolve())
            bpy.ops.render.render(write_still=True)
    report={
      "assetId":"ASTERIA_COMMAND_ARCHITECTURE_01",
      "roomId":CMD_ROOM,
      "sourceV3Blob":ORIGINAL_V3,
      "platformFootprint":{"xRadius":1.85,"zRadius":1.54,"zCenter":1.11,
                           "topY":.281},
      "pylonPositions":[[-1.27,.58],[1.27,.58]],
      "meshObjects":len(objects),
      "sourceFrozen":True,
      "cameraAndCampaignUnchanged":True,
      "cyclesSamples":a.samples,
      "realAOTexture":str(bake_path) if bake_path else None,
      "realAOBakedFor":"platform top only" if bake_path else "none",
      "notFullGlobalIllumination":True,
      "correctedOriginalScreenUv":bool(a.correct_screen_uv),
      "artApproval":False,
      "renderViews":[] if a.no_render else names,
      "notes":"Original authored PBR and frozen source instrument atlas, no scan or photoreal claim."
    }
    (a.out/"command-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("COMMAND_SET_REPORT",json.dumps(report,indent=2))

if __name__=="__main__":main()
