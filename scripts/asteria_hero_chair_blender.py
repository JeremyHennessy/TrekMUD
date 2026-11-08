#!/usr/bin/env python3
"""Isolated original USS Asteria command-chair hero asset.

blender -b -t 4 --python-exit-code 1 --python scripts/asteria_hero_chair_blender.py -- \
    --out _hero_chair_01 --samples 24 --view all --resolution 900 800

Creates .blend, GLB, Cycles frames and a manifest. Never modifies the original
V3/V5 bridge, collisions, browser UI, PADD or game state.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

PI = math.pi
ANCHOR_Z = 1.20
V3_BLOB = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"

def coord(x,y,z):
    """Original glTF Y-up room -> Blender Z-up."""
    return Vector((x,-(ANCHOR_Z+z),y))

def parameters():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--samples",type=int,default=24)
    p.add_argument("--texture-dir",type=Path,default=None,help="Optional pinned CC0 scan input")
    p.add_argument("--no-render",action="store_true",help="Export model and source only for browser testing")
    p.add_argument("--integrated-back",action="store_true",help="A/B sculpt continuous backrest rather than separate stiff insert plates")
    p.add_argument("--view",choices=["front","rear","quarter","detail","all"],default="all")
    p.add_argument("--resolution",nargs=2,type=int,default=[900,800])
    return p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

def mat(name,color,rough,metal=0,grain=False):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    shader=m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Roughness"].default_value=rough
    shader.inputs["Metallic"].default_value=metal
    if grain:
        # Cycles only: procedural relief is NOT a baked glTF texture.
        n=m.node_tree.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value=180
        n.inputs["Detail"].default_value=2
        b=m.node_tree.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value=.07
        b.inputs["Distance"].default_value=.002
        m.node_tree.links.new(n.outputs["Fac"],b.inputs["Height"])
        m.node_tree.links.new(b.outputs["Normal"],shader.inputs["Normal"])
    return m

def own(obj):
    for c in tuple(obj.users_collection):c.objects.unlink(obj)
    HERO.objects.link(obj)
    return obj

def geometry(name,vertices,faces,materials,indices):
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);HERO.objects.link(ob)
    for material in materials:data.materials.append(material)
    # True meter-scale UVs for textile geometry; curves and hard parts keep their
    # original generated mapping. Repeat roughly every 0.30 m.
    uv=data.uv_layers.new(name="ASTERIA_FABRIC_UV")
    for poly in data.polygons:
        for li in poly.loop_indices:
            vertex=data.vertices[data.loops[li].vertex_index].co
            x,depth,height=float(vertex.x),float(-vertex.y-ANCHOR_Z),float(vertex.z)
            uv.data[li].uv=(x*3.3,(depth if name.startswith("Seat /") else height)*3.3)
    for k,poly in enumerate(data.polygons):
        poly.material_index=indices[k]
        poly.use_smooth=True
    return ob

def thick_pad(name,surface,rows,cols,front,rear,thickness=.115):
    """Continuous closed, curved, solid furniture, not intersecting box panels."""
    front_points=[];back_points=[]
    for j in range(rows+1):
        for i in range(cols+1):
            x,y,z=surface(-1+2*i/cols,j/rows)
            front_points.append(tuple(coord(x,y,z)))
            back_points.append(tuple(coord(x,y,z+thickness)))
    off=len(front_points);verts=front_points+back_points
    stride=cols+1;faces=[];ids=[]
    def add(f,m):faces.append(f);ids.append(m)
    for j in range(rows):
        for i in range(cols):
            a=j*stride+i;b=a+1;c=a+stride;d=c+1
            add((a,c,b),0);add((b,c,d),0)
            add((a+off,b+off,c+off),1);add((b+off,d+off,c+off),1)
    boundaries=(
       [j*stride for j in range(rows+1)],
       [j*stride+cols for j in range(rows+1)],
       list(range(stride)),
       [rows*stride+i for i in range(stride)],
    )
    for edge in boundaries:
        for a,b in zip(edge,edge[1:]):
            add((a,b,a+off),1);add((b,b+off,a+off),1)
    return geometry(name,verts,faces,[front,rear],ids)

def pipe(name,points,radius,material):
    curve=bpy.data.curves.new(name,"CURVE")
    curve.dimensions="3D";curve.bevel_depth=radius;curve.bevel_resolution=3
    spline=curve.splines.new("POLY");spline.points.add(len(points)-1)
    for v,p in zip(spline.points,points):
        v.co=(*coord(*p),1)
    curve.materials.append(material)
    ob=bpy.data.objects.new(name,curve);HERO.objects.link(ob)
    return ob

def cylinder(name,x,y,z,r,h,material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=h,location=coord(x,y,z))
    ob=own(bpy.context.object);ob.name=name;ob.data.materials.append(material)
    for face in ob.data.polygons:face.use_smooth=True
    bevel=ob.modifiers.new("Physical edge roundover","BEVEL")
    bevel.width=min(.014,h*.22);bevel.segments=3
    ob.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return ob

def softened_box(name,x,y,z,width,height,depth,bevel,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=coord(x,y,z))
    ob=own(bpy.context.object);ob.name=name
    ob.dimensions=(width,depth,height)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    bevel_mod=ob.modifiers.new("Molded radius","BEVEL")
    bevel_mod.width=bevel;bevel_mod.segments=5
    ob.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return ob

def rod(name,a,b,r,material):
    p=coord(*a);q=coord(*b);d=q-p
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=d.length,location=(p+q)/2)
    ob=own(bpy.context.object);ob.name=name
    ob.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    ob.data.materials.append(material)
    for face in ob.data.polygons:face.use_smooth=True
    return ob

def back_surface(u,t):
    # Follows V3 original hero-v3.js (large chair) silhouette and pose.
    half=.54*(.78+.24*math.sin(PI*t)-.075*t)
    x=u*half*(1-.075*abs(u)**8)
    y=.76+1.08*t
    z=.245+.255*t+.032*math.sin(PI*t)-.105*(1-u*u)-.029
    z-=.012*(1-u*u)*math.sin(PI*t)**2
    return x,y,z

def integrated_back_surface(u,t):
    """One continuous upholstered front, with soft internal foam contours.

    Preserve frozen V3 exterior side/height silhouette: only the inner front
    relief is altered, with no detached lumbar/shoulder plates. The seam
    depressions are actual surface geometry, not floating tube decorations.
    """
    x,y,z=back_surface(u,t)
    width_falloff=max(0.,1-u*u)**1.45
    # Smooth volumetric foam support areas, fading toward the same shell edge.
    lumbar=.052*math.exp(-((t-.38)/.22)**4)
    shoulders=.033*math.exp(-((t-.83)/.12)**4)
    side_support=.016*math.exp(-((abs(u)-.72)/.19)**2)*math.sin(PI*t)**2
    z-=(lumbar+shoulders)*width_falloff+side_support
    # Three shallow recessed stitched channels; the front surface recedes into
    # the cushion, rather than an extra tube hovering in front of the fabric.
    for location in (.16,.65,.79):
        z+=.011*math.exp(-((t-location)/.021)**2)*width_falloff
    return x,y,z


def seat_surface(u,v):
    x=.54*u;z=-.42+.76*v
    y=.702+.065*(1-u*u)+.018*math.sin(PI*v)-.025*(v-.5)**2
    return x,y,z

def apply_cc0_material_scan(m,folder):
    """Use vetted 1K photo-scanned PBR maps; no runtime URLs or new geometry."""
    info=json.loads((folder/"fabric-provenance.json").read_text())
    if info.get("assetId")!="velour_velvet" or info.get("license")!="CC0-1.0":
        raise RuntimeError("Unexpected scanned-fabric provenance")
    verified={
        "diff.png":"fb9bde5e9ca1015424f3149fdc96daed0d040cbb944965d727993c9af40c478c",
        "nor_gl.png":"0bfa4622e13072494f36ce32d6af5e95b1037eb05e6dac10e39e90aac4154ed1",
        "rough.png":"abbf0df83e6b19e8924f3e32eb853d5f0a78d6a64f96e2aff16803ca2bae99d8",
        "asteria_mauve_diffuse.png":"a66fe908499d46c2aef9b03e0e0e627afa9af74cd7ca129dae7b969dc250a0e2",
        "asteria_mauve_light_diffuse.png":"babdbc8285877b2456d9ebcc67f2ba17bd210c81efa342df0016bf2aebf27025",
    }
    for fname,digest in verified.items():
        path=folder/fname
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise RuntimeError("CC0 fabric source changed; reject unapproved asset: "+fname)
    def attach(key,base):
        matobj=m[key]
        tree=matobj.node_tree
        shader=tree.nodes.get("Principled BSDF")
        for label,filename,srgb in [
          ("Asteria signed-off CC0 base",base,True),
          ("Asteria CC0 roughness","rough.png",False),
          ("Asteria CC0 normal OpenGL","nor_gl.png",False),
        ]:
            image=bpy.data.images.load(str((folder/filename).resolve()),check_existing=True)
            if not srgb:image.colorspace_settings.name="Non-Color"
            image.pack()
            tex=tree.nodes.new("ShaderNodeTexImage")
            tex.label=label;tex.image=image;tex.extension="REPEAT"
            if srgb:tree.links.new(tex.outputs["Color"],shader.inputs["Base Color"])
            elif filename=="rough.png":
                tree.links.new(tex.outputs["Color"],shader.inputs["Roughness"])
            else:
                normal=tree.nodes.new("ShaderNodeNormalMap")
                normal.inputs["Strength"].default_value=.45
                tree.links.new(tex.outputs["Color"],normal.inputs["Color"])
                tree.links.new(normal.outputs["Normal"],shader.inputs["Normal"])
    attach("fabric","asteria_mauve_diffuse.png")
    attach("fabric_light","asteria_mauve_light_diffuse.png")

def chair(m, integrated_back=False):
    # Weighted swivel construction, bearings and load-bearing collar.
    for name,y,r,h,material in [
        ("Weighted cast base",.080,.35,.095,"frame"),
        ("Machined lower bearing",.150,.305,.046,"metal"),
        ("Swivel hub",.222,.148,.072,"frame"),
        ("Height-adjust shaft",.374,.075,.267,"metal"),
        ("Under-seat collar",.528,.194,.106,"frame")]:
        cylinder("Pedestal / "+name,0,y,0,r,h,m[material])
    for s in (-1,1):
        rod("Pedestal / diagonal brace "+str(s),(s*.20,.24,.08),(s*.37,.48,.13),.03,m["metal"])

    # Rounded, pressure-formed seat cushion with its own bottom shell.
    N=42;R=24
    top=[];bottom=[]
    for j in range(R+1):
        for i in range(N+1):
            x,y,z=seat_surface(-1+2*i/N,j/R)
            top.append(tuple(coord(x,y,z)))
            bottom.append(tuple(coord(x,y-.13,z)))
    offset=len(top);f=[];ids=[];step=N+1
    for j in range(R):
        for i in range(N):
            a=j*step+i;b=a+1;c=a+step;d=c+1
            f.extend(((a,c,b),(b,c,d),(a+offset,b+offset,c+offset),(b+offset,d+offset,c+offset)))
            ids.extend((0,0,1,1))
    for edge in ([j*step for j in range(R+1)],[j*step+N for j in range(R+1)],
                 list(range(step)),[R*step+i for i in range(step)]):
        for a,b in zip(edge,edge[1:]):
            f.extend(((a,b,a+offset),(b,b+offset,a+offset)));ids.extend((1,1))
    geometry("Seat / contoured textile and structural shell",top+bottom,f,[m["fabric"],m["frame"]],ids)
    for s in (-1,1):
        pipe("Seat / side welt "+str(s),[seat_surface(s*.98,j/32) for j in range(33)],.007,m["thread"])
    pipe("Seat / curved front welt",[seat_surface(-.94+1.88*i/46,.027) for i in range(47)],.008,m["thread"])

    # Physical double-wall chair back. A/B alternative: sculpt padding into a
    # single continuous upholstered front so there are no squared-off pads.
    if integrated_back:
        thick_pad("Back / curved upholstered seat-back and shell",
                  integrated_back_surface,80,60,m["fabric"],m["shell"])
    else:
        thick_pad("Back / curved upholstered seat-back and shell",
                  back_surface,44,48,m["fabric"],m["shell"])
        def lumbar(u,t):
            x,y,z=back_surface(u*.74,.14+.49*t)
            return x,y,z-.025*(1-u*u)*math.sin(PI*t)
        thick_pad("Back / articulated lumbar cushion",lumbar,20,30,m["fabric_light"],m["fabric"],.037)
        def head(u,t):
            x,y,z=back_surface(u*.66,.76+.19*t)
            return x,y,z-.020*(1-u*u)*math.sin(PI*t)
        thick_pad("Back / integrated shoulder bolster",head,12,30,m["fabric_light"],m["fabric"],.036)
    for s in (-1,1):
        pipe("Back / moulded welting "+str(s),
             [back_surface(s*.955,.045+.91*i/50) for i in range(51)],.009,m["thread"])
    if not integrated_back:
        # Old raised seams are a deliberate part of the control image.
        for t in (.17,.66,.79):
            pipe("Back / recessed seam %.2f"%t,
                 [back_surface(-.75+1.5*i/36,t) for i in range(37)],.0035,m["thread"])

    # Cantilever support arms, rounded fabric, black inset control glass,
    # separate physical button geometry, and forged rear struts.
    for s in (-1,1):
        rod("Arm / front cast brace "+str(s),(s*.42,.49,-.20),(s*.67,.82,-.14),.035,m["metal"])
        rod("Arm / rear cast brace "+str(s),(s*.42,.53,.28),(s*.67,.83,.23),.035,m["metal"])
        softened_box("Arm / structural molding "+str(s),s*.665,.845,.05,.25,.18,.61,.052,m["frame"])
        softened_box("Arm / padded textile grip "+str(s),s*.665,.953,.05,.25,.085,.56,.036,m["fabric"])
        softened_box("Arm / smoked-glass control "+str(s),s*.665,1.006,-.035,.135,.012,.285,.005,m["glass"])
        for idx,(z,kind) in enumerate(((-.14,"pale"),(-.085,"amber"),(-.03,"cyan"),(.025,"pale"),(.08,"amber"))):
            softened_box("Arm / physical input %s-%d"%(s,idx),s*.665,1.015,z,.066,.010,.031,.004,m[kind])
        rod("Back / rear metal rib "+str(s),(s*.32,.54,.20),(s*.35,1.05,.39),.029,m["metal"])
        pipe("Back / rear satin rib "+str(s),
             [(back_surface(s*.88,i/26)[0],back_surface(s*.88,i/26)[1],
               back_surface(s*.88,i/26)[2]+.13) for i in range(27)],.011,m["metal"])

def area(name,position,aim,power,color,w,h):
    d=bpy.data.lights.new(name,"AREA");d.energy=power;d.color=color
    d.shape="RECTANGLE";d.size=w;d.size_y=h
    ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob)
    ob.location=coord(*position)
    ob.rotation_euler=(coord(*aim)-ob.location).to_track_quat("-Z","Y").to_euler()

def cam(name,position,aim,lens):
    d=bpy.data.cameras.new(name);d.lens=lens;d.sensor_width=36
    ob=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(ob)
    ob.location=coord(*position)
    ob.rotation_euler=(coord(*aim)-ob.location).to_track_quat("-Z","Y").to_euler()
    return ob

def studio():
    # Light and floor here are NOT exported in the glTF furniture asset.
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.6,depth=.09,location=coord(0,-.025,.06))
    bpy.context.object.name="RENDER STUDIO - floor only"
    floor=mat("Studio / neutral charcoal",(.11,.12,.15),.95)
    bpy.context.object.data.materials.append(floor)
    world=bpy.data.worlds.new("Neutral photographic environment")
    world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.06,.08,.105,1)
    bg.inputs["Strength"].default_value=.37
    bpy.context.scene.world=world
    area("Warm broad key",(-2,3.6,-1.2),(0,1.1,.02),520,(1,.85,.72),3.1,2.8)
    area("Cool rim",(1.5,3.0,1.2),(0,1.15,0),360,(.68,.84,1),2.2,2.8)
    area("Warm bounce",(1.3,2.5,-1.6),(0,1.0,0),215,(1,.90,.83),1.4,2.0)
    data={
      # Wider whole-object composition before judging texture and geometry.
      # Only these offline reference cameras change; no game camera moves.
      "front":((0,1.29,-3.20),(0,1.02,.13),47),
      "rear":((0,1.43,4.10),(0,1.06,.18),47),
      "quarter":((-2.40,1.53,-2.55),(0,1.09,.11),48),
      "detail":((-.73,1.53,-.53),(0,1.29,.17),75),
    }
    return {key:cam("ASSET QA / "+key,*v) for key,v in data.items()}

def main():
    a=parameters()
    if a.samples<8 or min(a.resolution)<128:raise ValueError("Invalid QA settings")
    a.out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    global HERO
    HERO=bpy.data.collections.new("USS ASTERIA / HERO CHAIR / EXPERIMENT 01")
    bpy.context.scene.collection.children.link(HERO)
    m={
      "fabric":mat("Asteria / woven plum microfibre",(.29,.215,.28),.87,grain=True),
      "fabric_light":mat("Asteria / muted mauve cushion",(.41,.316,.36),.89,grain=True),
      "shell":mat("Asteria / graphite moulded backing",(.13,.12,.155),.59),
      "frame":mat("Asteria / dark cast structure",(.10,.102,.13),.65,.18),
      "metal":mat("Asteria / satin brushed nickel",(.51,.46,.45),.34,.71),
      "glass":mat("Asteria / smoky instrument glass",(.025,.043,.055),.23,.05),
      "thread":mat("Asteria / restrained seam piping",(.53,.455,.45),.83),
      "cyan":mat("Asteria / cyan controls",(.24,.56,.66),.28),
      "amber":mat("Asteria / amber controls",(.72,.47,.27),.35),
      "pale":mat("Asteria / pale controls",(.68,.68,.68),.40),
    }
    if a.texture_dir:
        apply_cc0_material_scan(m,a.texture_dir)
    chair(m, integrated_back=a.integrated_back)
    cameras=studio()
    sc=bpy.context.scene;sc.render.engine="CYCLES";sc.cycles.samples=a.samples
    sc.cycles.use_denoising=False
    for layer in sc.view_layers:
        if hasattr(layer,"cycles"):layer.cycles.use_denoising=False
    sc.render.resolution_x=a.resolution[0];sc.render.resolution_y=a.resolution[1]
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    sc.view_settings.view_transform="AgX"
    sc.view_settings.look="AgX - Medium High Contrast"
    # A/B only: reduce Cycles display exposure, preserving all asset geometry,
    # material inputs, studio light positions, and exported GLB bytes.
    sc.view_settings.exposure=-1.4
    sc.camera=cameras["quarter"]
    bpy.ops.wm.save_as_mainfile(filepath=str((a.out/"asteria-hero-chair-candidate.blend").resolve()))
    # Blender curves are editable in the .blend; convert only the export stage
    # to actual mesh surfaces so glTF does not silently omit the fine piping.
    for curve in [o for o in HERO.objects if o.type=="CURVE"]:
        bpy.ops.object.select_all(action="DESELECT")
        curve.select_set(True);bpy.context.view_layer.objects.active=curve
        bpy.ops.object.convert(target="MESH")
    mesh_objects=[o for o in HERO.objects if o.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=mesh_objects[0]
    props=bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    select_arg="use_selection" if "use_selection" in props else "export_selected"
    if select_arg not in props:raise RuntimeError("glTF exporter cannot isolate selected chair")
    bpy.ops.export_scene.gltf(filepath=str((a.out/"asteria-hero-chair-candidate.glb").resolve()),
                              export_format="GLB",**{select_arg:True})
    chosen=list(cameras) if a.view=="all" else [a.view]
    if not a.no_render:
        for name in chosen:
            sc.camera=cameras[name]
            sc.render.filepath=str((a.out/("asteria-chair-"+name+".png")).resolve())
            bpy.ops.render.render(write_still=True)
    report={
      "assetId":"ASTERIA-HERO-CHAIR-CANDIDATE-01",
      "roomId":"AST-D01-BRIDGE","originalChairAnchor":[0,ANCHOR_Z],
      "frozenV3Blob":V3_BLOB,"meshObjects":len(mesh_objects),
      "renderer":"Blender Cycles","samples":a.samples,
      "cyclesExposureEV":-1.4,
      "renderedViews":[] if a.no_render else chosen,"separateFromBrowser":True,
      "photoScannedFabric":bool(a.texture_dir),
      "integratedBackCandidate":bool(a.integrated_back),
      "materialLimit":"Scanned albedo, roughness and normal embedded in candidate GLB when texture-dir is supplied",
      "visualApproved":False,
    }
    (a.out/"hero-chair-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
