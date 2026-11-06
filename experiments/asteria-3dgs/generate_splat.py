#!/usr/bin/env python3
"""Isolated demonstration splat of the existing Asteria captain's chair.

Deliberately synthetic. It samples the approved V4 glTF chair mesh and its base-color
textures; it does NOT train a Gaussian field from photographic observations.
This is for testing Spark/Three.js hybrid occlusion and camera compatibility only.
"""
import argparse
import json
from pathlib import Path
import struct
import numpy as np
import trimesh
from PIL import Image

SELECT_PREFIXES = ('AST_Captain_Seat_Padded_Contour', 'AST_Captain_Seat_Outer_Composite_Shell',
    'AST_Captain_Seat_3D_Padded_Pan', 'AST_Captain_Headrest', 'AST_Captain_Seat_Arm_Leather_',
    'AST_Captain_Seat_Arm_Cast_', 'AST_Captain_Seat_Back_SideRail_',
    'AST_Captain_Seat_Outer_Rear_Recess_', 'AST_Captain_Seat_Control_Pad_')


def make_splat(glb: Path, output: Path, target: int=24000, seed: int=63542) -> dict:
    scene = trimesh.load(str(glb), force='scene')
    entries=[]
    for name in sorted(scene.graph.nodes_geometry):
        if not name.startswith(SELECT_PREFIXES):
            continue
        trans, geomname = scene.graph[name]
        g = scene.geometry[geomname]
        if g.faces.size == 0 or g.area<=0:
            continue
        entries.append((name, g, trans))
    if not entries:
        raise RuntimeError('No recognized Asteria captain-chair geometry in source GLB')
    areas=np.array([g.area for _,g,_ in entries]); areas=areas/areas.sum()
    counts=np.maximum(35,np.floor(areas*target).astype(int))
    rng=np.random.default_rng(seed)
    payload=bytearray()
    aabb=np.array([[np.inf]*3,[-np.inf]*3],dtype=float)
    stored=0
    for (name,mesh,transform),N in zip(entries,counts):
        # trimesh uses numpy global RNG for sample_surface; seed each call deterministically.
        point,face=trimesh.sample.sample_surface(mesh,int(N),seed=int(rng.integers(1,2**30)))
        if not len(face): continue
        normal=mesh.face_normals[face]
        # Interpolated UVs from actual mesh, preserving its material texture.
        uv=mesh.visual.uv if hasattr(mesh.visual,'uv') else None
        if uv is not None:
            bary=trimesh.triangles.points_to_barycentric(mesh.triangles[face],point)
            uvp=np.einsum('ij,ijk->ik',bary,uv[mesh.faces[face]])
            img=getattr(mesh.visual.material,'baseColorTexture',None)
            if img is not None:
                im=np.asarray(img.convert('RGBA'))
                h,w=im.shape[:2]
                col=im[np.clip(((1-uvp[:,1])%1*h).astype(int),0,h-1),np.clip(((uvp[:,0])%1*w).astype(int),0,w-1),:3]
            else: col=np.tile([160,150,158],(int(N),1))
        else:
            col=np.tile([160,150,158],(int(N),1))
        # Sample flat lighting from a fixed original-key direction: splats embed their appearance.
        key=np.array([-0.35,0.85,-0.4]);key/=np.linalg.norm(key)
        lam=np.maximum(0,normal@key)
        shade=np.clip(.63+.34*lam,0,1.15)
        col=np.clip(col*shade[:,None],0,255).astype('u1')
        alpha=np.full((len(col),1),240,dtype='u1')
        rgba=np.concatenate([col,alpha],axis=1)
        # A local patch (tangent X,Y) with thin normal direction Z.
        up=np.array([0.,1.,0.]); tangent=np.cross(np.tile(up,(len(normal),1)),normal)
        near=np.linalg.norm(tangent,axis=1)<.01
        tangent[near]=np.cross(np.tile([1.,0.,0.],(near.sum(),1)),normal[near])
        tangent/=np.maximum(1e-10,np.linalg.norm(tangent,axis=1,keepdims=True))
        # Quaternion from +Z to the normal; XY footprint is effectively circular.
        q=np.column_stack([1+normal[:,2],-normal[:,1],normal[:,0],np.zeros(len(normal))])
        south=q[:,0]<1e-5
        q[south]=[0.,1.,0.,0.]
        q/=np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-10)
        q8=np.rint(q*128+128).clip(0,255).astype('u1')
        # Estimate area/splat, clamp to prevent giant floaters from small discrete parts.
        base=np.sqrt(mesh.area/int(N)/np.pi)
        jitter=rng.uniform(.77,1.23,len(point))
        scale=np.stack([base*jitter,base/jitter,np.full(len(point),max(.002,base*.15))],axis=1).astype('<f4')
        point=np.column_stack([point,np.ones(len(point))])@transform.T
        point=point[:,:3].astype('<f4')
        aabb[0]=np.minimum(aabb[0],point.min(axis=0));aabb[1]=np.maximum(aabb[1],point.max(axis=0))
        for i in range(len(point)):
            payload.extend(struct.pack('<6f',*point[i],*scale[i]));payload.extend(rgba[i].tobytes());payload.extend(q8[i].tobytes())
        stored+=len(point)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(payload)
    report={'source':str(glb),'format':'raw-splat-32-byte','training':'none: direct sampled V4 geometry',
        'purpose':'technical hybrid-render comparison only', 'room_id':'AST-D01-BRIDGE',
        'gaussians':stored,'meshes_sampled':len(entries),'file_bytes':len(payload),'bounds':aabb.tolist()}
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--count',type=int,default=24000)
    a=p.parse_args();print(json.dumps(make_splat(a.glb,a.out,a.count),indent=2))