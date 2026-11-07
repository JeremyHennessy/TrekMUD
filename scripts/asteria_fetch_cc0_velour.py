#!/usr/bin/env python3
"""Create a CC0 scanned-fabric material test without touching existing models.

Download only named maps for one Poly Haven texture through its documented
public API, validate checksums and host, then create two palette-corrected
albedo maps. Requires Pillow and NumPy. No assets are requested at runtime
by the eventual browser walkthrough; this is build-time source provenance.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image

ASSET = "velour_velvet"
API = "https://api.polyhaven.com/files/"+ASSET
USER_AGENT = "USS-Asteria-TrekMUD-Asset-Builder/0.1 (+https://github.com/JeremyHennessy/TrekMUD)"
ASSET_PAGE = "https://polyhaven.com/a/"+ASSET
MAX_BYTES = 20_000_000

def request(url):
    parsed=urlsplit(url)
    if parsed.scheme!="https" or parsed.hostname not in {"api.polyhaven.com","dl.polyhaven.org"}:
        raise RuntimeError("Unapproved asset host: "+url)
    req=Request(url,headers={"User-Agent":USER_AGENT,
                              "Referer":"https://github.com/JeremyHennessy/TrekMUD"})
    with urlopen(req,timeout=35) as response:
        length=response.headers.get("Content-Length")
        if length and int(length)>MAX_BYTES:raise RuntimeError("Asset exceeds download cap")
        data=response.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:raise RuntimeError("Asset exceeds byte cap")
    return data

def find_map(tree,names):
    for key,value in tree.items():
        normalized=key.lower().replace("_","").replace(" ","").replace("-","")
        if normalized in names and isinstance(value,dict):
            resolution=value.get("1k",{})
            if not resolution:
                raise RuntimeError("Missing 1K map for "+key)
            for encoding in ("png","jpg","jpeg"):
                item=resolution.get(encoding)
                if isinstance(item,dict) and item.get("url") and item.get("md5"):
                    return key,item,encoding
            raise RuntimeError("No checksum-bearing PNG/JPG at 1K for "+key)
    raise RuntimeError("Poly Haven API missing expected map "+str(names))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    tree=json.loads(request(API))
    if not isinstance(tree,dict):raise TypeError("Unexpected API response")
    maps={
        "diff":find_map(tree,{"diffuse","diff","albedo","basecolor"}),
        "nor_gl":find_map(tree,{"norgl","normalgl","normalopengl"}),
        "rough":find_map(tree,{"rough","roughness"}),
    }
    original={}
    for label,(key,item,extension) in maps.items():
        data=request(item["url"])
        md5=hashlib.md5(data).hexdigest()
        if md5.lower()!=item["md5"].lower():
            raise RuntimeError("Poly Haven checksum mismatch for "+key)
        image=Image.open(io.BytesIO(data))
        if min(image.size)<512:raise RuntimeError("Unexpected small downloaded map "+key)
        image.load()
        path=a.out/(label+"."+extension)
        path.write_bytes(data)
        original[label]={
            "map":key,"file":path.name,"url":item["url"],
            "apiMd5":item["md5"],"sha256":hashlib.sha256(data).hexdigest(),
            "pixels":image.size,"bytes":len(data),
        }
    # Recolor the scanned diffuse *tonal variations* into the original Asteria
    # plum palette while retaining microstructure. This is an art-derived
    # recoloring, not a claim that the original scan is mauve.
    image=Image.open(a.out/original["diff"]["file"]).convert("RGB")
    pixels=np.asarray(image,dtype=np.float32)
    luminance=.2126*pixels[:,:,0]+.7152*pixels[:,:,1]+.0722*pixels[:,:,2]
    median=max(1.,float(np.median(luminance)))
    shade=np.clip(.92+.32*((luminance-median)/max(30.,median)),.72,1.18)
    for filename,color in [
        ("asteria_mauve_diffuse.png",(103,78,96)),
        ("asteria_mauve_light_diffuse.png",(131,103,117)),
    ]:
        recolored=np.uint8(np.clip(shade[:,:,None]*np.array(color,dtype=np.float32),0,255))
        Image.fromarray(recolored,"RGB").save(a.out/filename,optimize=True)
    report={
        "assetId":ASSET,
        "origin":ASSET_PAGE,
        "license":"CC0-1.0",
        "licenseSource":"https://polyhaven.com/license",
        "sourceMapResolution":"1k",
        "maps":original,
        "derived":["asteria_mauve_diffuse.png","asteria_mauve_light_diffuse.png"],
        "sourceAuthority":"Poly Haven Public API; checksum verified at acquisition",
        "limitations":"Source checksums are captured for this test, not yet pinned in code. No distribution to public browser claimed.",
    }
    (a.out/"fabric-provenance.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
