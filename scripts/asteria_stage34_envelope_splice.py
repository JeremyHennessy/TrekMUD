#!/usr/bin/env python3
"""Stage34 NO-DEPLOY macro: append source-proven forward shell to pinned envelope GLB.
Original 135 meshes, materials, scans, AO maps and binary bytes are preserved.
This is ART-FIRST only; new UV1/GI and full QA are NOT established.
"""
import argparse,hashlib,json,math,struct
from pathlib import Path
from asteria_stage34_forward_hero import generate

ENVELOPE="models/asteria-realistic-architectural-envelope-08.glb"
PIN="b43096fed31334511f6d78b0b3b254863ec90349d7490059e44d957c9f2e688c"
APP_PIN="3a85cd7f60bb7523ff2f52d414de9be6e9c4b671a6b1a1c14e8ea73ee03c3baa"
def sha(b):return hashlib.sha256(b).hexdigest()
def pad(b):return b+bytes((-len(b))%4)
def read_glb(b):
    assert struct.unpack_from("<4sII",b,0)==(b"glTF",2,len(b))
    size,kind=struct.unpack_from("<I4s",b,12)
    assert kind==b"JSON"
    doc=json.loads(b[20:20+size]);offset=20+size
    length,kind=struct.unpack_from("<I4s",b,offset)
    assert kind==b"BIN\x00" and offset+8+length==len(b)
    raw=b[offset+8:]
    assert doc["buffers"][0]["byteLength"]==len(raw)
    return doc,raw
def write_glb(doc,raw):
    js=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
    js+=b" "*((-len(js))%4);raw=pad(raw)
    return (struct.pack("<4sII",b"glTF",2,28+len(js)+len(raw))
            +struct.pack("<I4s",len(js),b"JSON")+js
            +struct.pack("<I4s",len(raw),b"BIN\x00")+raw)
def accessor(doc,index,components,count,kind,bounds=None):
    a={"bufferView":index,"componentType":components,"count":count,"type":kind}
    if bounds:a["min"],a["max"]=bounds
    doc["accessors"].append(a)
    return len(doc["accessors"])-1
def add_buffer(doc,raw,contents,target):
    contents=pad(contents)
    doc["bufferViews"].append({"buffer":0,"byteOffset":len(raw),
                              "byteLength":len(contents),"target":target})
    return raw+contents,len(doc["bufferViews"])-1
def triangles(doc):
    return sum(doc["accessors"][p["indices"]]["count"]//3
        for m in doc["meshes"] for p in m["primitives"])
def inject(control,candidate,out):
    original=(control/ENVELOPE).read_bytes()
    assert sha(original)==PIN and sha((control/"app.js").read_bytes())==APP_PIN
    doc,raw=read_glb(original)
    assert len(doc["meshes"])==len(doc["nodes"])==135 and triangles(doc)==27848
    assert len(doc["scenes"])==1 and doc["scene"]==0
    assert len(doc["scenes"][0]["nodes"])==135 and len(doc["buffers"])==1
    assert doc["materials"][1]["name"]=="Architecture / original 112 exterior shell and capped edges / P"
    assert doc["materials"][3]["name"]=="Asteria / captured satin trim"
    assert doc["materials"][7]["name"]=="ZONE20 / engineered matte graphite hardware"
    protected={k:json.dumps(doc[k],sort_keys=True) for k in
        ("meshes","nodes","materials","images","textures","samplers",
         "bufferViews","accessors")}
    first_raw=raw;count_faces=0;names=[]
    mats={"powder_ivory":1,"powder_graphite":7,"satin_nickel":3}
    parts=generate()
    assert len(parts)==6
    for part in parts:
        faces=part["faces"];vs=part["vertices"];uvs=part["face_uv"]
        assert len(faces)>15 and len(faces)==len(uvs)
        assert part["material"] in mats and part["name"].startswith("STAGE34 / ")
        pos=[];normals=[];tex=[]
        for (a,b,c),uv in zip(faces,uvs):
            assert len({a,b,c})==3
            p,q,r=vs[a],vs[b],vs[c]
            u=[q[i]-p[i] for i in range(3)]
            v=[r[i]-p[i] for i in range(3)]
            n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            mag=math.sqrt(sum(t*t for t in n))
            assert mag>1e-10
            n=[x/mag for x in n]
            for vertex,tc in zip((p,q,r),uv):
                assert all(math.isfinite(z) for z in (*vertex,*tc))
                pos.extend(vertex);normals.extend(n);tex.extend(tc)
        count=len(faces)*3
        ids=[]
        for vals,target in ((pos,34962),(normals,34962),(tex,34962)):
            raw,view=add_buffer(doc,raw,struct.pack("<%sf"%len(vals),*vals),target)
            ids.append(view)
        raw,iv=add_buffer(doc,raw,struct.pack("<%sI"%count,*range(count)),34963)
        bounds=[[min(pos[i::3]),max(pos[i::3])] for i in range(3)]
        ap=accessor(doc,ids[0],5126,count,"VEC3",
                    ([b[0] for b in bounds],[b[1] for b in bounds]))
        an=accessor(doc,ids[1],5126,count,"VEC3")
        au=accessor(doc,ids[2],5126,count,"VEC2")
        ai=accessor(doc,iv,5125,count,"SCALAR",([0],[count-1]))
        m=len(doc["meshes"]);name=part["name"]
        doc["meshes"].append({"name":name,"primitives":[{
            "attributes":{"POSITION":ap,"NORMAL":an,"TEXCOORD_0":au},
            "indices":ai,"material":mats[part["material"]],"mode":4}]})
        node=len(doc["nodes"]);doc["nodes"].append({"mesh":m,"name":name})
        doc["scenes"][0]["nodes"].append(node)
        names.append(name);count_faces+=len(faces)
    assert count_faces==1296 and triangles(doc)==29144
    assert len(doc["meshes"])==len(doc["nodes"])==141
    assert raw[:len(first_raw)]==first_raw
    for key,record in protected.items():
        assert json.dumps(doc[key][:len(json.loads(record))],sort_keys=True)==record,key
    doc["buffers"][0]["byteLength"]=len(raw)
    product=write_glb(doc,raw)
    assert read_glb(product)[0]["buffers"][0]["byteLength"]==len(raw)
    (candidate/ENVELOPE).write_bytes(product)
    app=(candidate/"app.js").read_text()
    marker="be!==27848||Te!==135"
    assert app.count(marker)==1
    (candidate/"app.js").write_text(app.replace(marker,"be!==29144||Te!==141",1))
    path=candidate/"models/envelope-manifest.json"
    meta=json.loads(path.read_text())
    assert meta["newEnvelopeTriangles"]==27848 and meta["meshObjects"]==135
    meta.update(newEnvelopeTriangles=29144,meshObjects=141)
    meta["stage34OptionalGeometry"]={"names":names,"faces":1296,
      "originalEnvelopeSha256":PIN,"artApproved":False,"newUV1OrGIProven":False}
    path.write_text(json.dumps(meta,indent=2)+"\n")
    proof={"baseEnvelopeSha256":PIN,"candidateEnvelopeSha256":sha(product),
      "original135MeshJSONAndBinaryPreserved":True,"originalMaterialLibraryRetained":True,
      "newMeshes":6,"newTriangles":1296,"newUV1OrGIProven":False,
      "artApproved":False,"productionUnchanged":True}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(proof,indent=2)+"\n")
    print("STAGE34_ENVELOPE_CORRECT_OWNER",json.dumps(proof),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("control","candidate","proof"):p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args();inject(a.control,a.candidate,a.proof)
