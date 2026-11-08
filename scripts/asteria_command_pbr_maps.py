#!/usr/bin/env python3
"""Build deterministic PBR textures for original USS Asteria command-set parts.

Real-world color calibration is not claimed: these are restrained, original
authored textures, NOT photo scans. The instrument panel pixels come from the
frozen original V3 asset atlas. Source/geometry provenance is pinned separately.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

STYLES={
 "powder_ivory":((167,156,151),.72,.16),
 "powder_graphite":((75,70,80),.67,.15),
 "satin_nickel":((146,140,139),.38,.67),
 "rose_bronze":((158,123,99),.43,.56),
 "plum_carpet":((101,95,111),.92,.0),
 "console_gasket":((48,47,57),.87,.0),
}
SIZE=512

def output_image(path,arr):
 Image.fromarray(np.uint8(np.clip(np.round(arr),0,255)),"RGB").save(path,optimize=True)

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--v3-atlas",type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 if not a.v3_atlas.is_file():raise FileNotFoundError(a.v3_atlas)
 rng=np.random.default_rng(63542)
 y,x=np.mgrid[0:SIZE,0:SIZE].astype(np.float32)
 manifests={}
 for style,(tint,rough,metallic) in STYLES.items():
  # Low-amplitude physical surface texture; ensure the viewer responds to
  # normal and roughness variation, rather than relying on flat color only.
  fine=rng.normal(0,1,(SIZE,SIZE)).astype(np.float32)
  low=np.array(Image.fromarray(np.uint8(rng.integers(
    95,161,(64,64),dtype=np.uint8))).resize((SIZE,SIZE),Image.Resampling.BICUBIC),
    dtype=np.float32)
  low=(low-128)/33
  if style=="plum_carpet":
   weave=np.sin(x*3.4)*np.cos(y*2.7)
   h=.12*weave+.05*low+.035*fine
  elif style=="satin_nickel":
   h=.22*np.sin(y*5.9)+.05*np.sin(y*10.1)+.025*fine
  else:
   h=.06*low+.04*fine
  variation=np.clip(1+.020*low+.012*fine,.88,1.12)
  base=np.array(tint,dtype=np.float32)[None,None,:]*variation[:,:,None]
  dx=np.gradient(h,axis=1)
  dy=np.gradient(h,axis=0)
  strength=.08 if style=="satin_nickel" else .11 if style=="plum_carpet" else .045
  norm=np.stack([-dx*strength,-dy*strength,np.ones_like(dx)],axis=2)
  norm/=np.maximum(np.linalg.norm(norm,axis=2,keepdims=True),1.e-9)
  normal=(norm*.5+.5)*255
  r=np.clip(rough+.017*low+.005*fine,.08,.99)
  mr=np.stack([np.full_like(r,255),r*255,np.full_like(r,metallic*255)],axis=2)
  entries={}
  for suffix,arr in (("base",base),("normal",normal),("orm",mr)):
   filename=f"{style}_{suffix}.png"
   target=a.out/filename
   output_image(target,arr)
   entries[suffix]={"filename":filename,"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                    "size":target.stat().st_size}
  manifests[style]={"baseSrgb":tint,"roughness":rough,"metallic":metallic,"maps":entries}
 original=Image.open(a.v3_atlas).convert("RGB")
 assert original.size==(2048,1024),original.size
 panel_hash=hashlib.sha256(a.v3_atlas.read_bytes()).hexdigest()
 for panel,name in ((3,"command_overview"),(5,"systems_control")):
  x0=(panel%4)*512;y0=(panel//4)*256
  tile=original.crop((x0,y0,x0+512,y0+256))
  filename=f"v3_{name}_screen.png"
  tile.save(a.out/filename,optimize=True)
  manifests[name]={"sourceAtlasSha256":panel_hash,
                   "sourceV3Blob":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
                   "sourceTile":panel,"filename":filename,
                   "sha256":hashlib.sha256((a.out/filename).read_bytes()).hexdigest()}
 report={"id":"ASTERIA-COMMAND-PBR-01","seed":63542,"sourceType":"original authored procedural material response",
         "notPhotographicScans":True,"colorCalibration":"artistic, not measured",
         "license":"TrekMUD original work; V3 screen atlas from frozen source",
         "materials":manifests}
 (a.out/"material-provenance.json").write_text(json.dumps(report,indent=2)+"\n")
 print("Generated deterministically authored PBR maps and exact frozen V3 screen tile references")
 print(json.dumps({k:[*v.get("maps",{}).keys()] for k,v in manifests.items()},indent=2))

if __name__=="__main__":main()
