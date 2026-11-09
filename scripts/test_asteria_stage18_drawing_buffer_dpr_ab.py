#!/usr/bin/env python3
"""Stage18: one-variable actual WebGL drawing-buffer pixel resolution diagnostic.

Same exact Stage12 source and five GLBs, cameras, lighting/shadows, controls,
room geometry, CSS viewport and UI. Only Playwright emulated device pixel ratio
changes (1.0 to 0.5) to isolate rasterization load; no site source patch.
This is a SwiftShader A/B diagnostic, NOT a deployment or art acceptance.
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

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
ROUTE = "3d-preview-v5-command-envelope"
assert (ROOT / ROUTE / "index.html").is_file()
metadata = json.loads((ROOT / ROUTE / "models/envelope-manifest.json").read_text())
expected_faces = int(metadata["newEnvelopeTriangles"])
assert expected_faces == 8544, expected_faces
SHOTS = [("aft", 1280, 800), ("command", 1280, 800),
         ("science", 1280, 800), ("envelopeWall", 1280, 800),
         ("envelopeCeiling", 1280, 800), ("aft", 390, 844),
         ("command", 390, 844)]
MODES = ("native-dpr", "half-dpr")

RAF_PROBE = """async () => {
  const times=[];
  const start=performance.now();
  const framesBefore=Number(document.body.dataset.renderedFrames||0);
  const status=await Promise.race([
    (async()=>{
      for(let i=0;i<8;i++)
        await new Promise(resolve=>requestAnimationFrame(t=>{times.push(t);resolve()}));
      return 'sampled';
    })(),
    new Promise(resolve=>setTimeout(()=>resolve('watchdog-timeout'),60000))
  ]);
  const gaps=times.slice(1).map((t,i)=>t-times[i]);
  return {status,visibility:document.visibilityState,hidden:document.hidden,
          meanMs:gaps.length?gaps.reduce((s,n)=>s+n,0)/gaps.length:null,
          intervalsMs:gaps.map(x=>Number(x.toFixed(2))),
          frameDelta:Number(document.body.dataset.renderedFrames||0)-framesBefore,
          elapsedWallMs:performance.now()-start};
}"""

server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0),
    functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = f"http://127.0.0.1:{server.server_port}"
captures = []
pacing = []
navigation = []
try:
    with sync_playwright() as p:
        chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
        assert chrome, "Actual Chromium required; never use a synthetic mock"
        browser = p.chromium.launch(
            executable_path=chrome, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--enable-webgl",
                  "--use-gl=angle", "--use-angle=swiftshader",
                  "--enable-unsafe-swiftshader"])
        for view, width, height in SHOTS:
            for mode in MODES:
                mobile = width < 500
                emulated_dpr = 0.5 if mode == "half-dpr" else 1.0
                url = f"{origin}/{ROUTE}/?studioCapture={view}"
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=emulated_dpr, has_touch=mobile)
                errors, requests = [], []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("response", lambda response: errors.append(
                    f"HTTP_{response.status}: {response.url}")
                    if response.status >= 400 else None)
                page.on("request", lambda request: requests.append(request.url))
                response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                assert response and response.status == 200
                page.wait_for_function(
                    "document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",
                    timeout=150000)
                page.wait_for_function(
                    "document.body.dataset.threeBayLoaded==='true'||document.body.dataset.rendererReady==='error'",
                    timeout=150000)
                page.wait_for_function(
                    "document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",
                    timeout=180000)
                page.wait_for_function(
                    "Number(document.body.dataset.renderedFrames||0)>=4",
                    timeout=120000)
                observation = page.evaluate("""() => ({
                   ready:document.body.dataset.rendererReady,
                   error:document.getElementById('error')?.textContent||'',
                   room:window.__asteriaV5?.roomId,
                   sourceV3:window.__asteriaV5?.sourceV3Sha,
                   writes:window.__asteriaV5?.changesCampaign,
                   originalFaces:Number(document.body.dataset.geometryTriangles),
                   chairFaces:Number(document.body.dataset.heroChairFaces),
                   commandFaces:Number(document.body.dataset.commandMeshFaces),
                   commandAO:Number(document.body.dataset.commandBakedAoMaterials),
                   threeBayLoaded:document.body.dataset.threeBayLoaded,
                   threeBayFaces:Number(document.body.dataset.threeBayFaces),
                   envelopeLoaded:document.body.dataset.envelopeLoaded,
                   envelopeFaces:Number(document.body.dataset.envelopeFaces),
                   envelopeMeshes:Number(document.body.dataset.envelopeMeshes),
                   envelopeAO:Number(document.body.dataset.envelopeAOMaterials),
                   envelopeOriginalRemoved:Number(document.body.dataset.envelopeOriginalRemoved),
                   renderedFrames:Number(document.body.dataset.renderedFrames),
                   urlShadowFlag:new URLSearchParams(location.search).get('shadows'),
                   cssViewport:[window.innerWidth,window.innerHeight],
                   emulatedDpr:window.devicePixelRatio,
                   canvasSize:[document.getElementById('scene').width,document.getElementById('scene').height],
                   canvasClientSize:[document.getElementById('scene').clientWidth,document.getElementById('scene').clientHeight],
                   ceilingBounce:document.body.dataset.ceilingBounce||'unknown'
                })""")
                assert observation["ready"] == "true" and not observation["error"], (mode, observation)
                assert observation["room"] == "AST-D01-BRIDGE"
                assert observation["sourceV3"] == "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
                assert observation["writes"] is False
                assert observation["originalFaces"] == 81050
                assert observation["chairFaces"] == 31484
                assert observation["commandFaces"] == 16292 and observation["commandAO"] >= 1
                assert observation["threeBayLoaded"] == "true" and observation["threeBayFaces"] == 13098
                assert observation["envelopeLoaded"] == "true" and observation["envelopeFaces"] == 8544
                assert observation["envelopeMeshes"] == 30 and observation["envelopeAO"] >= 2
                assert observation["envelopeOriginalRemoved"] == 864
                assert observation["urlShadowFlag"] is None
                assert abs(observation["emulatedDpr"] - emulated_dpr) < 0.01, (mode, observation)
                assert observation["cssViewport"] == [width, height], (mode, observation)
                cssw, cssh = observation["canvasClientSize"]
                pxw, pxh = observation["canvasSize"]
                assert cssw >= width - 2 and cssh >= height - 2, (mode, observation)
                assert abs(pxw / cssw - emulated_dpr) < 0.015, (mode, observation)
                assert abs(pxh / cssh - emulated_dpr) < 0.015, (mode, observation)
                assert not errors, (mode, errors)
                assert all(u.startswith(origin) for u in requests if u.startswith("http"))
                glbs = {u for u in requests if u.endswith(".glb")}
                assert len(glbs) == 5, (mode, glbs)
                if mobile:
                    overlap = page.evaluate("""() => {
                      const a=document.getElementById('topTitle').getBoundingClientRect();
                      const b=document.getElementById('panel').getBoundingClientRect();
                      return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                             Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
                    }""")
                    assert overlap == 0, (mode, view, overlap)
                filename = f"stage18-{mode}-{view}-{width}x{height}.png"
                page.screenshot(path=str(OUT / filename), scale="css", timeout=120000)
                pixels = np.asarray(Image.open(OUT / filename).convert("RGB"))
                assert pixels.std(axis=(0, 1)).mean() > 16, filename
                diagnostic = None
                if view == "aft":
                    diagnostic = page.evaluate(RAF_PROBE)
                    entry = {"mode": mode, "view": view,
                             "viewport": [width, height],
                             "emulatedDevicePixelRatio": emulated_dpr,
                             "measuredDrawingBuffer": observation["canvasSize"],
                             "measuredCssCanvas": observation["canvasClientSize"],
                             "mobileOriginalShadowsAlreadyDisabled": mobile,
                             "measurement": diagnostic,
                             "originalThresholdMs": 1000,
                             "gatePass": diagnostic["status"] == "sampled" and
                                diagnostic["meanMs"] is not None and
                                0 < diagnostic["meanMs"] < 1000}
                    pacing.append(entry)
                    print("STAGE18_SAME_MODEL_SHADOWS_ONLY_FRAME_PACING",
                          json.dumps(entry), flush=True)
                captures.append({"mode": mode, "view": view,
                                 "width": width, "height": height,
                                 "emulatedDevicePixelRatio": emulated_dpr,
                                 "screenshot": filename, "observation": observation,
                                 "requestedGLBs": sorted(glbs), "pageErrors": errors})
                print("STAGE18_REAL_CHROMIUM_SCREENSHOT",
                      mode, view, width, filename, flush=True)
                page.close()
        deltas = {}
        for view, width, height in SHOTS:
            a = np.asarray(Image.open(
                OUT / f"stage18-native-dpr-{view}-{width}x{height}.png").convert("RGB"),
                dtype=np.int16)
            b = np.asarray(Image.open(
                OUT / f"stage18-half-dpr-{view}-{width}x{height}.png").convert("RGB"),
                dtype=np.int16)
            diff = np.abs(a - b)
            delta = {"meanAbsRGB": round(float(diff.mean()), 6),
                     "fractionPixelsDeltaOver10": round(float(
                         (diff.max(axis=2) > 10).mean()), 6)}
            deltas[f"{view}/{width}"] = delta
            print("STAGE18_REAL_SAME_CAMERA_DPR_ONLY_DELTA",
                  view, width, json.dumps(delta), flush=True)
        for mode in MODES:
            page = browser.new_page(viewport={"width": 860, "height": 560},
                device_scale_factor=(0.5 if mode == "half-dpr" else 1.0))
            page.goto(f"{origin}/{ROUTE}/?studioCapture=aft",
                      wait_until="domcontentloaded", timeout=60000)
            page.wait_for_function(
                "document.body.dataset.envelopeLoaded==='true'", timeout=180000)
            before = page.evaluate("window.__asteriaV5.getPosition()")
            n = page.evaluate("Number(document.body.dataset.renderedFrames||0)")
            page.keyboard.down("w")
            try:
                page.wait_for_function(
                    "(n)=>Number(document.body.dataset.renderedFrames||0)>=n+3",
                    arg=n, timeout=120000)
            finally:
                page.keyboard.up("w")
            after = page.evaluate("window.__asteriaV5.getPosition()")
            moved = abs(after["x"] - before["x"]) + abs(after["z"] - before["z"])
            assert moved > .025, (mode, before, after)
            page.locator('[data-go="command"]').click()
            position = page.evaluate("window.__asteriaV5.getPosition()")
            assert abs(position["x"] + 2.32) < .01 and abs(position["z"] - 2.15) < .01, position
            navigation.append({"mode": mode, "movementMeters": moved,
                               "commandWaypointPass": True})
            page.close()
        browser.close()
finally:
    server.shutdown()
report = {
    "id": "ASTERIA_STAGE18_DRAWING_BUFFER_DPR_SINGLE_VARIABLE_DIAGNOSTIC",
    "sourceStage12SHA": "e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b",
    "originalV3Blob": "74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
    "singleVariable": "Playwright browser device_scale_factor 1.0 versus 0.5, same CSS viewport and source; measured actual canvas drawing-buffer sizes",
    "controlsFixed": "Original Stage12 browser app, five models, geometry, UV, scan provenance, shadows and camera; only emulated DPR differs",
    "desktopShadows": "original 2048 PCFSoft pass ON in BOTH variants",
    "bothMobileModes": "shadow maps OFF by unchanged original !mobile condition",
    "matchedRealChromiumScreenshots": captures,
    "measurements": pacing,
    "actualPixelDifferences": deltas,
    "navigation": navigation,
    "retainedOriginalPerformanceThresholdMs": 1000,
    "allMeasuredPerformanceGatePass": bool(pacing) and all(p["gatePass"] for p in pacing),
    "physicalIphoneGpuVerified": False,
    "noReleaseApprovalRegardlessOfDiagnosticPass": True,
    "notUserArtApproved": True,
    "productionUnchanged": True
}
(OUT / "stage18-shadowmap-browser-report.json").write_text(
    json.dumps(report, indent=2) + "\n")
print("ASTERIA_STAGE18_DRAWING_BUFFER_ONLY_DIAGNOSTIC_COMPLETE",
      json.dumps(deltas), flush=True)
