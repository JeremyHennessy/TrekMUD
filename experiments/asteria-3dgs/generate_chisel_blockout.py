#!/usr/bin/env python3
"""Generate a neutral 3D layout guide for USS Asteria bridge visual generation.

This is an approximate conditioning blockout: exact canon only names the stable
room and approved neighbor; the physical dimensions are from the existing V3
viewer's internal geometry, NOT a licensed television ship deck plan.
"""
import json, argparse, numpy as np, trimesh
from pathlib import Path
from trimesh.transformations import rotation_matrix

W,D=7.55,6.55
scene=trimesh.Scene()
colors={'walls':[167,167,166,255],'floor':[104,115,129,255],'rim':[128,122,128,255],
        'command':[174,156,158,255],'chair':[116,100,115,255],'flight':[135,150,154,255],
        'science':[132,147,150,255],'opening':[48,53,62,255],'ceiling':[190,186,183,255]}

def add(name,mesh,mat):
    m=mesh.copy();m.visual.vertex_colors=np.tile(np.asarray(colors[mat],dtype='u1'),(len(m.vertices),1))
    scene.add_geometry(m,geom_name=name,node_name=name)

def block(name,x,y,z,sx,sy,sz,mat):
    m=trimesh.creation.box(extents=[sx,sy,sz]);m.apply_translation([x,y,z]);add(name,m,mat)

# The visual-only room skin is approximate, incomplete at the front viewer and aft portal.
# The elliptical floor is a recognizable layout guide but not an exact collision mesh.
# trimesh annulus lies along Z. Build an elliptical flat disk in X-Z at y=0.
t=np.linspace(0,2*np.pi,128,endpoint=False)
verts=[[0,.012,0]]+[[W*np.sin(a),.012,D*np.cos(a)] for a in t]
faces=[[0,i+1,((i+1)%128)+1] for i in range(128)]
add('AST-D01-BRIDGE__floor-ellipse',trimesh.Trimesh(vertices=verts,faces=faces,process=False),'floor')
for i in range(72):
    a=i*2*np.pi/72; b=(i+1)*2*np.pi/72; mid=(a+b)/2
    # Room viewer at front (negative z), access at rear (positive z).
    if abs(((mid+np.pi)%(2*np.pi))-np.pi)<.18:continue # aft opening
    if abs(((mid-np.pi+np.pi)%(2*np.pi))-np.pi)<.48:continue # forward view
    xx,zz=.97*W*np.sin(mid),.97*D*np.cos(mid)
    length=np.hypot(W*(np.sin(b)-np.sin(a)),D*(np.cos(b)-np.cos(a)))
    m=trimesh.creation.box(extents=[max(.16,length),3.6,.13])
    yaw=np.arctan2(-D*np.sin(mid),W*np.cos(mid))
    m.apply_transform(rotation_matrix(-yaw,[0,1,0]));m.apply_translation([xx,1.80,zz]);add(f'AST_Bridge_Structural_Wall_{i:02d}',m,'walls')
# Neutral structural soffit: no invented LED décor or detailed set claim.
for j in range(28):
    a=2*np.pi*j/28
    length=.70
    x,z=(W*.72*np.sin(a), D*.72*np.cos(a))
    block(f'AST_Ceiling_Diffuser_Bay_{j:02d}',x,3.88,z,.65,.07,length,'ceiling')
# Command dais center z ~1.11 and captain facing forward.
block('AST_Command_Dais_Step',0,.19,1.11,3.72,.30,3.10,'command')
block('AST_Captain_Chair_Pedestal',0,.54,1.22,.62,.53,.65,'chair')
block('AST_Captain_Chair_Seat',0,.88,1.15,1.04,.17,.86,'chair')
block('AST_Captain_Chair_Back',0,1.45,1.57,1.05,1.25,.20,'chair')
for s in (-1,1):
    block(f'AST_Command_Console_{s}',s*1.27,.70,.57,.75,1.03,1.12,'command')
# The flight desk's continuous sweep is approximated by adjacent blocks.
for i,x in enumerate(np.linspace(-2.55,2.55,16)):
    z=-3.24+.24*(x/2.45)**2
    block(f'AST_Flight_Dais_Module_{i:02d}',float(x),.66,float(z),.35,1.00,.98,'flight')
for s in (-1,1):
    block(f'AST_Helm_Seat_{s}',s*1.15,.79,-2.05,.67,.86,.75,'chair')
    block(f'AST_Science_Gallery_{s}',s*3.52,.30,4.20,3.7,.60,1.80,'science')
    block(f'AST_Science_Console_{s}',s*4.30,1.40,4.68,2.55,1.70,.35,'science')
    block(f'AST_Side_Hatch_Sealed_{s}',s*7.03,1.67,-.28,.26,3.1,1.95,'walls')
block('AST_Forward_Viewscreeen_Frame',0,2.18,-6.28,6.75,3.20,.18,'opening')
block('AST_Aft_Access_Hub_Opening',0,1.56,6.17,1.95,3.06,.22,'opening')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a=a.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(scene.export(file_type='glb'))
    report={'source':'Original V3 TrekMUD visual dimensions','format':'glb','use':'layout-conditioning-only','not':'canonical room construction blueprint','roomId':'AST-D01-BRIDGE',
            'approvedNeighbor':'AST-D01-HUB-C','meshCount':len(scene.geometry),'bounds':scene.bounds.tolist(),'sizeBytes':a.out.stat().st_size}
    a.out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))