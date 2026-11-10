#!/usr/bin/env python3
"""Exact original 6476-face opaque flightIsland exclusion on Stage33 opt-in V3.
No changes to frozen source, original six atlas touchglass planes, or pilot chairs.
Checks full per-material original source vertex ordering before removing faces.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
from asteria_stage33_v3_filter import parse_glb
SPAN=(37104,43580)
def run(site,capture,proof,out):
    audit=json.loads(proof.read_text())
    assert (audit["start"],audit["end"])==SPAN and audit["originalOpaqueDeskFaces"]==6476
    assert audit["sourceV3Blob"]=="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
    assert audit["sourceHeroBlob"]=="95ac0fc2d480736ddf2f38f596d1115a4193f926"
    assert audit["sourceSetDetailsBlob"]=="3716accf4490bf28da56be0ae21081ab3a3a0f17"
    assert audit["originalSixFunctionalFlightGlassPlanesRetained"]
    manifest=json.loads((site/"models/manifest.json").read_text())
    assert manifest["triangles"]==80750 and manifest["under_console_original_faces_removed"]==96
    raw=(site/"models/asteria-v3-restored-pbr.glb").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==manifest["sha256"]
    doc,bin=parse_glb(raw)
    source=np.load(capture/"positions.npy").reshape(-1,3,3)
    mats=np.load(capture/"materials.npy").reshape(-1,3)
    assert len(source)==len(mats)==106988 and np.all(mats==mats[:,0,None])
    # Frozen build_asteria_v5_assets.py reclassifies the two source-material-7
    # starfield triangles as unlit GLB material 9 after source capture. Preserve
    # those six original vertices, the source arrays and all functional screens.
    # Match the exact pinned V5 builder's geometric predicate, fail closed.
    source_pos=source.reshape(-1,3)
    source_mats=mats.reshape(-1)
    star=(source_mats==7)&(np.abs(source_pos[:,2]+6.06)<.0005)&(
        np.abs(source_pos[:,0])<=3.101)
    assert int(star.sum())==6, "Pinned V5 starfield material provenance drift"
    assert np.all(star.reshape(-1,3)==star.reshape(-1,3)[:,0,None])
    mats=mats.copy()
    mats.reshape(-1)[star]=9
    assert int((mats[:,0]==9).sum())==2, "Unlit starfield must be exactly two triangles"
    keep=np.ones(106988,dtype=bool)
    exclusions=[(14404,30676)]
    for key in ("command_source_ranges","three_rib_bays_source_ranges",
                "envelope_source_ranges","forward_portal_source_ranges",
                "under_console_source_ranges"):
        exclusions.extend((x["start"],x["end"]) for x in manifest[key])
    for a,b in exclusions:
        assert keep[a:b].all(),("Previously excluded spans overlap",a,b)
        keep[a:b]=False
    assert int(keep.sum())==80750
    assert keep[SPAN[0]:SPAN[1]].all(),("Flight source overlaps removed area")
    removed=0;updates={}
    for i,mesh in enumerate(doc["meshes"]):
        prim=mesh["primitives"][0]
        assert prim["material"]==i and prim["mode"]==4 and "indices" not in prim
        attrs=prim["attributes"]
        assert set(attrs)=={"POSITION","NORMAL","COLOR_0","TEXCOORD_0"}
        ids=np.flatnonzero(keep & (mats[:,0]==i))
        removed_idx=(ids>=SPAN[0])&(ids<SPAN[1])
        num=int(removed_idx.sum());removed+=num
        vk=np.repeat(~removed_idx,3)
        for attr,ai in attrs.items():
            ac=doc["accessors"][ai];view=doc["bufferViews"][ac["bufferView"]]
            dtype={5126:"<f4",5121:"u1"}[ac["componentType"]]
            dim={"VEC3":3,"VEC2":2}[ac["type"]]
            chunk=bin[view.get("byteOffset",0):view.get("byteOffset",0)+view["byteLength"]]
            arr=np.frombuffer(chunk,dtype=dtype).reshape(-1,dim)
            assert len(arr)==ac["count"]==len(ids)*3
            if attr=="POSITION":
                assert np.allclose(arr.reshape(-1,3,3),source[ids],atol=1e-6,rtol=0),(
                    "GLB original position order differs from pinned V3 source",i)
            if num:
                out_arr=arr[vk]
                assert len(out_arr)==(len(ids)-num)*3
                ac["count"]=len(out_arr)
                if attr=="POSITION":
                    ac["min"]=out_arr.min(axis=0).astype(float).tolist()
                    ac["max"]=out_arr.max(axis=0).astype(float).tolist()
                updates[ac["bufferView"]]=out_arr.tobytes()
    assert removed==6476
    buffer=bytearray()
    for i,view in enumerate(doc["bufferViews"]):
        previous=bin[view.get("byteOffset",0):view.get("byteOffset",0)+view["byteLength"]]
        nxt=updates.get(i,previous)
        buffer.extend(b"\0"*((-len(buffer))%4))
        view["byteOffset"]=len(buffer)
        view["byteLength"]=len(nxt)
        buffer.extend(nxt)
    buffer.extend(b"\0"*((-len(buffer))%4))
    doc["buffers"][0]["byteLength"]=len(buffer)
    doc["extras"]["stage35OpaqueFlightIslandFacesRemoved"]=6476
    doc["extras"]["remainingV3Triangles"]=74274
    js=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
    js+=b" "*((-len(js))%4)
    final=(struct.pack("<4sII",b"glTF",2,28+len(js)+len(buffer))
         +struct.pack("<I4s",len(js),b"JSON")+js
         +struct.pack("<I4s",len(buffer),b"BIN\x00")+buffer)
    assert parse_glb(final)[0]["extras"]["remainingV3Triangles"]==74274
    f=out/"models/asteria-v3-restored-pbr.glb"
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_bytes(final)
    manifest.update(sha256=hashlib.sha256(final).hexdigest(),bytes=len(final),
        triangles=74274,stage35_forward_original_faces_removed=6476,
        stage35_forward_original_source_span=list(SPAN))
    (f.parent/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    app=(site/"app.js").read_text()
    guard="Se!==106988-Be-ft-174-864-204-96"
    assert app.count(guard)==1
    (out/"app.js").write_text(app.replace(guard,guard+"-6476",1))
    return dict(originalV3Blob=audit["sourceV3Blob"],originalHeroBlob=audit["sourceHeroBlob"],
        originalModelSHA256=hashlib.sha256(raw).hexdigest(),
        candidateModelSHA256=manifest["sha256"],
        exactSourceExcludedFaces=6476,excludedSpan=list(SPAN),
        functionalTouchglassPreserved=True,allOtherOriginalV3FacesPreserved=True,
        experimentalOnly=True,artApproved=False)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("site","capture","proof","out","receipt"):
        p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();record=run(a.site,a.capture,a.proof,a.out)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(record,indent=2)+"\n")
    print("STAGE35_EXACT_OPAQUE_FLIGHT_SOURCE_EXCLUSION",json.dumps(record),flush=True)
