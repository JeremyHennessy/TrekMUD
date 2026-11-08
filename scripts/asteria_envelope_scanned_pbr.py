#!/usr/bin/env python3
"""Build original Asteria wall/ceiling composite from real CC0 scanned microtexture.

One Poly Haven painted-plaster photographic scan supplies diffuse variation,
roughness and true photo-derived normal detail. Colours are deliberately
recalibrated to original 2372-era Asteria cream composite, NOT claimed to
represent the actual photographed wall. Geometry remains TrekMUD original.
Downloads occur only on controlled CI build, never in the visitor browser.
"""
from __future__ import annotations
import argparse,hashlib,io,json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
import numpy as np
from PIL import Image

ASSET="painted_plaster_wall"
ASSET_PAGE="https://polyhaven.com/a/"+ASSET
API="https://api.polyhaven.com/files/"+ASSET
UA="USS-Asteria-TrekMUD-Architectural-Texture/0.1 (+https://github.com/JeremyHennessy/TrekMUD)"
ALLOWED={"api.polyhaven.com","dl.polyhaven.org"}
CAP=24_000_000
SIZE=1024

def fetch(url):
    parts=urlsplit(url)
    if parts.scheme!="https" or parts.hostname not in ALLOWED:
        raise ValueError("Refusing unapproved texture download host: "+url)
    req=Request(url,headers={"User-Agent":UA,"Referer":"https://github.com/JeremyHennessy/TrekMUD"})
    with urlopen(req,timeout=50) as resp:
        length=resp.headers.get("Content-Length")
        if length and int(length)>CAP:raise ValueError("Source texture exceeds byte cap")
        raw=resp.read(CAP+1)
    if len(raw)>CAP:raise ValueError("Source texture exceeds byte cap")
    return raw

def choose(tree,names):
    for key,item in tree.items():
        norm=key.lower().replace(" ","").replace("_","").replace("-","")
        if norm not in names or not isinstance(item,dict):continue
        resolutions=item.get("1k")
        if not isinstance(resolutions,dict):raise KeyError("Missing 1K map "+key)
        for ext in ("png","jpg","jpeg"):
            entry=resolutions.get(ext)
            if isinstance(entry,dict) and entry.get("url") and entry.get("md5"):
                return key,entry
    raise KeyError("No valid checksum-bearing Poly Haven map: "+str(names))

def load_verified(label,item,out):
    name,meta=item
    raw=fetch(meta["url"])
    md5=hashlib.md5(raw).hexdigest()
    if md5.lower()!=str(meta["md5"]).lower():
        raise ValueError("Poly Haven checksum changed for "+name)
    image=Image.open(io.BytesIO(raw)).convert("RGB")
    if min(image.size)<SIZE:raise ValueError("Source map too small")
    image=image.resize((SIZE,SIZE),Image.Resampling.LANCZOS)
    path=out/f"scan_{label}.png"
    image.save(path,optimize=True)
    return image,{"apiMap":name,"originUrl":meta["url"],"apiMd5":md5,
                  "rawSha256":hashlib.sha256(raw).hexdigest(),
                  "derivedFile":path.name,"derivedSha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                  "resolution":list(image.size),"rawBytes":len(raw)}

def save(path,arr):
    Image.fromarray(np.uint8(np.clip(np.rint(arr),0,255)),"RGB").save(path,optimize=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    tree=json.loads(fetch(API))
    assert isinstance(tree,dict)
    scans={}
    refs={}
    for name,choices in (
        ("diff",{"diff","diffuse","albedo","basecolor"}),
        ("normal",{"norgl","normalgl","normalopengl"}),
        ("rough",{"rough","roughness"})):
        image,refs[name]=load_verified(name,choose(tree,choices),a.out)
        scans[name]=np.asarray(image,dtype=np.float32)
    luminance=np.dot(scans["diff"],np.array([.2126,.7152,.0722],dtype=np.float32))
    median=max(1.,float(np.median(luminance)))
    # Respect photographed grain but avoid copying weathered outdoor stains
    # into a supposedly maintained starship interior. The normal and rough
    # scans preserve authentic microstructure, muted with material strength.
    scan_relative=np.clip((luminance-median)/max(45.,median),-.20,.20)
    height=np.clip(.5+(luminance-median)/255,.28,.72)
    normals=scans["normal"].copy()
    # Moderate strong plaster height relief so the ship's painted composite
    # appears manufactured rather than crumbling.
    xy=(normals[:,:,:2]/255-.5)*.32
    normals[:,:,:2]=np.clip((xy+.5)*255,0,255)
    normalz=np.sqrt(np.maximum(0.001,1-((normals[:,:,0]/127.5-1)**2
                                      +(normals[:,:,1]/127.5-1)**2)))
    normals[:,:,2]=normalz*127.5+127.5
    scans_rough=scans["rough"].mean(axis=2)/255
    settings={
      "wall": {"tint":(211,201,187),"rough":.67,"metal":.025,"grain":.16},
      "ceiling":{"tint":(211,201,190),"rough":.80,"metal":0.0,"grain":.11},
    }
    products={}
    for name,preset in settings.items():
        tint=np.asarray(preset["tint"],dtype=np.float32)[None,None,:]
        variation=np.clip(1+scan_relative*preset["grain"],.93,1.07)
        albedo=tint*variation[:,:,None]
        rough=np.clip(preset["rough"]+.16*(scans_rough-.55),.36,.97)
        orm=np.stack([np.full_like(rough,255),
                      rough*255,
                      np.full_like(rough,preset["metal"]*255)],axis=2)
        maps={}
        for suffix,array in (("base",albedo),("normal",normals),("orm",orm)):
            path=a.out/f"architectural_{name}_{suffix}.png"
            save(path,array)
            maps[suffix]={"file":path.name,
                          "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                          "bytes":path.stat().st_size}
        products[name]={"baseTint":preset["tint"],"roughness":preset["rough"],
                        "metallic":preset["metal"],"scanDetailMuted":True,
                        "textures":maps}
    report={
        "id":"ASTERIA_ENVELOPE_SCANNED_PBR_08",
        "originalV3Source":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
        "scanProvider":"Poly Haven","scanAsset":ASSET,
        "scanPage":ASSET_PAGE,
        "license":"CC0", "licenseSource":"https://polyhaven.com/license",
        "mapsProvenance":refs,"derived":products,
        "photoBasedNormalAndRoughness":True,
        "recoloredFromPhotographicBase":True,
        "indoorWearAndDirtMuted":True,
        "doesNotProveOriginalStarshipSurfaceMeasurements":True,
        "notCalibratedRealWorldColour":True,
        "downloadOnlyAtAuthoringBuildTime":True,
    }
    (a.out/"envelope-material-provenance.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ENVELOPE_VERIFIED_CC0_PHOTOGRAPHIC_PBR",json.dumps({
      "source":ASSET_PAGE,"maps":{k:v["rawSha256"] for k,v in refs.items()},
      "derived":{k:list(v["textures"]) for k,v in products.items()}
    }))
if __name__=="__main__":
    main()
