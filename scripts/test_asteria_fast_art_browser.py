#!/usr/bin/env python3
"""Fast genuine Chromium two-camera visual review of one command GLB.

This is an art *screening* tool, NEVER the full Cycles/UV1/movement release gate.
Control and candidate use identical site/app/HUD and all other unchanged GLBs.
"""
from __future__ import annotations
import argparse
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

COMMAND = "models/asteria-command-set-candidate.glb"
SHOTS = (("desktop", 1280, 800), ("mobile", 390, 844))
def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--base-sha", required=True)
    args = ap.parse_args()
    control = args.site / "control"
    candidate = args.site / "candidate"
    assert args.base_sha and len(args.base_sha) == 40
    a = {p.relative_to(control).as_posix():hash_file(p)
         for p in control.rglob("*") if p.is_file()}
    b = {p.relative_to(candidate).as_posix():hash_file(p)
         for p in candidate.rglob("*") if p.is_file()}
    assert set(a) == set(b) and COMMAND in a, "Art trial must have identical file inventory"
    mismatched = [k for k in sorted(a) if a[k] != b[k]]
    assert not set(mismatched) - {COMMAND}, ("Non-art asset differs", mismatched)
    assert a["app.js"] == b["app.js"] and a["index.html"] == b["index.html"]
    args.out.mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    assert chrome, "Real Chromium is required"
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(args.site))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = "http://127.0.0.1:" + str(server.server_port)
    report = {
        "kind": "ASTERIA_COMMAND_ART_FIRST_TWO_CAMERA_AB_V1",
        "sourceBaseline": args.base_sha,
        "artChanges": mismatched,
        "controlCommandSHA256": a[COMMAND],
        "candidateCommandSHA256": b[COMMAND],
        "comparison": {},
        "artApproved": False,
        "fullReleaseQACompleted": False,
    }
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=chrome, headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--enable-webgl",
                      "--use-gl=angle", "--use-angle=swiftshader",
                      "--enable-unsafe-swiftshader"]
            )
            for label, width, height in SHOTS:
                images = {}
                for route in ("control", "candidate"):
                    page = browser.new_page(
                        viewport={"width": width, "height": height},
                        device_scale_factor=1, has_touch=width < 500
                    )
                    errors = []
                    requested = []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.on("response", lambda r: errors.append("HTTP " + str(r.status) + " " + r.url)
                            if r.status >= 400 else None)
                    page.on("request", lambda r: requested.append(r.url))
                    response = page.goto(origin + "/" + route + "/?studioCapture=command",
                                         wait_until="domcontentloaded", timeout=60000)
                    assert response and response.status == 200
                    page.wait_for_function(
                        "document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",
                        timeout=120000)
                    page.wait_for_function(
                        "document.body.dataset.threeBayLoaded==='true'||document.body.dataset.rendererReady==='error'",
                        timeout=120000)
                    page.wait_for_function(
                        "document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",
                        timeout=180000)
                    page.wait_for_function(
                        "Number(document.body.dataset.renderedFrames||0)>=4",
                        timeout=90000)
                    observed = page.evaluate("""() => ({
                      ready:document.body.dataset.rendererReady,
                      error:document.getElementById('error')?.textContent||'',
                      room:window.__asteriaV5?.roomId,
                      source:window.__asteriaV5?.sourceV3Sha,
                      writes:window.__asteriaV5?.changesCampaign,
                      floor:Number(document.body.dataset.geometryTriangles),
                      chair:Number(document.body.dataset.heroChairFaces),
                      command:Number(document.body.dataset.commandMeshFaces),
                      removed:Number(document.body.dataset.commandFacesRemoved),
                      envelope:document.body.dataset.envelopeLoaded,
                      threeBay:document.body.dataset.threeBayLoaded,
                      ao:Number(document.body.dataset.commandBakedAoMaterials),
                      frames:Number(document.body.dataset.renderedFrames)
                    })""")
                    assert observed["ready"] == "true" and not observed["error"], (route, observed)
                    assert observed["room"] == "AST-D01-BRIDGE"
                    assert observed["source"] == "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
                    assert observed["writes"] is False
                    assert observed["floor"] == 80846 and observed["chair"] == 31484
                    assert observed["removed"] == 8628
                    assert observed["envelope"] == observed["threeBay"] == "true"
                    assert observed["command"] > 4000 and observed["ao"] >= 1
                    assert not errors, (route, errors)
                    assert all(u.startswith(origin) for u in requested if u.startswith("http"))
                    glbs = {u for u in requested if u.endswith(".glb")}
                    assert len(glbs) == 5, (route, glbs)
                    file = args.out / f"command-{label}-{route}-{width}x{height}.png"
                    page.screenshot(path=str(file), timeout=60000)
                    images[route] = Image.open(file).convert("RGB")
                    assert np.asarray(images[route]).std(axis=(0,1)).mean() > 16
                    page.close()
                arr0 = np.asarray(images["control"], dtype=np.int16)
                arr1 = np.asarray(images["candidate"], dtype=np.int16)
                diff = np.abs(arr0 - arr1).max(axis=2) > 10
                quarters = [round(float(part.mean() * 100), 3)
                            for part in np.array_split(diff, 4, axis=0)]
                pair = Image.new("RGB", (width * 2, height))
                pair.paste(images["control"], (0,0))
                pair.paste(images["candidate"], (width,0))
                pair.save(args.out / f"command-{label}-actual-before-after.jpg", quality=92)
                report["comparison"][label] = {
                    "viewport": [width,height],
                    "changedRGBOver10Percent":round(float(diff.mean() * 100), 4),
                    "verticalQuartersPercent":quarters,
                    "humanArtReview": "PENDING",
                }
            browser.close()
    finally:
        server.shutdown()
    (args.out / "art-first-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("ASTERIA_ACTUAL_BROWSER_ART_FIRST_AB", json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
