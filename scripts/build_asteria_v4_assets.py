#!/usr/bin/env python3
"""Original USS Asteria bridge glTF 2.0 set asset builder.

Generates real 3D mesh assets (not screenshots) with embedded PBR texture maps.
Deterministic and offline. This first V4 slice is an original scene study,
not a reconstruction of any television production set.
"""
from __future__ import annotations
import argparse, json, math, os
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

PI=math.pi
ROOT=Path(__file__).resolve().parent
W,D=7.55,6.55
rng=np.random.default_rng(37542)


def texture_set(key, rgb, kind, size=512):
    """Make deterministic textile/composite/metallic color and tangent-normal PBR maps."""
    y,x=np.mgrid[:size,:size]; n=rng.normal(0,1,(size,size))
    grain=np.sin(x*1.29)+np.sin(y*1.37)
    if kind=='textile':
        weave=(np.sin(x*2.83)*np.cos(y*2.64))*.85+np.sin((x+y)*.29)*.19
        variation=weave*3.0+n*1.7
        rough=.91; metal=.0; normal_z=246; scale=5.5
    elif kind=='carpet':
        wave=(np.sin((x-y)*.24)+np.sin((x+y)*.36))*1.20
        variation=wave*1.65+n*1.2
        rough=.98; metal=.0; normal_z=239; scale=10.0
    elif kind=='metal':
        brush=np.sin(y*2.46)*.85+np.sin(y*.23)*.25
        variation=brush*3.5+n*.85
        rough=.36;metal=.82;normal_z=253;scale=2.4
    elif kind=='paint':
        variation=n*2.35 + np.sin(x*.073+y*.041)*1.5
        rough=.76;metal=.04;normal_z=249;scale=3.9
    elif kind=='rubber':
        variation=n*2.0
        rough=.87;metal=.0;normal_z=251;scale=3.0
    else:
        variation=n*1.4
        rough=.45;metal=.03;normal_z=251;scale=2.1
    base=np.zeros((size,size,4),dtype=np.uint8)
    for i,v in enumerate(rgb): base[:,:,i]=np.clip(v+variation,0,255).astype('uint8')
    base[:,:,3]=255
    grad_y,grad_x=np.gradient(variation)
    nm=np.stack([128-grad_x*scale,128-grad_y*scale,np.full((size,size),normal_z)],axis=-1)
    nm=np.clip(nm,0,255).astype('uint8')
    mr=np.zeros((size,size,3),dtype=np.uint8)
    mr[:,:,0]=int(100) # occlusion channel separate
    mr[:,:,1]=int(rough*255)
    mr[:,:,2]=int(metal*255)
    ao=np.zeros((size,size,3),dtype=np.uint8)
    ao[:]=245
    return (Image.fromarray(base,'RGBA'),Image.fromarray(nm,'RGB'),Image.fromarray(mr,'RGB'),Image.fromarray(ao,'RGB'),rough,metal)

TEXTURES={}
PALETTE={
 'wall': ((164,155,147),'paint'),
 'bone': ((192,181,169),'paint'),
 'carpet':((57,74,92),'carpet'),
 'dais':((98,79,95),'textile'),
 'upholstery':((118,96,114),'textile'),
 'upholstery_dark':((74,62,79),'textile'),
 'satin':((139,135,142),'metal'),
 'bronze':((147,121,99),'metal'),
 'console':((111,109,111),'paint'),
 'shell':((89,90,98),'paint'),
 'rubber':((36,40,46),'rubber'),
 'glass':((21,33,44),'glass'),
 'light':((231,218,187),'glass'),
 'coollight':((158,213,233),'glass'),
 'black':((15,18,26),'rubber'),
}
for k,(color,kind) in PALETTE.items():
    base,norm,mr,ao,rough,metal=texture_set(k,color,kind)
    kw=dict(name='ASTERIA_'+k,baseColorFactor=[255,255,255,255],baseColorTexture=base,
            normalTexture=norm,metallicRoughnessTexture=mr,occlusionTexture=ao,
            roughnessFactor=1., metallicFactor=1.,doubleSided=True)
    if k in ('light','coollight'):
        kw['emissiveFactor']=([1.0,.86,.65] if k=='light' else [.50,.82,1.0]);
        kw['metallicFactor']=0.;kw['roughnessFactor']=.42
    if k=='glass': kw.update(roughnessFactor=.4,metallicFactor=.22)
    TEXTURES[k]=PBRMaterial(**kw)

