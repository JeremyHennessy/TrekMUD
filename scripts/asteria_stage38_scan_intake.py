#!/usr/bin/env python3
"""Stage38 read-only real CC0 2K upholstered-asset intake (not a bridge visual pass)."""
from __future__ import annotations
import argparse, hashlib, json, urllib.request
from pathlib import Path
from urllib.parse import urlparse
ASSET="modern_arm_chair_01"
UA="USS-Asteria-3D-AssetProvenance/1.0 (TrekMUD isolated research)"
LIMIT=85_000_000
def get(url, max_bytes=LIMIT):
    p=urlparse(url)
    assert p.scheme=="https" and p.hostname in ("api.polyhaven.com","dl.polyhaven.org"),url
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=45) as f:
        data=f.read(max_bytes+1)
        assert len(data)<=max_bytes and not f.read(1),"oversize asset"
        return data
def safe_path(root,name):
    assert isinstance(name,str) and 0<len(name)<220
    assert "\\" not in name and not name.startswith("/")
    assert all(x not in ("",".","..") for x in name.split("/"))
    dst=root/name
    assert dst.resolve().is_relative_to(root.resolve())
    return dst
def download(root,name,meta):
    assert set(("url","size","md5")).issubset(meta)
    size=int(meta["size"])
    assert 0<size<LIMIT
    data=get(meta["url"],size)
    assert len(data)==size,(name,"bad size")
    digest=hashlib.md5(data).hexdigest()
    assert digest.lower()==meta["md5"].lower(),(name,"bad md5")
    dst=safe_path(root,name)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_bytes(data)
    return dict(path=name,bytes=size,md5=digest,sha256=hashlib.sha256(data).hexdigest(),url=meta["url"])
def gltf_proof(root,main):
    j=json.loads(safe_path(root,main).read_text())
    assert j["asset"]["version"]=="2.0"
    assert j.get("meshes") and j.get("accessors") and j.get("materials")
    assert j.get("textures") and j.get("images")
    faces=0
    for m in j["meshes"]:
        for p in m["primitives"]:
            assert all(k in p["attributes"] for k in ("POSITION","NORMAL","TEXCOORD_0"))
            assert p.get("mode",4)==4 and isinstance(p.get("indices"),int)
            count=j["accessors"][p["indices"]]["count"]
            assert count>0 and count%3==0
            faces+=count//3
    assert 1000<faces<60000
    roles={"baseColor":0,"normal":0,"roughMetallic":0}
    for m in j["materials"]:
        pbr=m.get("pbrMetallicRoughness",{})
        roles["baseColor"]+=bool(pbr.get("baseColorTexture"))
        roles["normal"]+=bool(m.get("normalTexture"))
        roles["roughMetallic"]+=bool(pbr.get("metallicRoughnessTexture"))
    assert all(roles.values()),roles
    for a in j.get("images",[])+j.get("buffers",[]):
        if "uri" in a:
            uri=a["uri"]
            assert not uri.startswith("data:") and "%" not in uri
            assert safe_path(root,uri).is_file(),("missing dependency",uri)
    return dict(triangles=faces,meshes=len(j["meshes"]),materials=[m.get("name") for m in j["materials"]],pbrTextureRoles=roles,images=len(j["images"]),normalAndUV0PerPrimitive=True)
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    root=a.parse_args().out.resolve()
    root.mkdir(parents=True,exist_ok=True)
    files=json.loads(get("https://api.polyhaven.com/files/"+ASSET))
    info=json.loads(get("https://api.polyhaven.com/info/"+ASSET))
    asset=files["gltf"]["2k"]["gltf"]
    deps=asset.get("include")
    assert isinstance(deps,dict) and 1<=len(deps)<48
    filenames=[(ASSET+"_2k.gltf",asset)]+sorted(deps.items())
    manifest=[download(root,n,v) for n,v in filenames]
    total=sum(x["bytes"] for x in manifest)
    assert total<LIMIT
    proof=gltf_proof(root,filenames[0][0])
    receipt=dict(id="STAGE38_POLYHAVEN_SCAN_INTAKE_ONLY",asset="https://polyhaven.com/a/"+ASSET,
        creator="Vibrant Nordic (verify on official asset listing)",catalog=info.get("name"),
        license="CC0 1.0 https://polyhaven.com/license",
        liveAPIUseRequiresPolyHavenCredit=True,sourceFiles=manifest,gltf=proof,totalBytes=total,
        originalSourceMask32_600VerifiedOnEarlierRun=True,chairPlacedInBridge=False,
        desktopMobileArtVerified=False,originalV3OrMainChanged=False,
        newUV1ContactAOProven=False,approved=False,deployed=False)
    (root/"stage38-provenance.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE38_SCAN_SOURCE_OK",json.dumps(dict(triangles=proof["triangles"],bytes=total,
        files=len(manifest),approved=False,deployed=False)),flush=True)
if __name__=="__main__":
    main()
