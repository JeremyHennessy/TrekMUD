#!/usr/bin/env python3
"""Stage35 opt-in source-replacing curved flight console, architectural-envelope GLB.

Original 135 envelope meshes, UV1, texture data, material dictionary and binary
prefix are exact SHA-pinned. The new 14 closed parts have UV0 but UV1/GI is
NOT accepted or approved, and this workflow must never deploy automatically.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from pathlib import Path
from asteria_stage35_flight_geometry import generate,preflight
ENVELOPE="models/asteria-realistic-architectural-envelope-08.glb"
PIN="b43096fed31334511f6d78b0b3b254863ec90349d7490059e44d957c9f2e688c"
def sha(b):return hashlib.sha256(b).hexdigest()
def pad(b):return b+bytes((-len(b))%4)
def read(b):
    assert struct.unpack_from("<4sII",b,0)==(b"glTF",2,len(b))
    size,kind=struct.unpack_from("<I4s",b,12)
    assert kind==b"JSON"
    doc=json.loads(b[20:20+size]);off=20+size
    length,kind=struct.unpack_from("<I4s",b,off)
    assert kind==b"BIN\x00" and off+8+length==len(b)
    raw=b[off+8:]
    assert doc["buffers"][0]["byteLength"]==len(raw)
    return doc,raw
def put(doc,raw,values,target):
    raw=pad(raw);values=pad(values)
    doc["bufferViews"].append({"buffer":0,"byteOffset":len(raw),
                               "byteLength":len(values),"target":target})
    return raw+values,len(doc["bufferViews"])-1
def accessor(doc,v,ct,n,kind,bounds=None):
    spec={"bufferView":v,"componentType":ct,"count":n,"type":kind}
    if bounds:spec["min"],spec["max"]=bounds
    doc["accessors"].append(spec)
    return len(doc["accessors"])-1
def triangles(doc):
    return sum(doc["accessors"][p["indices"]]["count"]//3
               for mesh in doc["meshes"] for p in mesh["primitives"])
def run(control,candidate,proof):
    original=(control/ENVELOPE).read_bytes()
    assert sha(original)==PIN
    doc,raw=read(original)
    assert len(doc["meshes"])==len(doc["nodes"])==135 and triangles(doc)==27848
    assert len(doc["scenes"])==1 and len(doc["scenes"][0]["nodes"])==135
    assert len(doc["buffers"])==1
    assert doc["materials"][1]["name"]=="Architecture / original 112 exterior shell and capped edges / P"
    assert doc["materials"][3]["name"]=="Asteria / captured satin trim"
    assert doc["materials"][7]["name"]=="ZONE20 / engineered matte graphite hardware"
    keys=("meshes","nodes","materials","images","textures","samplers","bufferViews","accessors")
    exact={key:json.dumps(doc[key],sort_keys=True) for key in keys}
    original_binary=raw
    pre=preflight()
    names=[]
    for part in generate():
        verts,faces,uv=part["vertices"],part["faces"],part["face_uv"]
        assert len(faces)==len(uv)
        positions=[];normals=[];tex=[]
        for (a,b,c),mapped in zip(faces,uv):
            p,q,r=(verts[j] for j in (a,b,c))
            u=[q[j]-p[j] for j in range(3)]
            v=[r[j]-p[j] for j in range(3)]
            n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            length=math.sqrt(sum(x*x for x in n))
            assert length>1e-8 and len(mapped)==3
            for point,coord in zip((p,q,r),mapped):
                assert all(math.isfinite(c) for c in (*point,*coord))
                positions.extend(point)
                normals.extend(a/length for a in n)
                tex.extend(coord)
        total=len(faces)*3;views=[]
        for vals,target in ((positions,34962),(normals,34962),(tex,34962)):
            raw,view=put(doc,raw,struct.pack("<%sf"%len(vals),*vals),target)
            views.append(view)
        raw,indices=put(doc,raw,struct.pack("<%sI"%total,*range(total)),34963)
        limits=([min(positions[k::3]) for k in range(3)],
                [max(positions[k::3]) for k in range(3)])
        attrs={"POSITION":accessor(doc,views[0],5126,total,"VEC3",limits),
               "NORMAL":accessor(doc,views[1],5126,total,"VEC3"),
               "TEXCOORD_0":accessor(doc,views[2],5126,total,"VEC2")}
        idx=accessor(doc,indices,5125,total,"SCALAR",([0],[total-1]))
        mat={"powder_ivory":1,"powder_graphite":7,"satin_nickel":3}[part["material"]]
        mi=len(doc["meshes"]);name=part["name"]
        doc["meshes"].append({"name":name,"primitives":[
            {"attributes":attrs,"indices":idx,"material":mat,"mode":4}]})
        doc["nodes"].append({"mesh":mi,"name":name})
        doc["scenes"][0]["nodes"].append(mi)
        names.append(name)
    assert raw[:len(original_binary)]==original_binary
    for key in keys:
        old=json.loads(exact[key])
        assert doc[key][:len(old)]==old,("Original architecture changed",key)
    assert len(doc["meshes"])==len(doc["nodes"])==135+pre["closedMeshes"]
    assert triangles(doc)==27848+pre["triangles"]
    doc["buffers"][0]["byteLength"]=len(raw)
    text=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
    text+=b" "*((-len(text))%4)
    raw=pad(raw)
    glb=(struct.pack("<4sII",b"glTF",2,28+len(text)+len(raw))
       +struct.pack("<I4s",len(text),b"JSON")+text
       +struct.pack("<I4s",len(raw),b"BIN\x00")+raw)
    assert read(glb)[0]["buffers"][0]["byteLength"]==len(raw)
    (candidate/ENVELOPE).write_bytes(glb)
    app=(candidate/"app.js").read_text()
    guard="be!==27848||Te!==135"
    assert app.count(guard)==1
    app=app.replace(guard,
        f'be!=={27848+pre["triangles"]}||Te!=={135+pre["closedMeshes"]}',1)
    (candidate/"app.js").write_text(app)
    metapath=candidate/"models/envelope-manifest.json"
    meta=json.loads(metapath.read_text())
    assert meta["newEnvelopeTriangles"]==27848 and meta["meshObjects"]==135
    meta.update(newEnvelopeTriangles=27848+pre["triangles"],
                meshObjects=135+pre["closedMeshes"])
    meta["stage35OptionalGeometry"]={"sourceFlightDeskRemovedFaces":6476,
       "newFaces":pre["triangles"],"names":names,"newUV1OrGIProven":False,
       "artApproved":False,"releaseApproved":False}
    metapath.write_text(json.dumps(meta,indent=2)+"\n")
    record=dict(originalEnvelopeSHA256=PIN,candidateEnvelopeSHA256=sha(glb),
        allOriginalEnvelopeMeshesAndMaterialsExact=True,
        originalBinaryPrefixExact=True,newMeshes=pre["closedMeshes"],
        newTriangles=pre["triangles"],originalOpaqueFlightFacesRemoved=6476,
        newUV1ContactGIProven=False,artApproved=False,fullReleaseQA=False)
    proof.parent.mkdir(parents=True,exist_ok=True)
    proof.write_text(json.dumps(record,indent=2)+"\n")
    print("STAGE35_ARCHITECTURAL_FLIGHT_DESK",json.dumps(record),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("control","candidate","proof"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    run(a.control,a.candidate,a.proof)