SCENE=trimesh.Scene()
STATS={'meshes':0,'triangles':0,'materials':sorted(TEXTURES),'originalRoomId':'AST-D01-BRIDGE','unit':'meter','authoring':'offline numpy/trimesh glTF2 PBR geometry'}

def add(mesh,name,mat='wall',uv=None):
    mesh=mesh.copy()
    if uv is None:
        pts=np.asarray(mesh.vertices)
        # world-aligned UVs allow seamless texture appearance on most room surfaces
        dimensions=np.ptp(pts,axis=0)
        ids=np.argsort(dimensions)[-2:]
        scale=.25 if mat=='carpet' else .58
        uv=np.stack([pts[:,ids[0]]*scale,pts[:,ids[1]]*scale],axis=-1)
    mesh.visual=TextureVisuals(uv=np.asarray(uv,dtype=np.float64),material=TEXTURES[mat])
    try: mesh.fix_normals()
    except Exception: pass
    SCENE.add_geometry(mesh,node_name=name,geom_name=name)
    STATS['meshes']+=1; STATS['triangles']+=len(mesh.faces)
    return mesh

def box(name,center,size,mat='wall',rotation=0):
    mesh=trimesh.creation.box(extents=size)
    if rotation: mesh.apply_transform(trimesh.transformations.rotation_matrix(rotation,[0,1,0]))
    mesh.apply_translation(center)
    add(mesh,name,mat)

def cyl(name,center,radius,height,mat='satin',segments=40,axis='y'):
    mesh=trimesh.creation.cylinder(radius=radius,height=height,sections=segments)
    if axis=='y':mesh.apply_transform(trimesh.transformations.rotation_matrix(PI/2,[1,0,0]))
    mesh.apply_translation(center);add(mesh,name,mat)

def elliptical_band(name,rx,rz,inner,y0,y1,mat,segments=120,zc=0):
    vertices=[];faces=[];uv=[]
    for j in range(segments+1):
        a=2*PI*j/segments; sa,ca=math.sin(a),math.cos(a)
        for p in [(rx,y0,rz),(rx,y1,rz),(rx*inner,y1,rz*inner),(rx*inner,y0,rz*inner)]:
            vertices.append((p[0]*sa,p[1],p[2]*ca+zc));uv.append((j/segments*8,(p[1]+p[0]*.02)*.6))
    for j in range(segments):
        a=j*4;b=a+4
        for k in range(4):
            c=(k+1)%4;faces.extend([(a+k,b+k,b+c),(a+k,b+c,a+c)])
    add(trimesh.Trimesh(vertices=vertices,faces=faces,process=False),name,mat,uv)

def ellipse_disk(name,rx,rz,y,mat,zc=0,segments=140):
    vertices=[(0,y,zc)];uv=[(.5,.5)]
    for j in range(segments+1):
        a=2*PI*j/segments
        vertices.append((rx*math.sin(a),y,zc+rz*math.cos(a)));uv.append((math.sin(a)*.48+.5,math.cos(a)*.48+.5))
    faces=[(0,j,j+1) for j in range(1,segments+1)]
    add(trimesh.Trimesh(vertices=vertices,faces=faces,process=False),name,mat,uv)

