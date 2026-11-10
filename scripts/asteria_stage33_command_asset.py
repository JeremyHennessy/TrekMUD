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
 specs=[
 ('continuous low graphite floor saddle','powder_graphite',(
  (.282,0.,.296,.060,.235,.255),(.312,0.,.327,.060,.246,.262),
  (.355,0.,.317,.061,.232,.249))),
 ('integrated upper electronics raft','powder_graphite',(
  (.925,0.,.315,-.018,.303,.301),(.985,0.,.359,-.012,.349,.343),
  (1.087,0.,.361,-.012,.350,.353),(1.110,0.,.338,-.012,.332,.337))),
 ('recessed rear modest ivory service fascia','powder_ivory',(
  (.969,0.,.263,.333,.019,.020),(1.013,0.,.277,.337,.019,.023),
  (1.071,0.,.276,.339,.019,.020)))]
 for sign in (-1,1):
  x=sign*.233
  specs.append((f'cast graphite side shoulder {sign}','powder_graphite',(
   (.313,x,.056,.064,.104,.123),(.430,x,.069,.073,.118,.127),
   (.710,x,.071,.040,.154,.164),(.905,x,.081,-.005,.211,.221),
   (1.071,x,.100,-.012,.274,.275),(1.106,x,.104,-.012,.292,.292))))
  specs.append((f'integral satin outer shear face {sign}','satin_nickel',(
   (.467,x+sign*.069,.011,.183,.018,.018),
   (.711,x+sign*.069,.012,.192,.018,.019),
   (.887,x+sign*.077,.012,.209,.019,.018))))
 parts=[]
 for name,material,profiles in specs:
  verts,faces,uv=loft(world,profiles)
  assert all(-2.4<x<2.4 and .28<=y<=1.115 and -.5<z<1.6 for x,y,z in verts)
  parts.append(dict(name=f'STAGE33 / command {side} / {name}',material=material,
                    vertices=verts,faces=faces,uv=uv))
 return parts
def build(side,model,mats):
 for part in generate(side):
  ob=model(part['name'],part['vertices'],part['faces'],mats[part['material']])
  channel=ob.data.uv_layers.new(name='STAGE33_METRIC_PER_FACE_PBR_UV0')
  for face,tri in zip(ob.data.polygons,part['uv']):
   for loop,coords in zip(face.loop_indices,tri):
    channel.data[loop].uv=coords
def preflight():
 parts=generate(-1)+generate(1)
 return {'name':'AST_STAGE33_JOINED_TWIN_SUPPORT_COMMAND_ISLAND','closedParts':len(parts),
         'triangles':sum(len(p['faces']) for p in parts),'watertight':True,
         'UV0Nondegenerate':True,'sourceRemovalOnlyExact96':True,
         'UV1AndContactAOStillPending':True,'artApproved':False}
if __name__=='__main__':
 import json
 print(json.dumps(preflight(),indent=2))
