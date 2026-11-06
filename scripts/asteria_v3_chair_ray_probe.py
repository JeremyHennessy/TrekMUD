#!/usr/bin/env python3
"""Inspect V3 chair-camera ray hits directly in immutable extracted triangle arrays.

Fast, read-only pre-Blender evidence: hit order, material IDs, vertex palette,
normals and geometry. No rendering, source edits or PADD/campaign interaction.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
import numpy as np

MATERIAL={
 0:"architectural accent",1:"carpet",2:"acoustic shell",
 3:"cast construction",4:"satin metal",5:"upholstery",
 6:"instrument atlas",7:"smoked glass",8:"practical diffuser",
}
CAMERA=(0.0,1.67,-0.85)
LENS_MM=48.
SENSOR_MM=36.
ASPECT=960/600

def parse():
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path,default=Path("_v5_mesh_capture"))
 p.add_argument("--out",type=Path,default=Path("_v5_mesh_capture/chair-ray-probe.json"))
 return p.parse_args()

def unit(v):
 n=float(np.linalg.norm(v))
 return v/max(n,1e-12)

def hits(tri,material,color,vertex_normal,origin,direction):
 # Double-sided Möller–Trumbore, no BVH dependency. 106,988 triangles x 49 rays.
 v0=tri[:,0,:];e1=tri[:,1,:]-v0;e2=tri[:,2,:]-v0
 d=np.asarray(direction,dtype=np.float64)
 p=np.cross(d,e2)
 det=np.einsum("ij,ij->i",e1,p)
 nonzero=np.abs(det)>1e-10
 inverse=np.zeros_like(det)
 inverse[nonzero]=1./det[nonzero]
 to=np.asarray(origin,dtype=np.float64)-v0
 u=np.einsum("ij,ij->i",to,p)*inverse
 q=np.cross(to,e1)
 v=np.einsum("j,ij->i",d,q)*inverse
 t=np.einsum("ij,ij->i",e2,q)*inverse
 good=nonzero&(u>=-1e-6)&(v>=-1e-6)&((u+v)<=1+1e-6)&(t>.035)
 ids=np.where(good)[0]
 if not len(ids):return []
 ids=ids[np.argsort(t[ids])][:6]
 found=[]
 for i in ids:
  geo=unit(np.cross(e1[i],e2[i]))
  vn=unit(vertex_normal[i].mean(axis=0))
  col=color[i].mean(axis=0)
  m=int(material[i,0])
  found.append({
    "triangle":int(i),"materialId":m,"material":MATERIAL.get(m,"other"),
    "distance":round(float(t[i]),5),"vertexColor":np.round(col,4).tolist(),
    "geometricNormal":np.round(geo,4).tolist(),
    "vertexNormal":np.round(vn,4).tolist(),
    "normalDotCameraRay":round(float(np.dot(vn,-d)),4),
    "point":np.round(np.asarray(origin)+d*t[i],4).tolist(),
  })
 return found

def main():
 args=parse();src=args.source
 P=np.load(src/"positions.npy").reshape(-1,3)
 N=np.load(src/"normals.npy").reshape(-1,3)
 C=np.load(src/"colors.npy").reshape(-1,3)
 M=np.load(src/"materials.npy").reshape(-1)
 assert len(P)==len(N)==len(C)==len(M)==320964
 tri=P.reshape(-1,3,3).astype(np.float64)
 norm=N.reshape(-1,3,3).astype(np.float64)
 col=C.reshape(-1,3,3).astype(np.float64)
 mat=M.reshape(-1,3)
 assert np.all(mat==mat[:,0:1]),"Material changes within a triangle"
 origin=np.array(CAMERA,dtype=np.float64)
 # Blender chair camera points toward (0,1.53,+2.15), pitch .14/3.
 half_width=SENSOR_MM/(2*LENS_MM)
 half_height=half_width/ASPECT
 samples=[]
 for v in (-.6,-.4,-.2,0,.2,.4,.6):
  for u in (-.6,-.4,-.2,0,.2,.4,.6):
   direction=unit(np.array([u*half_width,(-.14/3)+v*half_height,1.]))
   layers=hits(tri,mat,col,norm,origin,direction)
   samples.append({"u":u,"v":v,"hits":layers})
 centre=next(x for x in samples if x["u"]==0 and x["v"]==0)
 visible=Counter(s["hits"][0]["material"] if s["hits"] else "<no hit>" for s in samples)
 # Compare triangle winding with stored V3 vertex normals without changing either.
 e1=tri[:,1,:]-tri[:,0,:]
 e2=tri[:,2,:]-tri[:,0,:]
 geo=np.cross(e1,e2)
 geo/=np.maximum(1e-12,np.linalg.norm(geo,axis=1,keepdims=True))
 vn=norm.mean(axis=1)
 vn/=np.maximum(1e-12,np.linalg.norm(vn,axis=1,keepdims=True))
 alignment=np.einsum("ij,ij->i",geo,vn)
 centroids=tri.mean(axis=1)
 chair=(np.abs(centroids[:,0])<.95)&(centroids[:,1]>.45)&(centroids[:,1]<2.3)&(np.abs(centroids[:,2]-1.2)<.9)
 normal_alignment={}
 for m,name in MATERIAL.items():
  group=(mat[:,0]==m)
  area=group&chair
  normal_alignment[name]={
   "faces":int(group.sum()),
   "globalOpposed":int((group&(alignment<-.5)).sum()),
   "globalAligned":int((group&(alignment>.5)).sum()),
   "chairNearbyFaces":int(area.sum()),
   "chairNearbyOpposed":int((area&(alignment<-.5)).sum()),
   "chairNearbyAligned":int((area&(alignment>.5)).sum()),
  }
 report={
  "roomId":"AST-D01-BRIDGE",
  "sourceV3Blob":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
  "triangles":len(tri),
  "cameraWorldPosition":list(CAMERA),
  "cameraDirection":[0,-.14/3,1],
  "centreHits":centre["hits"],
  "firstSurfaceMaterials":dict(visible),
  "windingVsVertexNormal":normal_alignment,
  "samples":samples,
  "note":"This reports unlit geometry/material at ray hits, not a final pixel-lighting diagnosis.",
 }
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(report,indent=2)+"\n")
 print("First-surface materials:",dict(visible))
 print("Normal alignment:",json.dumps(normal_alignment["upholstery"],indent=2))
 print("Centre intersection stack:",json.dumps(centre["hits"][:4],indent=2))
 assert centre["hits"],"Camera centre sees no source triangles"

if __name__=="__main__":main()