def curve_tube(name,points,radius,mat='bronze',sides=10):
    pts=np.asarray(points,dtype=float); vert=[]; faces=[];uv=[]
    for i,p in enumerate(pts):
        prev=pts[max(0,i-1)]; nxt=pts[min(len(pts)-1,i+1)]
        tan=(nxt-prev);tan=tan/(np.linalg.norm(tan)+1e-9)
        axis=np.array([0,1.,0])
        if abs(np.dot(axis,tan))>.88:axis=np.array([1.,0,0])
        u=np.cross(axis,tan);u=u/(np.linalg.norm(u)+1e-9);v=np.cross(tan,u)
        for k in range(sides):
            a=2*PI*k/sides
            vert.append(p+radius*(u*math.cos(a)+v*math.sin(a)));uv.append([i/10,k/sides])
        if i:
            for k in range(sides):
                a=(i-1)*sides+k;b=(i-1)*sides+(k+1)%sides;c=i*sides+k;d=i*sides+(k+1)%sides
                faces.extend([(a,c,b),(b,c,d)])
    add(trimesh.Trimesh(vertices=vert,faces=faces,process=False),name,mat,uv)

def panel4(name,coords,mat='wall',uv=None):
    verts=np.array(coords,dtype=float)
    faces=np.array([(0,1,2),(0,2,3)],dtype=int)
    add(trimesh.Trimesh(vertices=verts,faces=faces,process=False),name,mat,uv)

def sweep_shell(name, rows, cols, sample, mat, width_uv=1,height_uv=1):
    """Custom continuous parametric fabrications with welded vertices and UV."""
    vertices=[];faces=[];uv=[]
    for i in range(rows+1):
        v=i/rows
        for j in range(cols+1):
            u=j/cols
            vertices.append(sample(u,v));uv.append((u*width_uv,v*height_uv))
    for i in range(rows):
        for j in range(cols):
            a=i*(cols+1)+j;b=a+1;c=a+(cols+1);d=c+1
            faces.extend([(a,c,b),(b,c,d)])
    add(trimesh.Trimesh(vertices=vertices,faces=faces,process=False),name,mat,uv)

# FLOOR AND MECHANICAL PLINTHS
ellipse_disk('AST_Bridge_Main_Carpet',W-.06,D-.06,.02,'carpet')
elliptical_band('AST_Bridge_Carpet_Outer_Gasket',W-.06,D-.06,.986,.029,.049,'rubber')
ellipse_disk('AST_Forward_Aisle_Zone',2.48,3.95,.035,'carpet',zc=-.55)
elliptical_band('AST_Command_Cast_Step',2.24,1.86,.965,.07,.29,'satin',zc=.96)
ellipse_disk('AST_Command_Bevel_Underlay',2.20,1.80,.298,'dais',zc=.96)
elliptical_band('AST_Command_Bronze_Edge',2.21,1.80,.992,.302,.322,'bronze',zc=.96)
for idx,s in enumerate([-1,1]):
    curve_tube(f'AST_Aisle_Inlay_{idx}',[(s*(1.4+.17*k/22),.043,-4.66+6.32*k/22) for k in range(23)],.010,'bronze',8)

# EXPERIMENT V4-WALL-01: a continuous inner structural backing behind the decorative wall bays.
# The v4 base model created separate wall bays with open gaps and omitted side sectors,
# revealing dark space instead of the underlying wall. Leave the forward viewscreen and
# aft command access open. The outer radius keeps the backing behind existing panels.
for k in range(120):
    a0=k*2*PI/120; a1=(k+1)*2*PI/120
    am=(a0+a1)/2
    dfront=abs((am-PI+PI)%(2*PI)-PI)
    daft=min(abs(am),abs(am-2*PI))
    if dfront<.55 or daft<.215:
        continue
    def structural_at(a,y):
        return (W*1.007*math.sin(a),y,D*1.007*math.cos(a))
    panel4(f'AST_Structural_Wall_Back_{k:03d}',
           [structural_at(a0,.24),structural_at(a1,.24),
            structural_at(a1,3.58),structural_at(a0,3.58)],'wall')

