#!/usr/bin/env python3
"""Source-exact Stage12 vs Stage22 full-furnished Chromium A/B — no publishing.

The new hatch must be observed from identical real camera controls. JSON report
is technical evidence only; artistic approval requires separate human review.
"""
from __future__ import annotations
import functools
import http.server
import json
import os
import shutil
import sys
import threading
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

root=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve()
out.mkdir(parents=True,exist_ok=True)
base="3d-preview-v5-command-envelope"
candidate="3d-preview-v5-command-envelope-hatches"
for route in (base,candidate):
 assert (root/route/"index.html").is_file()
 assert (root/route/"models/asteria-v3-restored-pbr.glb").is_file()
manifest=json.loads((root/candidate/"models/manifest.json").read_text())
assert manifest["triangles"] == 80810
assert manifest["side_hatches_source_faces_removed"] == 240
assert [(r["start"],r["end"]) for r in manifest["side_hatches_source_ranges"]]==[
 (92830,92950),(92950,93070)]
shots=[("aft",1280,800),("command",1280,800),("science",1280,800),
       ("envelopeWall",1280,800),("envelopeCeiling",1280,800),
       ("aft",390,844),("envelopeWall",390,844),("command",390,844)]
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),
    functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_port}"
observed=[]
comparison={}
try:
 with sync_playwright() as playwright:
  binary=os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
  if not binary:raise RuntimeError("Real Chromium executable required")
  browser=playwright.chromium.launch(executable_path=binary,headless=True,
       args=["--no-sandbox","--disable-dev-shm-usage","--enable-webgl",
            "--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
  for camera,w,h in shots:
   for route in (base,candidate):
    page=browser.new_page(viewport={"width":w,"height":h},
                          device_scale_factor=1,has_touch=w<500)
    errors=[];requests=[]
    page.on("pageerror",lambda err:errors.append(str(err)))
    page.on("response",lambda resp:errors.append(f"HTTP_{resp.status}:{resp.url}")
            if resp.status>=400 else None)
    page.on("request",lambda request:requests.append(request.url))
    response=page.goto(f"{origin}/{route}/?studioCapture={camera}",
      wait_until="domcontentloaded",timeout=60000)
    assert response and response.status==200
    page.wait_for_function("document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",
      timeout=120000)
    page.wait_for_function("document.body.dataset.threeBayLoaded==='true'||document.body.dataset.rendererReady==='error'",
      timeout=120000)
    page.wait_for_function("document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",
      timeout=120000)
    if route==candidate:
     page.wait_for_function("document.body.dataset.hatchLoaded==='true'||document.body.dataset.rendererReady==='error'",
       timeout=120000)
    page.wait_for_function("Number(document.body.dataset.renderedFrames||0)>=4",timeout=120000)
    value=page.evaluate("""() => ({
      ready:document.body.dataset.rendererReady,
      error:document.querySelector('#error')?.textContent||'',
      sourceV3:window.__asteriaV5?.sourceV3Sha,
      writes:window.__asteriaV5?.changesCampaign,
      room:window.__asteriaV5?.roomId,
      originalFaces:Number(document.body.dataset.geometryTriangles),
      chairFaces:Number(document.body.dataset.heroChairFaces),
      commandFaces:Number(document.body.dataset.commandMeshFaces),
      tripleFaces:Number(document.body.dataset.threeBayFaces),
      envelopeFaces:Number(document.body.dataset.envelopeFaces),
      originalShellRemoved:Number(document.body.dataset.envelopeOriginalRemoved),
      hatchLoaded:document.body.dataset.hatchLoaded||'none',
      hatchMeshes:Number(document.body.dataset.hatchMeshes||0),
      hatchFaces:Number(document.body.dataset.hatchFaces||0),
      hatchRemoved:Number(document.body.dataset.hatchOriginalRemoved||0),
      frames:Number(document.body.dataset.renderedFrames||0)
    })""")
    assert value["ready"]=="true" and not value["error"],(route,value)
    assert value["sourceV3"]=="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
    assert value["room"]=="AST-D01-BRIDGE" and value["writes"] is False
    assert value["originalFaces"]==(80810 if route==candidate else 81050),value
    assert value["chairFaces"]==31484 and value["commandFaces"]==16292
    assert value["tripleFaces"]==13098 and value["originalShellRemoved"]==864
    assert value["envelopeFaces"]==8544
    if route==candidate:
     assert value["hatchLoaded"]=="true" and value["hatchRemoved"]==240,value
     assert value["hatchMeshes"]>=80 and value["hatchFaces"]>2000,value
    else:
     assert value["hatchLoaded"]=="none" and value["hatchFaces"]==0,value
    if w<500:
     overlap=page.evaluate("""() => {
       const a=document.getElementById('topTitle').getBoundingClientRect();
       const b=document.getElementById('panel').getBoundingClientRect();
       return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
              Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
     }""")
     assert overlap==0,(camera,route,overlap)
    assert not errors,(route,errors)
    glbs=set(x for x in requests if x.endswith(".glb"))
    assert len(glbs)==(6 if route==candidate else 5),(route,glbs)
    filename=f"{route}-{camera}-{w}x{h}.png"
    page.screenshot(path=str(out/filename),timeout=90000)
    rgb=np.asarray(Image.open(out/filename).convert("RGB"))
    assert rgb.std(axis=(0,1)).mean()>16
    observed.append({"route":route,"view":camera,"width":w,"height":h,
                     "glbAssets":sorted(glbs),"observation":value,
                     "pageErrors":errors,"png":filename})
    page.close()
   old=np.asarray(Image.open(out/f"{base}-{camera}-{w}x{h}.png").convert("RGB"),dtype=np.int16)
   new=np.asarray(Image.open(out/f"{candidate}-{camera}-{w}x{h}.png").convert("RGB"),dtype=np.int16)
   delta=np.abs(new-old)
   fraction=float(np.mean(delta.max(axis=2)>10))
   mean=float(delta.mean())
   comparison[f"{camera}/{w}"]={"meanRgbAbsolute":round(mean,5),
                                  "fractionChangedOver10":round(fraction,6)}
   sheet=Image.new("RGB",(w*2,h))
   sheet.paste(Image.fromarray(old.astype(np.uint8)),(0,0))
   sheet.paste(Image.fromarray(new.astype(np.uint8)),(w,0))
   sheet.save(out/f"stage12-vs-stage22-{camera}-{w}-AB.jpg",quality=88)
   print("SOURCE_EXACT_STAGE22_PIXEL_DELTA",camera,w,comparison[f"{camera}/{w}"],flush=True)
  # Existing player movement and command teleport, geometry-only experiment.
  page=browser.new_page(viewport={"width":880,"height":560})
  page.goto(f"{origin}/{candidate}/?studioCapture=aft",wait_until="domcontentloaded")
  page.wait_for_function("document.body.dataset.hatchLoaded==='true'",timeout=120000)
  before=page.evaluate("window.__asteriaV5.getPosition()")
  n=page.evaluate("Number(document.body.dataset.renderedFrames||0)")
  page.keyboard.down("w")
  try:
   page.wait_for_function("(n) => Number(document.body.dataset.renderedFrames||0)>=n+3",
      arg=n,timeout=120000)
  finally:
   page.keyboard.up("w")
  after=page.evaluate("window.__asteriaV5.getPosition()")
  assert abs(after["x"]-before["x"])+abs(after["z"]-before["z"])>.025,(before,after)
  page.locator('[data-go="command"]').click()
  p=page.evaluate("window.__asteriaV5.getPosition()")
  assert abs(p["x"]+2.32)<.01 and abs(p["z"]-2.15)<.01,p
  page.close()
  browser.close()
finally:
 server.shutdown()
report={"id":"ASTERIA_STAGE22_ACTUAL_CHROMIUM_SOFTWARE_WEBGL_AB",
 "baselineStage12":"e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b",
 "sourceV3":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
 "onlyRemovedOriginalHatchSourceFaces":240,
 "realScreenshots":observed,"pixelDifferences":comparison,
 "movementCommandWaypointPass":True,
 "artApproved":False,"remotePagesTested":False,
 "physicalPhoneTested":False,"performanceGateUnverified":True}
(out/"stage22-browser-report.json").write_text(json.dumps(report,indent=2)+"\n")
# A small visible delta does not become "art approved" just by passing code.
assert comparison["envelopeWall/1280"]["fractionChangedOver10"]>.04,comparison
print("STAGE22_ACTUAL_CHROMIUM_BROWSER_GATE_PASS",json.dumps(comparison))
