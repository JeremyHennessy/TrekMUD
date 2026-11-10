#!/usr/bin/env python3
"""Opt-in Stage38 CC0 real-scan twin pilot art candidate; NO production changes."""
from __future__ import annotations
import argparse,copy,hashlib,json,struct
from pathlib import Path
MODEL="models/asteria-realistic-architectural-envelope-08.glb"
PIN="b43096fed31334511f6d78b0b3b254863ec90349d7490059e44d957c9f2e688c"
APP_PIN="3a85cd7f60bb7523ff2f52d414de9be6e9c4b671a6b1a1c14e8ea73ee03c3baa"
NAME="modern_arm_chair_01_2k.gltf"
def sha(data):return hashlib.sha256(data).hexdigest()
def pad(data):return data+b"\0"*(-len(data)%4)
def parse(data):
    assert struct.unpack_from("<4sII",data,0)==(b"glTF",2,len(data))
    n,t=struct.unpack_from("<I4s",data,12);assert t==b"JSON"
    doc=json.loads(data[20:20+n]);i=20+n
    m,t=struct.unpack_from("<I4s",data,i)
    assert t==b"BIN\x00" and i+8+m==len(data)
    raw=data[i+8:]
    assert len(raw)==doc["buffers"][0]["byteLength"]
    return doc,raw
def encode(doc,binary):
    binary=pad(binary)
    doc["buffers"][0]["byteLength"]=len(binary)
    b=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
    b+=b" "*(-len(b)%4)
    return struct.pack("<4sII",b"glTF",2,28+len(b)+len(binary))+struct.pack("<I4s",len(b),b"JSON")+b+struct.pack("<I4s",len(binary),b"BIN\x00")+binary
def sourcefile(root,name):
    assert name and "\\" not in name and not name.startswith("/")
    assert all(x not in ("",".","..") for x in name.split("/"))
    path=(root/name).resolve()
    assert path.is_relative_to(root.resolve())
    return path