# ORIGINAL ARCHITECTURAL WALL SYSTEM: segmented true curved skin, inset relief and shadow coves
N=48
for k in range(N):
    a=(k+.5)*2*PI/N
    dfront=abs((a-PI+PI)%(2*PI)-PI)
    daft=min(abs(a),abs(a-2*PI))
    dside=min(abs(a-PI/2),abs(a-3*PI/2))
    if dfront<.53 or daft<.21 or dside<.105: continue
    b0=k*2*PI/N+.006;b1=(k+1)*2*PI/N-.006
    def wall_at(th,fr,y):return (W*fr*math.sin(th),y,D*fr*math.cos(th))
    panel4(f'AST_Wall_Bay_{k:02d}',[wall_at(b0,.983,.42),wall_at(b1,.983,.42),wall_at(b1,.983,3.42),wall_at(b0,.983,3.42)],'wall')
    panel4(f'AST_Wall_Inset_{k:02d}',[wall_at(b0+.014,.971,.86),wall_at(b1-.014,.971,.86),wall_at(b1-.014,.971,2.82),wall_at(b0+.014,.971,2.82)],'bone')
    for h in (.77,2.89):
        curve_tube(f'AST_Wall_Bay_Rail_{k:02d}_{h}',[wall_at(b0,.963,h),wall_at((b0+b1)/2,.963,h),wall_at(b1,.963,h)],.013,'satin',6)
    if k%3==0:
        # slimmer, repeated structural rib inset into panel bay edges
        p=wall_at(b0,.960,1.92)
        box(f'AST_Acoustic_Joiner_{k:02d}',p,(.035,2.74,.10),'satin',rotation=-(b0))

curve_tube('AST_Ceiling_Outer_Cove',[(W*.963*math.sin(a),3.51,D*.963*math.cos(a)) for a in np.linspace(0,2*PI,142)],.065,'bronze',12)
curve_tube('AST_Floor_Kick_Rail',[(W*.982*math.sin(a),.25,D*.982*math.cos(a)) for a in np.linspace(0,2*PI,142)],.040,'satin',10)

# CEILING: nested overhead shells; large panels with real housing geometry
elliptical_band('AST_Ceiling_Outer_Soffit',W*.962,D*.962,.635,3.58,4.30,'bone')
ellipse_disk('AST_Ceiling_Central_Coffer',3.15,2.42,4.34,'shell')
elliptical_band('AST_Ceiling_Coffer_Trim',3.20,2.46,.979,4.35,4.42,'bronze')
ellipse_disk('AST_Ceiling_Upper_Inner_Acoustic',2.25,1.65,4.38,'upholstery_dark')
for s in [-1,1]:
    for i in range(4):
        z=-4.68+i*2.72;x=s*4.74
        box(f'AST_Ceiling_Light_Housing_{s}_{i}',(x,3.90,z),(.89,.14,1.38),'shell')
        box(f'AST_Ceiling_Light_Diffuser_{s}_{i}',(x,3.81,z),(.67,.024,1.14),'light')
        for dx in (-.39,.39):
            box(f'AST_Light_Satin_Bezel_{s}_{i}_{dx}',(x+dx,3.83,z),(.037,.04,1.25),'satin')
for i in range(12):
    a=2*PI*i/12
    box(f'AST_Soffit_Central_Bolt_{i}',(2.68*math.sin(a),4.36,2.05*math.cos(a)),(.048,.04,.048),'bronze')

# FORWARD VIEWSCREEN - deep surround, actual open aperture (no opaque flat black wall)
box('AST_Viewer_Header',(0,3.40,-6.02),(7.0,.43,.52),'bone')
box('AST_Viewer_Footer',(0,.66,-6.02),(7.0,.42,.52),'console')
for s in [-1,1]:
    box(f'AST_Viewer_Side_Cast_{s}',(s*3.49,2.06,-6.04),(.42,2.86,.60),'bone')
    box(f'AST_Viewer_Metallic_Shim_{s}',(s*3.26,2.06,-5.83),(.061,2.59,.08),'bronze')
box('AST_Viewer_Top_Light',(0,3.18,-5.84),(6.40,.028,.073),'light')
box('AST_Viewer_Lower_Glass_Rail',(0,.87,-5.82),(6.43,.05,.14),'glass')

