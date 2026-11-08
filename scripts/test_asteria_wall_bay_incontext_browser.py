#!/usr/bin/env python3
"""Actual Chromium A/B render test of optional one-bay GLB.

This script uses a QA-only site folder; game source, controls and published
walkthroughs are not rewritten. Nonzero pixel differences prove visibility,
NOT improved artistic realism, proper lightmap baking, or owner approval.
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
control="3d-preview-v5-command"
candidate="3d-preview-v5-command-bay"
for route in (control,candidate):
    assert (root/route/"index.html").is_file(),route
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),
    functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_port}"
shots=[("aft",1280,800),("command",1280,800),("science",1280,800),
       ("command",390,844)]
state=[]
try:
 with sync_playwright() as playwright:
    exe=os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    if not exe:raise RuntimeError("Real Chromium browser not installed")
    browser=playwright.chromium.launch(executable_path=exe,headless=True,
         args=["--no-sandbox","--disable-dev-shm-usage","--enable-webgl",
               "--use-gl=angle","--use-angle=swiftshader",
               "--enable-unsafe-swiftshader"])
    for view,width,height in shots:
      for route in (control,candidate):
        page=browser.new_page(viewport={"width":width,"height":height},
               device_scale_factor=1,has_touch=width<500)
        errors=[]
        requests=[]
        page.on("pageerror",lambda err:errors.append(str(err)))
        page.on("response",lambda resp:errors.append(f"HTTP_{resp.status}: {resp.url}")
                if resp.status>=400 else None)
        page.on("request",lambda req:requests.append(req.url))
        response=page.goto(f"{origin}/{route}/?studioCapture={view}",
                            wait_until="domcontentloaded",timeout=60000)
        assert response and response.status==200
        page.wait_for_function("document.body.dataset.rendererReady === 'true' || document.body.dataset.rendererReady === 'error'",
                               timeout=120000)
        if route==candidate:
          page.wait_for_function("document.body.dataset.wallBayLoaded === 'true' || document.body.dataset.rendererReady === 'error'",
                                 timeout=120000)
        page.wait_for_function("Number(document.body.dataset.renderedFrames||0)>=4",timeout=90000)
        info=page.evaluate("""() => ({
          ready:document.body.dataset.rendererReady,
          error:document.getElementById('error')?.textContent,
          original:Number(document.body.dataset.geometryTriangles),
          hero:Number(document.body.dataset.heroChairFaces),
          command:Number(document.body.dataset.commandMeshFaces),
          commandAO:Number(document.body.dataset.commandBakedAoMaterials),
          bayLoaded:document.body.dataset.wallBayLoaded||'none',
          bayFaces:Number(document.body.dataset.wallBayFaces||0),
          bayMeshes:Number(document.body.dataset.wallBayMeshes||0),
          campaign:window.__asteriaV5?.changesCampaign,
          room:window.__asteriaV5?.roomId,
          frozen:window.__asteriaV5?.sourceV3Sha,
          renderedFrames:Number(document.body.dataset.renderedFrames||0)
        })""")
        assert info["ready"]=="true" and not info["error"],(route,info)
        assert info["original"]==82088 and info["hero"]==31484
        assert info["command"]==16292 and info["commandAO"]>=1
        assert info["room"]=="AST-D01-BRIDGE" and info["campaign"] is False
        assert info["frozen"]=="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
        if route==candidate:
          assert info["bayLoaded"]=="true" and info["bayFaces"]==1344 and info["bayMeshes"]>=40,info
        else:
          assert info["bayLoaded"]=="none",info
        if width<500:
          overlap=page.evaluate("""() => {
            const a=document.getElementById('topTitle').getBoundingClientRect();
            const b=document.getElementById('panel').getBoundingClientRect();
            return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                   Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
          }""")
          assert overlap==0,(route,'mobile heading collision',overlap)
        assert not errors,(route,errors)
        assert all(url.startswith(origin) for url in requests if url.startswith("http"))
        assets=set(s for s in requests if s.endswith(".glb"))
        assert len(assets)==(4 if route==candidate else 3),(route,assets)
        file=f"{route}-{view}-{width}x{height}.png"
        page.screenshot(path=str(out/file),timeout=60000)
        pixels=np.asarray(Image.open(out/file).convert("RGB"))
        assert pixels.std(axis=(0,1)).mean()>18,(route,view)
        state.append(dict(route=route,view=view,width=width,height=height,
                          image=file,observed=info,errors=errors,assets=sorted(assets)))
        print("REAL_BROWSER_FRAME",file,json.dumps(info),flush=True)
        page.close()
    diffs={}
    for view,width,height in shots:
      pa=np.asarray(Image.open(out/f"{control}-{view}-{width}x{height}.png").convert("RGB"),
                    dtype=np.int16)
      pb=np.asarray(Image.open(out/f"{candidate}-{view}-{width}x{height}.png").convert("RGB"),
                    dtype=np.int16)
      d=np.abs(pa-pb)
      whole=float(d.mean())
      changed=float((d.max(axis=2)>10).mean())
      # Does the actual room view show the extra kit? This can be very small
      # for the starboard forward bay seen from the aft command station.
      diffs[f"{view}/{width}"]={"meanAbsoluteRgb":round(whole,4),
                                "changedPixelFraction":round(changed,6)}
      if view in ("aft","command") and width>=500:
          assert whole>.07,(view,width,whole,"Optional bay not visibly rendered")
    page=browser.new_page(viewport={"width":860,"height":560})
    page.goto(f"{origin}/{candidate}/?studioCapture=aft",wait_until="domcontentloaded")
    page.wait_for_function("document.body.dataset.wallBayLoaded==='true'",timeout=120000)
    before=page.evaluate("window.__asteriaV5.getPosition()")
    n=page.evaluate("Number(document.body.dataset.renderedFrames||0)")
    page.keyboard.down("w")
    try:
      page.wait_for_function("(n) => Number(document.body.dataset.renderedFrames||0)>n+3",
          arg=n,timeout=90000)
    finally:page.keyboard.up("w")
    after=page.evaluate("window.__asteriaV5.getPosition()")
    assert abs(after["x"]-before["x"])+abs(after["z"]-before["z"])>.025,(before,after)
    page.close()
    browser.close()
finally:
 server.shutdown()
report={"qa":"real Chromium software-WebGL baseline-vs-bay",
        "originalV3Triangles":82088,"heroTriangles":31484,
        "commandTriangles":16292,"wallBayTriangles":1344,
        "screenshots":state,"matchedDifferences":diffs,
        "walkTest":"passed",
        "sourceAndCampaignUnchanged":True,
        "visualApproval":False,
        "notAQualityProof":True}
(out/"incontext-browser-results.json").write_text(json.dumps(report,indent=2)+"\n")
print("IN_CONTEXT_BAY_A_B_BROWSER_PASSED",json.dumps(diffs),flush=True)
