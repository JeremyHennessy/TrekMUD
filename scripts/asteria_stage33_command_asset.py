#!/usr/bin/env python3
"""Stage33 isolated manufactured command island: paired solid undertray supports.
A reversible art trial, not a released model; original console screens and player untouched.
"""
from __future__ import annotations
from collections import Counter
from math import cos,sin,isfinite
def volume(vertices,faces):
 v=0.
 for i,j,k in faces:
  a,b,c=(vertices[n] for n in (i,j,k))
  v+=a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
 return v/6
def loft(world,profiles):
 verts=[]
 for y,xcentre,halfwidth,zcentre,front,rear in profiles:
  assert .28<=y<=1.115 and .01<halfwidth<.40 and .01<front<.42 and .01<rear<.42
  w=halfwidth;r=min(.024,w*.31,front*.31,rear*.31)
  pts=[(-w+r,-front),(w-r,-front),(w,-front+r),(w,rear-r),
       (w-r,rear),(-w+r,rear),(-w,rear-r),(-w,-front+r)]
  verts.extend(world(x+xcentre,y,z+zcentre) for x,z in pts)
 faces=[]
 for ring in range(len(profiles)-1):
  for j in range(8):
   a=ring*8+j;b=ring*8+(j+1)%8;c=(ring+1)*8+j;d=(ring+1)*8+(j+1)%8
   faces.extend(((a,b,c),(b,d,c)))
 last=(len(profiles)-1)*8
 for j in range(1,7):
  faces.extend(((0,j+1,j),(last,last+j,last+j+1)))
 if volume(verts,faces)<0:faces=[(i,k,j) for i,j,k in faces]
 assert volume(verts,faces)>.000002
 edges=Counter();dirs=Counter();uv=[]
 for i,j,k in faces:
  assert len({i,j,k})==3
  pts=[verts[i],verts[j],verts[k]]
  assert all(isfinite(x) for pt in pts for x in pt)
  u=[pts[1][q]-pts[0][q] for q in range(3)]
  v=[pts[2][q]-pts[0][q] for q in range(3)]
  n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
  axis=max(range(3),key=lambda q:abs(n[q]))
  dx,dy=((1,2),(0,2),(0,1))[axis]
  xy=[(pt[dx]*2.2,pt[dy]*2.2) for pt in pts]
  area=(xy[1][0]-xy[0][0])*(xy[2][1]-xy[0][1])-(xy[2][0]-xy[0][0])*(xy[1][1]-xy[0][1])
  assert abs(area)>1e-9,('Invalid scanned PBR UV0',i,j,k)
  uv.append(xy)
  for a,b in ((i,j),(j,k),(k,i)):
   edges[tuple(sorted((a,b)))]+=1;dirs[(a,b)]+=1
 assert all(n==2 for n in edges.values())
 assert all(dirs[(a,b)]==dirs[(b,a)]==1 for a,b in edges)
 return verts,faces,uv