# AFT ACCESS PORTAL with framed door panels (not traversable in visual preview)
box('AST_Aft_Turbolift_Frame_Top',(0,3.20,6.11),(2.42,.28,.29),'bronze')
for s in [-1,1]:
    box(f'AST_Aft_Turbolift_Frame_{s}',(s*1.16,1.65,6.10),(.22,2.96,.27),'bronze')
    box(f'AST_Aft_Door_Panel_{s}',(s*.51,1.66,6.15),(1.00,2.69,.09),'wall')
    box(f'AST_Aft_Door_Inset_{s}',(s*.50,1.66,6.074),(.83,2.46,.027),'shell')
    box(f'AST_Aft_Door_Handle_{s}',(s*.25,1.53,6.04),(.06,.35,.044),'satin')
box('AST_Aft_Door_Nameplate',(0,3.40,6.045),(1.90,.11,.08),'light')

# SIDE SEALED SERVICE HATCHES - scenic placeholders only
for s in [-1,1]:
    box(f'AST_Side_Hatch_Frame_{s}',(s*7.28,1.70,-.12),(.20,2.97,1.85),'bronze')
    box(f'AST_Side_Hatch_Door_{s}',(s*7.14,1.70,-.12),(.11,2.74,1.67),'shell')
    box(f'AST_Side_Hatch_Seal_{s}',(s*7.04,1.70,-.12),(.02,2.55,1.46),'wall')
    box(f'AST_Side_Hatch_Display_{s}',(s*6.96,1.97,-.65),(.035,.30,.19),'glass')

# COMMAND CHAIR — HERO ASSET at (0, 1.25), curvilinear fully surfaced padding
cx,cz=0.,1.22
cyl('AST_Captain_Seat_Circular_Pedestal',(cx,.40,cz),.30,.53,'bronze',56)
cyl('AST_Captain_Seat_Cast_Plinth',(cx,.15,cz),.50,.17,'shell',64)
cyl('AST_Captain_Seat_Bearing_Ring',(cx,.62,cz),.22,.12,'satin',56)
# seat cushion, ellipsoid top shell as a parametric membrane with pear-shaped edge

def cushion(u,v):
    a=(u-.5)*2;b=(v-.5)*2
    w=(1-abs(a)**6)**.25
    z=cz-.16+.41*b
    x=.55*w*a
    y=.81+.125*max(0,1-a*a)**.8*(1-b*b)+.015*math.sin(v*PI)
    return (x,y,z)
sweep_shell('AST_Captain_Seat_3D_Padded_Pan',42,44,cushion,'upholstery',2.5,2.5)
# cushion cast lower rail/edging, layered yet realistic
curve_tube('AST_Captain_Seat_Seam',[(-.52*math.cos(a),.76,cz-.15+.36*math.sin(a)) for a in np.linspace(0,2*PI,85)],.016,'upholstery_dark',10)
# backrest with thick forward padded panel and satin rigid back shell

def chair_back(u,v,front=True):
    t=v; xnorm=(u-.5)*2
    taper=.50+.085*math.sin(t*PI)-.075*t
    x=taper*xnorm
    y=.80+t*1.25
    z=cz+.20+.23*t+.045*math.sin(t*PI)-.13*(1-xnorm*xnorm)
    if front: z-=.115+.035*math.sin(t*PI)*max(0,1-xnorm*xnorm)
    else:z+=.095
    return (x,y,z)
