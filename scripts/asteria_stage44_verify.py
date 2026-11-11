#!/usr/bin/env python3
"""Independent glTF proof: Stage44 changes ONLY port-pylon texture mapping."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np

DT={5120:"i1",5121:"u1",5122:"i2",5123:"u2",5125:"u4",5126:"f4"}
W={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}
TARGET="Command / -1 / moulded eight-corner closed cast pedestal"
def glb(path):
    b=path.read_bytes()
    assert b[:4]==b"glTF" and struct.unpack_from("<I",b,8)[0]==len(b)
    pos=12;chunks={}
    while pos<len(b):
        length,kind=struct.unpack_from("<I4s",b,pos);pos+=8
        chunks[kind]=b[pos:pos+length];pos+=length
    return json.loads(chunks[b"JSON"]),chunks[b"BIN\x00"]
def acc(j,b,idx):
    a=j["accessors"][idx];v=j["bufferViews"][a["bufferView"]]
    dt=np.dtype("<"+DT[a["componentType"]]);w=W[a["type"]]
    offset=v.get("byteOffset",0)+a.get("byteOffset",0)
    stride=v.get("byteStride",dt.itemsize*w)
    return np.ndarray((a["count"],w),dtype=dt,buffer=b,offset=offset,strides=(stride,dt.itemsize)).copy()
def tris(j,b,prim):
    p=acc(j,b,prim["attributes"]["POSITION"]).astype("f8")
    ix=acc(j,b,prim["indices"]).astype("i8").reshape(-1,3)
    return p[ix]
def canonical(t):
    return sorted(tuple(sorted(tuple(round(float(v),5) for v in p) for p in tri)) for tri in t)
def verify(base,candidate):
    j0,b0=glb(base);j1,b1=glb(candidate)
    old={n["name"]:n for n in j0["nodes"] if "mesh" in n}
    new={n["name"]:n for n in j1["nodes"] if "mesh" in n}
    assert len(old)==90 and set(old)==set(new)
    assert TARGET in old
    unchanged=0;faces0=faces1=None;uv_good=0;uv_bad=0
    for name,n0 in old.items():
        n1=new[name]
        for key in ("matrix","rotation","scale","translation"):
            assert n0.get(key)==n1.get(key),(name,key)
        p0=j0["meshes"][n0["mesh"]]["primitives"]
        p1=j1["meshes"][n1["mesh"]]["primitives"]
        assert len(p0)==len(p1)==1,name
        a0=p0[0];a1=p1[0]
        mat0=j0["materials"][a0["material"]]["name"]
        mat1=j1["materials"][a1["material"]]["name"]
        assert mat0==mat1,name
        if name==TARGET:
            assert "TEXCOORD_0" not in a0["attributes"],"Original UV0 missing premise invalid"
            assert "TEXCOORD_0" in a1["attributes"],"UV0 not exported"
            faces0=tris(j0,b0,a0);faces1=tris(j1,b1,a1)
            assert len(faces0)==len(faces1)==76
            assert canonical(faces0)==canonical(faces1),"Source geometry changed"
            uvs=acc(j1,b1,a1["attributes"]["TEXCOORD_0"])
            indices=acc(j1,b1,a1["indices"]).reshape(-1,3)
            assert np.isfinite(uvs).all() and uvs.min()>=-1e-5 and uvs.max()<=1+1e-5
            utri=uvs[indices]
            area=np.abs(np.cross(utri[:,1]-utri[:,0],utri[:,2]-utri[:,0]))*.5
            uv_good=int((area>1e-9).sum());uv_bad=int((area<=1e-9).sum())
            assert uv_bad==0,(uv_good,uv_bad)
        else:
            assert a0["attributes"].keys()==a1["attributes"].keys(),name
            for at in a0["attributes"]:
                v0=acc(j0,b0,a0["attributes"][at]);v1=acc(j1,b1,a1["attributes"][at])
                assert v0.shape==v1.shape and np.allclose(v0,v1,atol=2e-6,rtol=0),(name,at)
            assert np.array_equal(acc(j0,b0,a0["indices"]),acc(j1,b1,a1["indices"])),name
            unchanged+=1
    assert unchanged==89
    return {"sourceGLBSHA256":hashlib.sha256(base.read_bytes()).hexdigest(),
      "candidateGLBSHA256":hashlib.sha256(candidate.read_bytes()).hexdigest(),
      "originalMeshNodes":len(old),"originalMeshNodesByteNumericIdentical":unchanged,
      "sourceExactPortCabinetFaces":len(faces1),"UV0NonDegenerateFaces":uv_good,
      "UV0DegenerateFaces":uv_bad,"newNodes":0,"removedNodes":0,
      "originalScreensSwitchesAndRimsPreserved":True,"artApproved":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();r=verify(a.base,a.candidate)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+"\n")
    print("STAGE44_UV0_SOURCE_PRESERVATION",json.dumps(r))