def run(control,candidate,asset,receipt):
    old=(control/MODEL).read_bytes()
    assert sha(old)==PIN
    assert sha((control/"app.js").read_bytes())==APP_PIN
    receipt_original=json.loads((asset/"stage38-provenance.json").read_text())
    assert receipt_original["id"]=="STAGE38_POLYHAVEN_SCAN_INTAKE_ONLY"
    assert receipt_original["gltf"]["triangles"]==8916
    for f in receipt_original["sourceFiles"]:
        data=sourcefile(asset,f["path"]).read_bytes()
        assert len(data)==f["bytes"] and sha(data)==f["sha256"]
        assert hashlib.md5(data).hexdigest()==f["md5"]
    src=json.loads(sourcefile(asset,NAME).read_text())
    assert src["asset"]["version"]=="2.0"
    assert len(src["buffers"])==len(src["meshes"])==len(src["nodes"])==1
    assert src["nodes"][0]["mesh"]==0 and src["scenes"][src.get("scene",0)]["nodes"]==[0]
    assert not src.get("extensionsRequired") and not src.get("skins") and not src.get("animations")
    doc,binary=parse(old)
    assert len(doc["meshes"])==len(doc["nodes"])==135 and len(doc["scenes"][0]["nodes"])==135
    assert len(doc["buffers"])==len(doc["scenes"])==1
    keys=("meshes","nodes","materials","images","textures","samplers","bufferViews","accessors")
    saved={k:json.dumps(doc[k],sort_keys=True) for k in keys}
    offsets={k:len(doc[k]) for k in keys}
    old_binary=binary
    source_binary=sourcefile(asset,src["buffers"][0]["uri"]).read_bytes()
    assert len(source_binary)==src["buffers"][0]["byteLength"]
    binary=pad(binary);offset=len(binary);binary+=pad(source_binary)
    for v in src["bufferViews"]:
        item=copy.deepcopy(v)
        assert item["buffer"]==0
        item["byteOffset"]=offset+item.get("byteOffset",0)
        doc["bufferViews"].append(item)
    for v in src["accessors"]:
        item=copy.deepcopy(v)
        assert not item.get("sparse")
        item["bufferView"]+=offsets["bufferViews"]
        doc["accessors"].append(item)
    for v in src["images"]:
        item=copy.deepcopy(v)
        img=sourcefile(asset,item.pop("uri")).read_bytes()
        assert img[:3]==b"\xff\xd8\xff"
        binary=pad(binary);at=len(binary);binary+=pad(img)
        doc["bufferViews"].append({"buffer":0,"byteOffset":at,"byteLength":len(img)})
        item["bufferView"]=len(doc["bufferViews"])-1
        item["mimeType"]="image/jpeg"
        doc["images"].append(item)
    for v in src["samplers"]:doc["samplers"].append(copy.deepcopy(v))
    for v in src["textures"]:
        item=copy.deepcopy(v)
        assert not item.get("extensions")
        item["source"]+=offsets["images"]
        if "sampler" in item:item["sampler"]+=offsets["samplers"]
        doc["textures"].append(item)
    for v in src["materials"]:
        item=copy.deepcopy(v)
        assert not item.get("extensions")
        item["name"]="STAGE38 CC0 scanned / "+item["name"]
        pbr=item.get("pbrMetallicRoughness",{})
        for field in ("baseColorTexture","metallicRoughnessTexture"):
            if field in pbr:pbr[field]["index"]+=offsets["textures"]
        for field in ("normalTexture","occlusionTexture","emissiveTexture"):
            if field in item:item[field]["index"]+=offsets["textures"]
        doc["materials"].append(item)
    for v in src["meshes"]:
        item=copy.deepcopy(v)
        for p in item["primitives"]:
            assert p.get("mode",4)==4 and not p.get("targets")
            assert all(x in p["attributes"] for x in ("POSITION","NORMAL","TEXCOORD_0"))
            p["indices"]+=offsets["accessors"]
            p["material"]+=offsets["materials"]
            p["attributes"]={k:i+offsets["accessors"] for k,i in p["attributes"].items()}
        item["name"]="STAGE38 original professionally modeled / "+item.get("name","")
        doc["meshes"].append(item)
    # Native scan back is -Z. Flip 180 about vertical to face forward -Z.
    # Runtime sees a node hierarchy with TWO PBR primitive meshes per chair.
    triangles=2*sum(src["accessors"][p["indices"]]["count"]//3 for p in src["meshes"][0]["primitives"])
    mesh_count=2*len(src["meshes"][0]["primitives"])
    assert triangles==17832 and mesh_count==4
    for side in (-1,1):
        index=len(doc["nodes"])
        doc["nodes"].append({"name":f"STAGE38 real CC0 pilot chair {side:+d}",
            "mesh":offsets["meshes"],"translation":[side*1.15,0,-2.13],
            "rotation":[0,1,0,0],"scale":[1.42,1.42,1.42]})
        doc["scenes"][0]["nodes"].append(index)
    for key in keys:
        before=json.loads(saved[key])
        assert json.dumps(doc[key][:len(before)],sort_keys=True)==saved[key],("original GLB mutated",key)
    assert binary[:len(old_binary)]==old_binary
    result=encode(doc,binary)
    assert parse(result)[0]["buffers"][0]["byteLength"]==len(pad(binary))
    (candidate/MODEL).write_bytes(result)
    app_path=candidate/"app.js"
    app=app_path.read_text()
    guard="be!==27848||Te!==135"
    assert app.count(guard)==1
    app_path.write_text(app.replace(guard,f"be!=={27848+triangles}||Te!=={135+mesh_count}",1))
    manifest_path=candidate/"models/envelope-manifest.json"
    manifest=json.loads(manifest_path.read_text())
    assert manifest["newEnvelopeTriangles"]==27848 and manifest["meshObjects"]==135
    manifest["newEnvelopeTriangles"]=27848+triangles
    manifest["meshObjects"]=135+mesh_count
    manifest["stage38ScanPilotTrial"]={"newTriangles":triangles,
        "newMeshInstances":mesh_count,"originalEnvelopeSha256":PIN,
        "candidateEnvelopeSha256":sha(result),"licensedScannedFabricProven":True,
        "newUV1OrGIProven":False,"artApproved":False,"releaseApproved":False}
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    evidence={"id":"STAGE38_SCANNED_CC0_PILOT_A_B", "source":"https://polyhaven.com/a/modern_arm_chair_01",
        "sourceTrianglesEach":8916,"newTriangles":triangles,"newMeshInstances":mesh_count,
        "old135MeshesAndBinaryPreserved":True,"sourceV3PilotMaskExpected":32600,
        "newAOorUV1Proven":False,"fullQualityGate":False,
        "artApproved":False,"deployed":False}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(evidence,indent=2)+"\n")
    print("STAGE38_REAL_SCANNED_TWIN_CC0_ART_CANDIDATE",json.dumps(evidence),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("control","candidate","asset","proof"):
        p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args()
    run(a.control,a.candidate,a.asset,a.proof)