sweep_shell('AST_Captain_Seat_Padded_Contour',50,46,lambda u,v:chair_back(u,v,True),'upholstery',2.4,3.0)
sweep_shell('AST_Captain_Seat_Outer_Composite_Shell',50,46,lambda u,v:chair_back(u,v,False),'shell',2.4,3.0)
for s in [-1,1]:
    curve_tube(f'AST_Captain_Seat_Edge_Piping_{s}',[chair_back(0 if s<0 else 1,t,True) for t in np.linspace(0,1,65)],.028,'bronze',9)
    curve_tube(f'AST_Captain_Seat_Back_SideRail_{s}',[chair_back(0 if s<0 else 1,t,False) for t in np.linspace(0,1,60)],.017,'satin',8)
    curve_tube(f'AST_Captain_Seat_Arm_Cast_{s}',[(s*.61,.63,cz-.35),(s*.63,.95,cz-.25),(s*.62,1.00,cz+.28),(s*.54,.97,cz+.53)],.06,'satin')
    curve_tube(f'AST_Captain_Seat_Arm_Leather_{s}',[(s*.63,.997,cz-.22),(s*.625,1.02,cz+.28),(s*.55,1.01,cz+.50)],.073,'upholstery_dark')
    box(f'AST_Captain_Seat_Control_Pad_{s}',(s*.635,1.09,cz+.00),(.20,.023,.31),'glass')
    for j in range(7):
        box(f'AST_Captain_Seat_Control_Key_{s}_{j}',(s*.635 + ((j%2)-.5)*.065,1.110,cz-.09+(j//2)*.063),(.048,.009,.033),'coollight' if j==0 else 'satin')
# aft-facing seat shell accent: three raised cushioned contour bands and a metal center spine.
for t in [.22,.50,.78]:
    curve_tube(f'AST_Captain_Seat_Outer_Rear_Recess_{int(t*100)}',
        [tuple(np.asarray(chair_back(u,t,False))+[0,0,.013]) for u in np.linspace(.18,.82,56)],
        .010,'upholstery_dark',7)
curve_tube('AST_Captain_Seat_Rear_Center_Stem',
    [tuple(np.asarray(chair_back(.50,t,False))+[0,0,.026]) for t in np.linspace(.16,.89,64)],
    .018,'bronze',8)
for ss in [-1,1]:
    curve_tube(f'AST_Captain_Seat_Rear_Piping_{ss}',
      [tuple(np.asarray(chair_back(.50+ss*.29,t,False))+[0,0,.018]) for t in np.linspace(.08,.94,64)],
      .012,'satin',7)
# horizontal stitch lines from real geometry crossing front fabric
for t in [.23,.47,.69,.85]:
    curve_tube('AST_Captain_Seat_Stitch_'+str(int(100*t)),[tuple(np.array(chair_back(u,t,True))+[0,0,-.008]) for u in np.linspace(.19,.81,52)],.006,'upholstery_dark',6)
# headrest
sweep_shell('AST_Captain_Headrest',22,32,lambda u,v:(.35*(2*u-1)*math.sqrt(max(.02,1-(2*u-1)**4)),1.98+.20*v,cz+.48-.045*math.sin(u*PI)),'upholstery_dark',1,1)

# COMMAND PYLONS: two independent integrated curved shells and recessed screen mounts
for s in (-1,1):
    x=s*1.34
    box(f'AST_Command_Pylon_Base_{s}',(x,.59,.55),(.63,.98,1.02),'console',rotation=s*.16)
    box(f'AST_Command_Pylon_Bronze_Heel_{s}',(x,.24,.55),(.65,.07,1.04),'bronze',rotation=s*.16)
    # actual slanted articulated screen support, distinct from a flat cube
    pts=[(x+dx,cy,czx) for dx,cy,czx in [(-.39,.98,.98),(.39,.98,.98),(.39,1.31,.04),(-.39,1.31,.04)]]
    panel4(f'AST_Command_Instrument_Housing_{s}',pts,'rubber')
    curve_tube(f'AST_Command_Satin_Bezel_{s}',pts+[pts[0]],.038,'bronze')

# HELM: one continuous, rounded, flowing desk shell from material across the bridge.
def desk_curve(x):return -3.72+.25*(x/2.76)**2

def desk_skin(u,v):
    x=(u-.5)*5.92
    z0=desk_curve(x)
    # front/back edge; very subtle ergonomic concavity
    return (x,.47+.71*v-.045*math.sin(u*PI), z0+.64-1.36*v)
sweep_shell('AST_Flight_Desk_Raked_Molded_Console',26,96,desk_skin,'console',4,2.4)
# base molding curved vertical solid
for zoff,y,material in [(.73,.21,'shell'),(.80,.27,'bronze')]:
    curve_tube('AST_Flight_Desk_Base_'+material,[(x,y,desk_curve(x)+zoff) for x in np.linspace(-2.96,2.96,100)],.04,material)
curve_tube('AST_Flight_Desk_Upper_Satin_Rim',[(x,1.22,desk_curve(x)-.72) for x in np.linspace(-2.96,2.96,100)],.049,'bronze',12)
# slanted instrument glass planes; each one is recessed and separate from underlying shell
for i,x in enumerate(np.linspace(-2.28,2.28,6)):
    z=desk_curve(x)
    panel4(f'AST_Flight_Screen_Recess_{i}',[(x-.38,1.165,z-.67),(x+.38,1.165,z-.67),(x+.38,.94,z+.16),(x-.38,.94,z+.16)],'glass')
    box(f'AST_Flight_Desk_Keyboard_{i}',(x,.99,z+.27),(.62,.018,.21),'rubber')
    for j in range(9):
        box(f'AST_Flight_Desk_Key_{i}_{j}',(x-.275+j*.07,1.007,z+.30),(.038,.007,.045),'satin' if j%4 else 'coollight')
# side pylons supporting desk
for x in (-2.66,2.66):
    box(f'AST_Flight_Cast_Endcap_{x}',(x,.69,desk_curve(x)),(.15,1.12,1.29),'bronze')

# HELM SUPPORT SEATING (less detailed than hero captain chair; future high-detail pass)
for s in (-1,1):
    x=s*1.23; z=-2.13
    cyl(f'AST_Helm_Chair_Plinth_{s}',(x,.38,z),.22,.47,'satin',40)
    cyl(f'AST_Helm_Chair_Seat_{s}',(x,.70,z),.43,.14,'upholstery',46)
    sweep_shell(f'AST_Helm_Chair_Back_{s}',25,32,lambda u,v:(x+(u-.5)*.84,.82+v*.96,z+.25+v*.18-.045*math.sin(PI*u)),'upholstery',1,2)
    curve_tube(f'AST_Helm_Chair_Arms_{s}',[(x-.48,.73,z-.12),(x-.48,.99,z-.12),(x-.48,.98,z+.25)],.04,'satin')
    curve_tube(f'AST_Helm_Chair_RightArm_{s}',[(x+.48,.73,z-.12),(x+.48,.99,z-.12),(x+.48,.98,z+.25)],.04,'satin')

# SCIENCE GALLERY: clean wall terminals and face panels, avoid excessive repeated small detail
for s in [-1,1]:
    for k in range(4):
        x=s*(2.46+k*.90);z=4.10+.20*math.sin(k*PI/3)
        box(f'AST_Science_Console_Cast_{s}_{k}',(x,.59,z),( .75,1.03,1.04),'shell',rotation=s*.10)
        box(f'AST_Science_Console_Glass_{s}_{k}',(x,1.15,z-.22),(.69,.035,.72),'glass',rotation=s*.10)
        box(f'AST_Science_Console_UnderLight_{s}_{k}',(x,.39,z-.49),(.54,.015,.025),'coollight')
    # aft wall vertical science terminal bays
    for k in range(3):
        x=s*(2.0+k*1.22)
        box(f'AST_Aft_Science_Bezel_{s}_{k}',(x,2.21,5.95),(1.07,1.49,.10),'bronze')
        box(f'AST_Aft_Science_Glass_{s}_{k}',(x,2.21,5.85),(.91,1.32,.03),'glass')

# FIXTURE DETAILS AND SET PLATES
for i in range(18):
    a=i*2*PI/18;x=2.35*math.sin(a);z=.96+1.96*math.cos(a)
    cyl(f'AST_Command_Deck_Ring_Fastener_{i}',(x,.331,z),.018,.015,'bronze',12)
for s in [-1,1]:
    for i in range(4):
        box(f'AST_Viewer_Frame_Fastener_{s}_{i}',(s*3.47,1.15+i*.52,-5.77),(.024,.036,.024),'satin')


def build(dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    p=dest/'asteria-bridge-shell.glb'
    data=SCENE.export(file_type='glb')
    p.write_bytes(data)
    STATS['glbBytes']=len(data)
    STATS['artifacts']=[p.name]
    (dest/'asset-report.json').write_text(json.dumps(STATS,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(STATS,indent=2))
    return p

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'dist'/'models'))
    build(ap.parse_args().out)