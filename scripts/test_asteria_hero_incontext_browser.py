#!/usr/bin/env python3
"""In-context chair A/B browser QA, using real software-WebGL Chromium.

The earlier V3/V5 pages remain byte-for-byte untouched. The test verifies
separate source-sculpted hero chair against the room from which only the exact
frozen V3 captain chair call was removed. No campaign data is read or written.
"""
from __future__ import annotations

import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import sys
import threading

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

root=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve()
out.mkdir(parents=True,exist_ok=True)
assert (root/"3d-preview-v5-chair/index.html").is_file()
assert (root/"3d-preview-v5/index.html").is_file()

server=http.server.ThreadingHTTPServer(
 ("127.0.0.1",0),
 functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
origin=f"http://127.0.0.1:{server.server_port}"
results=[]
try:
    with sync_playwright() as p:
        chrome=os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
        assert chrome,"A local real Chromium browser executable is required"
        browser=p.chromium.launch(executable_path=chrome,headless=True,args=[
            "--no-sandbox","--disable-dev-shm-usage","--enable-webgl",
            "--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader",
        ])
        shots=[
            ("3d-preview-v5-chair","aft",1280,800),
            ("3d-preview-v5-chair","command",1280,800),
            ("3d-preview-v5-chair","chairReview",1280,800),
            ("3d-preview-v5-chair","science",1280,800),
            ("3d-preview-v5-chair","aft",390,844),
            ("3d-preview-v5","aft",1280,800),
            ("3d-preview-v5","command",1280,800),
        ]
        for route,view,width,height in shots:
            page=browser.new_page(viewport={"width":width,"height":height},
                                  device_scale_factor=1,has_touch=width<500)
            errors=[]
            external=[]
            page.on("pageerror",lambda exc:errors.append(str(exc)))
            page.on("request",lambda req:external.append(req.url)
                    if req.url.startswith("http") and not req.url.startswith(origin) else None)
            response=page.goto(f"{origin}/{route}/?studioCapture={view}",
                               wait_until="domcontentloaded",timeout=45000)
            assert response and response.status==200,(route,response.status if response else None)
            page.wait_for_function("""() => ['true','error'].includes(document.body.dataset.rendererReady)""",
                                   timeout=90000)
            page.wait_for_timeout(750)
            data=page.evaluate("""() => ({
                ready:document.body.dataset.rendererReady,
                scene:document.body.dataset.sceneVersion,
                geometryFaces:Number(document.body.dataset.geometryTriangles),
                removedFaces:Number(document.body.dataset.captainChairFacesRemoved),
                heroFaces:Number(document.body.dataset.heroChairFaces),
                heroMeshes:Number(document.body.dataset.heroChairMeshes),
                heroLoaded:document.body.dataset.chairOverlayLoaded,
                materials:document.body.dataset.missingMaterials,
                source:window.__asteriaV5?.sourceV3Sha,
                noGameWrites:window.__asteriaV5?.changesCampaign === false,
                review:window.__asteriaChairReview || null,
                frames:Number(document.body.dataset.renderedFrames || 0)
            })""")
            filename=f"{route}-{view}-{width}.png"
            page.screenshot(path=str(out/filename),timeout=60000)
            pix=np.asarray(Image.open(out/filename).convert("RGB"),dtype=np.float32)
            spread=float(pix.std(axis=(0,1)).mean())
            data.update({"route":route,"view":view,"width":width,"height":height,
                         "screenshot":filename,"pixelStd":round(spread,2),
                         "jsErrors":errors,"externalRequests":external})
            results.append(data)
            print(json.dumps(data),flush=True)
            assert data["ready"]=="true" and data["frames"]>0,data
            assert data["geometryFaces"]>0 and data["materials"]=="0",data
            assert data["source"]=="74a154ae62bccb0c16d03c2ecf791a64ab19ce81",data
            assert data["noGameWrites"],data
            assert not errors and not external,data
            assert spread>22,("Blank or uniform WebGL screenshot",data)
            if route=="3d-preview-v5-chair":
                assert data["heroLoaded"]=="true" and data["heroFaces"]==26908,data
                assert data["removedFaces"]>1000,data
                assert data["geometryFaces"]+data["removedFaces"]==106988,data
                assert data["heroMeshes"]>=20,data
                assert data["review"]["noGameWrites"] is True,data
            else:
                assert data["geometryFaces"]==106988,data
            page.close()
        # One frozen-view composition comparison. This detects whether the
        # proposed chair affects actual rendered pixels (not just JSON counters).
        def image(name):
            return np.asarray(Image.open(out/name).convert("RGB"),dtype=np.int16)
        for view in ("aft","command"):
            changed=image(f"3d-preview-v5-chair-{view}-1280.png")
            baseline=image(f"3d-preview-v5-{view}-1280.png")
            difference=float(np.abs(changed-baseline).mean())
            assert difference>2,("Hero chair render indistinguishable from original",view,difference)
            print(f"PIXEL_COMPARE_{view.upper()} mean_abs_difference={difference:.3f}",flush=True)
        page=browser.new_page(viewport={"width":860,"height":560})
        page.goto(f"{origin}/3d-preview-v5-chair/?studioCapture=aft",
                  wait_until="domcontentloaded")
        page.wait_for_function("document.body.dataset.rendererReady==='true'",timeout=90000)
        start=page.evaluate("window.__asteriaV5.getPosition()")
        page.keyboard.down("w")
        page.wait_for_timeout(2200)
        page.keyboard.up("w")
        finish=page.evaluate("window.__asteriaV5.getPosition()")
        page.locator('[data-go="command"]').click()
        command=page.evaluate("window.__asteriaV5.getPosition()")
        assert abs(start["x"]-finish["x"])+abs(start["z"]-finish["z"])>.025,(start,finish)
        assert abs(command["x"]+2.32)<.01 and abs(command["z"]-2.15)<.01,command
        assert page.evaluate("window.__asteriaV5.changesCampaign") is False
        print("WALKING",json.dumps({"start":start,"after":finish,"command":command}),flush=True)
        # Touch viewport: verify actual original controls still accept taps.
        phone=browser.new_page(viewport={"width":390,"height":844},has_touch=True)
        phone.goto(f"{origin}/3d-preview-v5-chair/?studioCapture=aft")
        phone.wait_for_function("document.body.dataset.rendererReady==='true'",timeout=90000)
        phone.locator('[data-go="flight"]').click(timeout=30000)
        flight=phone.evaluate("window.__asteriaV5.getPosition()")
        assert abs(flight["z"]+1.32)<.01,flight
        print("TOUCH_STATION",json.dumps(flight),flush=True)
        phone.close();page.close();browser.close()
finally:
    server.shutdown()

(out/"browser-qa.json").write_text(json.dumps(results,indent=2)+"\n")
