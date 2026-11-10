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
    V3 = "models/asteria-v3-restored-pbr.glb"
    META = "models/manifest.json"
    if V3 in mismatched:
        # Stage35 independently removes original 6476 opaque flightIsland V3
        # triangles and appends a coherent full-width manufactured desk into
        # the envelope GLB without changing original screens/chairs/controls.
        envelope="models/asteria-realistic-architectural-envelope-08.glb"
        envelope_manifest="models/envelope-manifest.json"
        assert set(mismatched)=={COMMAND,V3,META,"app.js",envelope,envelope_manifest}, (
            "Unexpected Stage35 asset changes",mismatched)
        prev=(control/"app.js").read_text()
        nxt=(candidate/"app.js").read_text()
        marker="Se!==106988-Be-ft-174-864-204"
        assert prev.count(marker)==1
        expected=prev.replace(marker,marker+"-96-6476",1)
        old=json.loads((control/META).read_text())
        new=json.loads((candidate/META).read_text())
        assert old["triangles"]==80846 and new["triangles"]==74274
        assert new["under_console_original_faces_removed"]==96
        assert new["stage35_forward_original_faces_removed"]==6476
        assert new["stage35_forward_original_source_span"]==[37104,43580]
        for key in ("under_console_original_faces_removed","under_console_source_ranges",
                    "stage35_forward_original_faces_removed","stage35_forward_original_source_span",
                    "triangles","sha256","bytes"):
            new.pop(key,None);old.pop(key,None)
        assert old==new,"Original V3 manifest changed outside source exclusion"
        oldenv=json.loads((control/envelope_manifest).read_text())
        newenv=json.loads((candidate/envelope_manifest).read_text())
        assert oldenv["newEnvelopeTriangles"]==27848 and oldenv["meshObjects"]==135
        art=newenv.pop("stage35OptionalGeometry")
        assert art["sourceFlightDeskRemovedFaces"]==6476 and len(art["names"])==14
        assert not art["artApproved"] and not art["newUV1OrGIProven"]
        newtriangles=art["newFaces"]
        assert newenv["newEnvelopeTriangles"]==27848+newtriangles
        assert newenv["meshObjects"]==149
        newenv["newEnvelopeTriangles"]=27848
        newenv["meshObjects"]=135
        assert oldenv==newenv,"Changed approved envelope manifest"
        guard="be!==27848||Te!==135"
        assert expected.count(guard)==1
        expected=expected.replace(guard,f'be!=={27848+newtriangles}||Te!==149',1)
        assert nxt==expected,"Original viewer changed beyond two model-count assertions"
        from asteria_stage35_flight_envelope import read
        orig,bin0=read((control/envelope).read_bytes())
        cand,bin1=read((candidate/envelope).read_bytes())
        assert bin1[:len(bin0)]==bin0,"Existing scanned envelope bytes changed"
        for key in ("meshes","nodes","materials","images","textures","samplers",
                    "bufferViews","accessors"):
            assert cand[key][:len(orig[key])]==orig[key],("Existing GLB mutated",key)
        assert len(cand["meshes"])==len(cand["nodes"])==149
    else:
        assert set(mismatched) <= {COMMAND}, ("Non-art asset differs",mismatched)
        assert a["app.js"]==b["app.js"]
    assert a["index.html"]==b["index.html"]
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
                    assert observed["floor"] == (74274 if route=="candidate" and V3 in mismatched else 80846) and observed["chair"] == 31484
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
