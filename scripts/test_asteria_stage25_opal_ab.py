#!/usr/bin/env python3
"""Stage25 six-diffuser emissive-material A/B: exact Stage24 geometry/UI, real Chromium.

ART HOLD until actual images examined. Pixel change and HUD clipping do not
prove photorealism. Does not publish any route or modify production.
"""
from __future__ import annotations
import functools, hashlib, http.server, json, os, shutil, sys, threading
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

site = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
original = "3d-preview-v5-command-stage24"
reduced = "3d-preview-v5-command-envelope"
for name in (original, reduced):
    assert (site / name / "app.js").is_file(), name
    assert (site / name / "models" / "envelope-manifest.json").is_file(), name

def fingerprint(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

for p in (site / original).rglob("*"):
    if not p.is_file():
        continue
    q = site / reduced / p.relative_to(site / original)
    assert q.is_file(), (p, q)
    if p.name == "asteria-realistic-architectural-envelope-08.glb":
        assert fingerprint(p) != fingerprint(q), "Six-only material should change GLB"
    else:
        assert fingerprint(p) == fingerprint(q), ("Unexpected app/UI/other asset drift", p)
old_app = (site / original / "app.js").read_text()
new_app = (site / reduced / "app.js").read_text()
assert old_app == new_app, "Stage25 cannot alter game/WebGL renderer code"

server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0),
    functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site)),
)
threading.Thread(target=server.serve_forever, daemon=True).start()
origin = "http://127.0.0.1:" + str(server.server_port)
poses = [
    ("command", 1280, 800),
    ("envelopeCeiling", 1280, 800),
    ("envelopeWall", 1280, 800),
    ("aft", 1280, 800),
    ("command", 390, 844),
    ("envelopeWall", 390, 844),
    ("aft", 390, 844),
]
files = {}
observations = {}
try:
    with sync_playwright() as playwright:
        exe = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
        assert exe, "Actual installed Chromium is required, no fake screenshots"
        browser = playwright.chromium.launch(
            executable_path=exe, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--enable-webgl",
                  "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        for camera, width, height in poses:
            for route in (original, reduced):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1, has_touch=(width < 500),
                )
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("response", lambda r: errors.append("HTTP_" + str(r.status) + ": " + r.url)
                        if r.status >= 400 else None)
                response = page.goto(
                    f"{origin}/{route}/?studioCapture={camera}",
                    wait_until="domcontentloaded", timeout=60000,
                )
                assert response and response.status == 200
                page.wait_for_function(
                    "document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",
                    timeout=180000,
                )
                page.wait_for_function(
                    "Number(document.body.dataset.renderedFrames||0)>=4", timeout=90000
                )
                obs = page.evaluate("""() => ({
                    ready:document.body.dataset.rendererReady,
                    sourceV3:window.__asteriaV5?.sourceV3Sha,
                    room:window.__asteriaV5?.roomId,
                    writes:window.__asteriaV5?.changesCampaign,
                    geometryTriangles:Number(document.body.dataset.geometryTriangles),
                    envelopeFaces:Number(document.body.dataset.envelopeFaces),
                    envelopeMeshes:Number(document.body.dataset.envelopeMeshes),
                    frames:Number(document.body.dataset.renderedFrames),
                    error:document.getElementById('error')?.textContent||''
                })""")
                assert obs["ready"] == "true" and obs["error"] == "", (route, camera, obs)
                assert obs["sourceV3"] == "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
                assert obs["room"] == "AST-D01-BRIDGE" and obs["writes"] is False
                assert obs["geometryTriangles"] == 81050 and obs["envelopeMeshes"] == 74, obs
                assert not errors, (route, camera, errors)
                name = f"{route}-{camera}-{width}x{height}.png"
                page.screenshot(path=str(out / name), timeout=60000)
                rgb = np.asarray(Image.open(out / name).convert("RGB"))
                assert float(rgb.std(axis=(0,1)).mean()) > 16, (route, camera)
                files[(route, camera, width)] = name
                observations[(route, camera, width)] = obs
                page.close()
        browser.close()
finally:
    server.shutdown()

def regional_metrics(rgb, box):
    x0, y0, x1, y1 = box
    crop = rgb[y0:y1, x0:x1].astype(np.float64)
    gray = crop[...,0] * .2126 + crop[...,1] * .7152 + crop[...,2] * .0722
    return {
        "meanSrgbLuma": round(float(gray.mean()), 4),
        "lumaStd": round(float(gray.std()), 4),
        "nearWhiteFractionLuma245": round(float((gray >= 245).mean()), 6),
        "nearWhiteFractionAnyChannel250": round(float((crop.max(axis=2)>=250).mean()),6),
        "lumaP95": round(float(np.percentile(gray,95)), 4),
    }

comparison = {}
for camera, width, height in poses:
    a = np.asarray(Image.open(out / files[(original,camera,width)]).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(out / files[(reduced,camera,width)]).convert("RGB"), dtype=np.int16)
    assert a.shape == b.shape == (height,width,3)
    delta = np.abs(a-b)
    # Luminance of the actual bridge upper-left HUD backdrop, not edited UI.
    boxes = {"fullFrame":(0,0,width,height)}
    if width == 1280:
        boxes.update({
            "portArchitectureBehindHud":(0,0,400,210),
            "upperCeiling":(230,0,950,145),
            "forwardFlankLeft":(0,90,370,420),
        })
    else:
        boxes["mobileUpperHalf"]=(0,0,width,420)
    stats = {
        "changedPixelFractionOver10":round(float((delta.max(axis=2)>10).mean()),6),
        "meanAbsoluteRgb":round(float(delta.mean()),5),
        "stage24Control":{k:regional_metrics(a,box) for k,box in boxes.items()},
        "stage25Candidate":{k:regional_metrics(b,box) for k,box in boxes.items()},
    }
    comparison[f"{camera}/{width}"]=stats
    sheet=Image.new("RGB",(width*2,height))
    sheet.paste(Image.fromarray(a.astype(np.uint8)),(0,0))
    sheet.paste(Image.fromarray(b.astype(np.uint8)),(width,0))
    sheet.save(out/f"stage24-vs-stage25-opal-{camera}-{width}-ab.jpg",quality=91)
    print("STAGE25_STAGE24_REAL_CHROMIUM_OPAL_ONLY",camera,width,
          stats["changedPixelFractionOver10"],flush=True)

report={
    "purpose":"A/B isolate six new opal diffuser emissiveFactors, keeping Stage24 point-light power 0.45",
    "stage24Head":"133289b42d6a59a255daab9bd83995a348b7fda4",
    "unchangedStage24WebGLPointLightIntensity":0.45,
    "candidateEmissionFactorRatio":0.20,
    "comparison":comparison,
    "assetHash":{str(p.relative_to(site/original)):fingerprint(p)
                 for p in (site/original).rglob("*") if p.is_file() and p.name!="asteria-realistic-architectural-envelope-08.glb"},
    "chromiumViews":[{"route":r,"camera":c,"width":w,"file":files[(r,c,w)],
                      "observation":observations[(r,c,w)]}
                     for c,w,h in poses for r in (original,reduced)],
    "sameGeometryUVTextureCameraHUDAndAllOtherMaterials":True,
    "historicalProductionUntouched":True,
    "published":False,
    "ownerArtApproved":False,
    "physicalDevicePerformanceProven":False,
    "subjectiveContrastAcceptable":None
}
(out/"stage25-opal-browser-report.json").write_text(json.dumps(report,indent=2)+"\n")
print("STAGE25_REAL_BROWSER_AB_DONE_ART_REVIEW_REQUIRED",flush=True)
