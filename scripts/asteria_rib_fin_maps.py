#!/usr/bin/env python3
"""Deterministic, original microstructure PBR for one Asteria acoustic-fin bay.

The colours are source-matched to adjacent frozen V3 decorations, not claimed
photogrammetry. Material repeat corresponds to real 10-12 cm physical UV tiles.
This writes a separate optional asset directory, never overwriting the command
platform or live Pages material maps.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
S=512
FIN_STYLES={
    "acoustic_linen": {"tint":(209,196,183),"roughness":.89,"metal":0., "kind":"weave"},
    "formed_pearl": {"tint":(197,185,176),"roughness":.69,"metal":.09,"kind":"powder"},
}
def export(path,arr):
    Image.fromarray(np.uint8(np.clip(np.rint(arr),0,255)),"RGB").save(path,optimize=True)

def build(out):
    out.mkdir(parents=True,exist_ok=True)
    result={}
    rng=np.random.default_rng(63542)
    yy,xx=np.mgrid[0:S,0:S].astype(np.float32)
    for name,p in FIN_STYLES.items():
        # Sub-millimetre manufacturing texture at the tile scale; avoids
        # prior oversized, repetitive procedural marble/"plastic door" look.
        fine=rng.normal(0,1,(S,S)).astype(np.float32)
        low=np.asarray(Image.fromarray(np.uint8(
            rng.integers(118,139,(64,64),dtype=np.uint8))).resize((S,S),
                      Image.Resampling.BICUBIC),dtype=np.float32)-128.
        if p["kind"]=="weave":
            # Simulate separated warp/weft relief at ~1 mm thread scale.
            warp=np.sin(xx*2*np.pi/4.3)
            weft=np.sin(yy*2*np.pi/5.2)
            height=.27*warp+.22*weft+.035*fine
            delta=.028*warp+.023*weft+.012*low+.65*fine
        else:
            height=.043*low+.048*fine
            delta=.018*low+.75*fine
        base=np.asarray(p["tint"],dtype=np.float32)[None,None,:]*(1+delta[:,:,None]*.012)
        gx=np.gradient(height,axis=1)
        gy=np.gradient(height,axis=0)
        strength=.075 if p["kind"]=="weave" else .045
        normal=np.stack([-gx*strength,-gy*strength,np.ones((S,S),np.float32)],axis=2)
        normal/=np.maximum(1.e-6,np.linalg.norm(normal,axis=2,keepdims=True))
        normal=(normal*.5+.5)*255
        rough=np.clip(p["roughness"]+.009*low+.008*fine,.13,.98)
        orm=np.stack([np.full((S,S),255,np.float32),rough*255,
                      np.full((S,S),p["metal"]*255,np.float32)],axis=2)
        files={}
        for kind,img in (("base",base),("normal",normal),("orm",orm)):
            path=out/f"{name}_{kind}.png"
            export(path,img)
            files[kind]={"file":path.name,
                         "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                         "bytes":path.stat().st_size}
        result[name]={"tintRgb":list(p["tint"]),"roughness":p["roughness"],
                      "metal":p["metal"],"microstructure":p["kind"],
                      "tileRealUnitsMetres":[.10,.12],"files":files}
    report={"id":"ASTERIA_RIB_FIN_MATERIALS_03","originalAuthoring":True,
            "scanClaims":False,"licensedOriginal":True,
            "adjacentOriginalV3":{"linen":"#d1c4b7","satin":"#b4a9a9"},
            "sourceV3Blob":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
            "styles":result}
    (out/"material-provenance.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ORIGINAL_RIB_FIN_PBR",json.dumps(report))
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    p=a.parse_args()
    build(p.out)
