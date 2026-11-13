#!/usr/bin/env python3
"""CC0 photographed painted-metal detail intake, not accepted Asteria scene art.

Source: Poly Haven painted_metal_shutter (photography, CC0).
This is weathered corrugated metal, NOT clean interior powder coating.
Only high-frequency microdetail is preserved and recolored; source limitations
and each raw-map checksum are recorded. No deployed scene files are touched.
"""
from __future__ import annotations
import argparse, hashlib, io, json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

ASSET = "painted_metal_shutter"
API = "https://api.polyhaven.com/files/" + ASSET
SOURCE = "https://polyhaven.com/a/" + ASSET
LICENCE = "https://polyhaven.com/license"
HOSTS = {"api.polyhaven.com", "dl.polyhaven.org"}
LIMIT = 20_000_000
N = 1024

def download(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in HOSTS:
        raise ValueError("Unapproved source host: " + url)
    with urlopen(Request(url, headers={"User-Agent": "Asteria-photo-metal-source-check/1.0"}), timeout=45) as r:
        if int(r.headers.get("Content-Length", "0") or 0) > LIMIT:
            raise ValueError("Source content too large")
        raw = r.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("Source exceeds byte cap")
    return raw

def choose_map(tree, candidates):
    for key, val in tree.items():
        norm = key.lower().replace("_", "").replace("-", "").replace(" ", "")
        if norm not in candidates or not isinstance(val, dict):
            continue
        for ext in ("jpg", "png", "jpeg"):
            obj = val.get("1k", {}).get(ext, {})
            if isinstance(obj, dict) and obj.get("url") and obj.get("md5"):
                return key, ext, obj
    raise ValueError("Missing checksum-bearing 1K source map " + str(candidates))

def load_map(tree, choices, name, out):
    key, ext, obj = choose_map(tree, choices)
    raw = download(obj["url"])
    md5 = hashlib.md5(raw).hexdigest()
    if md5.lower() != str(obj["md5"]).lower():
        raise ValueError("Source/API MD5 mismatch for " + key)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    if min(image.size) < N:
        raise ValueError("Source map unexpectedly small")
    image = image.resize((N, N), Image.Resampling.LANCZOS)
    original = out / ("original_" + name + "." + ext)
    original.write_bytes(raw)
    return np.asarray(image, dtype=np.float32), {
        "map": key, "sourceUrl": obj["url"], "sourceMd5": md5,
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "originalFilename": original.name, "sourceBytes": len(raw)
    }

def blur(arr, radius=28):
    return np.asarray(Image.fromarray(np.uint8(np.clip(arr, 0, 255)), "RGB").filter(
        ImageFilter.GaussianBlur(radius)), dtype=np.float32)

def write_png(path, array):
    Image.fromarray(np.uint8(np.clip(np.rint(array), 0, 255)), "RGB").save(path, optimize=True)
    return {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}

def make_maps(scans, out):
    diffuse, normals, roughness = (scans[k] for k in ("diff", "nor", "rough"))
    weights = np.array([.2126, .7152, .0722], dtype=np.float32)
    hp = np.clip(diffuse @ weights - blur(diffuse) @ weights, -26, 26) / 26
    # Real shutter photography has strong horizontal ribs. Strip the row-wise
    # manufactured ridge profile while retaining photographed pixel micrograin.
    hp = np.clip(hp - np.median(hp, axis=1, keepdims=True), -1, 1)
    rough_hp = np.clip((roughness.mean(axis=2) - blur(roughness).mean(axis=2)) / 255, -.15, .15)
    rough_hp = np.clip(rough_hp - np.median(rough_hp, axis=1, keepdims=True), -.15, .15)
    normal_xy = np.clip((normals[:,:,:2] - blur(normals)[:,:,:2]) / 127.5 * .17, -.16, .16)
    normal_xy = np.clip(normal_xy - np.median(normal_xy, axis=1, keepdims=True), -.16, .16)
    normal_z = np.sqrt(np.maximum(.0001, 1 - np.sum(normal_xy**2, axis=2)))
    new_norm = (np.dstack((normal_xy, normal_z)) * .5 + .5) * 255
    outmaps = {}
    for label, color, target_rough, metal in [
        ("ivory_coat", (173, 163, 153), .64, 0.0),
        ("graphite_coat", (57, 56, 65), .59, 0.0),
        ("satin_insert", (137, 137, 143), .37, .82)]:
        base = np.asarray(color, dtype=np.float32)[None,None,:] * (1 + (.022 * hp)[:,:,None])
        rough = np.clip(target_rough + rough_hp*.45, .18, .95)
        orm = np.dstack((np.full((N,N),255,dtype=np.float32), rough*255,
                         np.full((N,N),255*metal,dtype=np.float32)))
        outmaps[label] = {k:write_png(out / (label+"_"+k+".png"), v)
                          for k,v in (("base",base),("normal",new_norm),("orm",orm))}
        outmaps[label]["design"] = {"sRGB": color, "roughness": target_rough, "metallic":metal,
                                   "photoMicrodetailHighpassOnly": True, "shutterRowBandRemoved": True,
                                   "notPristineMetalPhotograph": True}
    thumb = Image.new("RGB", (930, 330), (26,25,32))
    d = ImageDraw.Draw(thumb)
    for i,label in enumerate(outmaps):
        tile = Image.open(out / (label+"_base.png")).resize((290,290))
        thumb.paste(tile, (10+i*310,10))
        d.text((14+i*310,305), label, fill=(235,226,220))
    thumb.save(out / "palette_swatches_not_render.png")
    return outmaps, {"lumaHighpassAbsMean":float(np.abs(hp).mean()),
        "roughHighpassStd":float(rough_hp.std()), "photoNormalXYStd":float(normal_xy.std())}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    tree=json.loads(download(API))
    if not isinstance(tree,dict):
        raise ValueError("Unexpected Poly Haven metadata")
    maps, sources = {}, {}
    for name, choices in [("diff",{"diff","diffuse","albedo","basecolor"}),
                          ("nor",{"norgl","normalgl","normalopengl"}),
                          ("rough",{"rough","roughness"})]:
        maps[name],sources[name] = load_map(tree, choices, name, a.out)
    outputs,stats=make_maps(maps,a.out)
    report = {"status":"ART_HOLD_NOT_AN_ACCEPTED_MODEL",
        "sourceAsset":ASSET,"sourcePage":SOURCE,"license":"CC0",
        "licenseSource":LICENCE,"authors":"See authoritative Poly Haven asset page",
        "sourceDescription":"Photographed weathered painted corrugated metal shutter",
        "sourceMaps":sources,"derivedMaterials":outputs,"microdetailStats":stats,
        "limitations":["Source is NOT clean interior powder coating",
            "Large-scale ridges/dirt suppressed by highpass filtering",
            "No original glTF/atlas/geometry modified",
            "No UV0/UV1/contact AO or genuine browser artistic validation",
            "No production deployment"],"assetClass":"source-intake only"}
    (a.out / "photo_metal_receipt.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PHOTO_PAINTED_METAL_CC0_SOURCE_VERIFIED",json.dumps({
        "asset":ASSET,"sourceHashes":{k:v["sourceSha256"] for k,v in sources.items()},
        "stats":stats}))
if __name__=="__main__":
    main()
