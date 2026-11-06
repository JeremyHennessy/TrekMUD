#!/usr/bin/env python3
"""Make a disposable V3 chair-winding A/B geometry copy, not a production edit.

Swaps triangle vertex ordering ONLY where the original upholstery's face winding
opposes its stored normals, in the physical command-chair bounding volume.
Coordinates, UV attachment, normals, colors, number of faces are unchanged.
Original extractor arrays remain immutable. Validation rejects unexpected counts.
"""
from pathlib import Path
import argparse
import json
import shutil
import numpy as np

def arg():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("_v5_mesh_capture"))
    p.add_argument("--out",type=Path,default=Path("_v5_mesh_capture_chair_winding_trial"))
    return p.parse_args()

def unit(values):
    return values/np.maximum(1e-12,np.linalg.norm(values,axis=1,keepdims=True))

def main():
    args=arg()
    if args.source.resolve()==args.out.resolve():
        raise ValueError("Must not modify the source extraction directory")
    raw={k:np.load(args.source/(k+".npy")) for k in ("positions","normals","colors","materials","uv")}
    p=raw["positions"].reshape(-1,3,3)
    n=raw["normals"].reshape(-1,3,3)
    m=raw["materials"].reshape(-1,3)
    assert len(p)==106988 and np.all(m==m[:,0:1])
    c=p.mean(axis=1)
    # Isolated original command chair; does not touch flight station chairs.
    near=(np.abs(c[:,0])<.95)&(c[:,1]>.45)&(c[:,1]<2.3)&(np.abs(c[:,2]-1.2)<.9)
    geo=unit(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]))
    vn=unit(n.mean(axis=1))
    dot=np.einsum("ij,ij->i",geo,vn)
    candidates=(m[:,0]==5)&near&(dot<-.5)
    count=int(candidates.sum())
    assert 5000<count<5300, f"Unexpected affected triangle count: {count}; abort"
    args.out.mkdir(parents=True,exist_ok=True)
    report={
      "sourceV3Blob":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
      "roomId":"AST-D01-BRIDGE",
      "triangles":len(p),
      "windingOnlyTrial":True,
      "reorderedUpholsteryFaces":count,
      "positionChanged":False,
      "note":"Research-only A/B, no source geometry or approved browser change.",
    }
    for name,a in raw.items():
        b=np.asarray(a).copy()
        size=1 if name=="materials" else (2 if name=="uv" else 3)
        batch=b.reshape(-1,3,size)
        batch[candidates]=batch[candidates][:,[0,2,1],:]
        np.save(args.out/(name+".npy"),b)
    assert np.allclose(
      raw["positions"].reshape(-1,3,3).sum(axis=1),
      np.load(args.out/"positions.npy").reshape(-1,3,3).sum(axis=1)), "Geometry positions altered"
    assert np.array_equal(
      np.sort(np.linalg.norm(p,axis=2),axis=1),
      np.sort(np.linalg.norm(np.load(args.out/"positions.npy").reshape(-1,3,3),axis=2),axis=1))
    shutil.copyfile(args.source/"atlas.png",args.out/"atlas.png")
    (args.out/"winding-trial-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