def generate(side):
 assert side in (-1,1)
 x0,z0=side*1.27,.58;angle=side*.24;ca,sa=cos(angle),sin(angle)
 def world(x,y,z):return (x0+x*ca-z*sa,y,z0+x*sa+z*ca)
 # Stage33 coherent architected option B: manufactured cantilever, not a
 # solid pedestal. This is one reversible foreground assembly trial.
 # The floor shoe, swept side load paths, flush upper cassette, service
 # fascia and inset shear reveal are designed as ONE connected system.
 # Existing physical instruments/glass/buttons and room/player stay fixed.
 specs=[
 ('floor-mounted double-foot load shoe','powder_graphite',(
  (.282,0.,.305,.084,.228,.238),(.322,0.,.346,.080,.250,.258),
  (.356,0.,.324,.077,.238,.243))),
 ('curved thin upper instrument cassette','powder_graphite',(
  (.977,0.,.319,-.018,.288,.300),
  (1.020,0.,.356,-.013,.329,.343),
  (1.085,0.,.362,-.010,.337,.353),
  (1.112,0.,.338,-.010,.331,.340))),
 ('sunk rear ceramic service apron attached to cassette','powder_ivory',(
  (.990,0.,.265,.322,.027,.034),
  (1.040,0.,.275,.335,.025,.035),
  (1.101,0.,.274,.336,.025,.032)))]
 for sign in (-1,1):
  # Each narrow sweeps inward from its foot then flares into the tray.
  # No lower slab spanning the kneehole; open space is true geometry.
  path=(
   (.315,sign*.248,.055,.079,.095,.119),
   (.430,sign*.247,.053,.086,.100,.128),
   (.628,sign*.259,.055,.080,.132,.151),
   (.799,sign*.270,.060,.052,.171,.190),
   (.964,sign*.273,.082,.005,.248,.256),
   (1.106,sign*.256,.094,-.012,.278,.283))
  specs.append((f'one-piece curved load-bearing side fork {sign}',
                'satin_nickel',path))
  # Actual inset powder-coated service channel follows the metal side
  # cast surface: no unsupported decorative free-standing rails.
  specs.append((f'flush graphite access-channel in structural fork {sign}',
                'powder_graphite',(
   (.463,sign*.294,.012,.171,.016,.017),
   (.710,sign*.315,.011,.176,.018,.019),
   (.897,sign*.326,.012,.167,.020,.021))))
 parts=[]
 for name,material,profiles in specs:
  verts,faces,uv=loft(world,profiles)
  assert all(-2.4<x<2.4 and .28<=y<=1.115 and -.5<z<1.6 for x,y,z in verts)
  parts.append(dict(name=f'STAGE33 / command {side} / {name}',material=material,
                    vertices=verts,faces=faces,uv=uv))
 return parts
def build(side,model,mats):
 # One exact non-overlapping 30x30 UV1 atlas for all 840 Stage33
 # triangles, independent from the per-face metric scanned-PBR UV0.
 # Every mesh receives the SAME atlas texture but DIFFERENT cells.
 per_side=sum(len(part['faces']) for part in generate(-1))
 assert per_side==420,per_side
 offset=per_side if side==1 else 0
 part_offset=0
 for part in generate(side):
  key='stage33_ao_'+part['material']
  if key not in mats:
   cloned=mats[part['material']].copy()
   cloned.name='Asteria / Stage33 distinct AO '+part['material']
   mats[key]=cloned
  ob=model(part['name'],part['vertices'],part['faces'],mats[key])
  diffuse=ob.data.uv_layers.new(name='STAGE33_METRIC_PER_FACE_PBR_UV0')
  contact=ob.data.uv_layers.new(name='STAGE33_LOCAL_CONTACT_UV1')
  for i,(face,tri) in enumerate(zip(ob.data.polygons,part['uv'])):
   assert len(face.loop_indices)==3
   for loop,coords in zip(face.loop_indices,tri):
    diffuse.data[loop].uv=coords
   tile=offset+part_offset+i
   assert 0<=tile<900
   col,row=tile%30,tile//30
   uvs=(((col+.13)/30,(row+.13)/30),
        ((col+.86)/30,(row+.13)/30),
        ((col+.13)/30,(row+.86)/30))
   for loop,uv in zip(face.loop_indices,uvs):
    contact.data[loop].uv=uv
  part_offset+=len(part['faces'])
 assert part_offset==420

def preflight():
 parts=generate(-1)+generate(1)
 return {'name':'AST_STAGE33_JOINED_TWIN_SUPPORT_COMMAND_ISLAND','closedParts':len(parts),
         'triangles':sum(len(p['faces']) for p in parts),'watertight':True,
         'UV0Nondegenerate':True,'sourceRemovalOnlyExact96':True,
         'UV1NonOverlappingAtlasSourceDefined':True,
          'UV1BakedContactAORequiresExportValidation':True,'artApproved':False}
if __name__=='__main__':
 import json
 print(json.dumps(preflight(),indent=2))
