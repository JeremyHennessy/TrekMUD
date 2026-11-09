#!/usr/bin/env python3
"""Independent hosted USS Asteria Stage28 Pages QA (real Chromium SwiftShader).

Run ONLY after Pages deploy. Does not publish or change any source files.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request
from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_stage28_public_qa"
URL = "https://jeremyhennessy.github.io/TrekMUD/3d-preview-v5-stage28-review/"
OLD_BASE = "https://jeremyhennessy.github.io/TrekMUD/"
SHA = "ef7078dca29ddf5a89b83aac10bee1afbfa7672c"
FROZEN = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"


def remote(relative: str) -> bytes:
    req = urllib.request.Request(
        OLD_BASE + relative,
        headers={"User-Agent": "USS-Asteria-Independent-Live-Review-20261109"})
    with urllib.request.urlopen(req, timeout=55) as response:
        assert response.status == 200, (relative, response.status)
        return response.read()


def wait_for_live_manifest() -> dict:
    last = None
    for attempt in range(1, 16):
        try:
            data = json.loads(remote("3d-preview-v5-stage28-review/review-manifest.json"))
            assert data["art_source"] == SHA
            assert data["base_original_faces"] == 81050
            assert data["envelope_faces"] == 27368
            assert data["owner_visual_approval"] is False
            return data
        except Exception as exc:
            last = exc
            print("STAGE28_CDN_NOT_YET_READY", attempt, str(exc), flush=True)
            if attempt < 15:
                time.sleep(12)
    raise AssertionError(f"New live Pages route not verified: {last}")


def verify_old_published_assets() -> dict:
    immutable = json.loads(
        (ROOT / "docs/asteria-pages-published-sha256-20261108.json").read_text()
    )["original_files"]
    names = [
        "index.html", "3d-preview-v3/index.html",
        "3d-preview-v4/index.html", "3d-preview-v5-chair/index.html",
        "3d-preview-v5-chair/app.js",
        "3d-preview-v5-command/index.html",
        "3d-preview-v5-command/app.js",
        "3d-preview-v5-three-bays/index.html",
        "3d-preview-v5-three-bays/app.js",
        "3d-preview-v5-three-bays/models/asteria-hero-chair-candidate.glb",
        "3d-preview-v5-three-bays/models/asteria-command-set-candidate.glb",
        "3d-preview-v5-three-bays/models/asteria-three-original-pitch-rib-bays-04.glb",
    ]
    result = {}
    for item in names:
        actual = hashlib.sha256(remote(item)).hexdigest()
        assert actual == immutable[item], ("Protected published route changed", item, actual)
        result[item] = actual
        print("PUBLIC_OLD_ROUTE_SHA256_IDENTICAL", item, flush=True)
    return result


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    meta = wait_for_live_manifest()
    protected_hashes = verify_old_published_assets()
    views = [
        ("command", 1280, 800),
        ("command", 390, 844),
        ("envelopeCeiling", 1280, 800),
        ("envelopeWall", 1280, 800),
    ]
    rows = []
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    assert chrome, "Actual Chromium binary is required, not a simulated renderer"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, headless=True, args=[
            "--no-sandbox", "--disable-dev-shm-usage", "--enable-webgl",
            "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"
        ])
        for view, width, height in views:
            page = browser.new_page(viewport={"width": width, "height": height},
                has_touch=width < 500, device_scale_factor=1)
            errors, asset_requests = [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda r: errors.append(
                f"HTTP_{r.status}: {r.url}") if r.status >= 400 else None)
            page.on("request", lambda r: asset_requests.append(r.url))
            response = page.goto(URL + "?studioCapture=" + view,
                wait_until="domcontentloaded", timeout=60000)
            assert response is not None and response.status == 200
            page.wait_for_function(
                "document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",
                timeout=120000)
            page.wait_for_function(
                "document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",
                timeout=180000)
            page.wait_for_function(
                "document.body.dataset.threeBayLoaded==='true'||document.body.dataset.rendererReady==='error'",
                timeout=120000)
            page.wait_for_function(
                "Number(document.body.dataset.renderedFrames||0)>=4", timeout=90000)
            state = page.evaluate("""() => ({
                ready:document.body.dataset.rendererReady,
                error:document.getElementById('error')?.textContent||'',
                room:window.__asteriaV5?.roomId,
                source:window.__asteriaV5?.sourceV3Sha,
                gameWrites:window.__asteriaV5?.changesCampaign,
                original:Number(document.body.dataset.geometryTriangles),
                chair:Number(document.body.dataset.heroChairFaces),
                command:Number(document.body.dataset.commandMeshFaces),
                threeBay:Number(document.body.dataset.threeBayFaces),
                threeBayMeshes:Number(document.body.dataset.threeBayMeshes),
                envelope:Number(document.body.dataset.envelopeFaces),
                envelopeMeshes:Number(document.body.dataset.envelopeMeshes),
                envelopeAO:Number(document.body.dataset.envelopeAOMaterials),
                envelopeOriginalRemoved:Number(document.body.dataset.envelopeOriginalRemoved),
                frames:Number(document.body.dataset.renderedFrames||0),
                mobileHUDOverlap:(() => {
                    const a=document.getElementById('topTitle').getBoundingClientRect();
                    const b=document.getElementById('panel').getBoundingClientRect();
                    return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                        Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
                })()
            })""")
            assert not errors and not state["error"], (view, state, errors)
            assert state["ready"] == "true" and state["room"] == "AST-D01-BRIDGE"
            assert state["source"] == FROZEN and state["gameWrites"] is False
            assert (state["original"], state["chair"], state["command"]) == (81050, 31484, 16292)
            assert (state["threeBay"], state["threeBayMeshes"]) == (13098, 105)
            assert (state["envelope"], state["envelopeMeshes"], state["envelopeOriginalRemoved"]) == (
                27368, 119, 864)
            assert state["envelopeAO"] >= 2
            assert state["frames"] >= 4
            if width < 500:
                assert state["mobileHUDOverlap"] == 0, state
            glbs = sorted(set(x for x in asset_requests if x.endswith(".glb")))
            assert len(glbs) == 5, (view, glbs)
            screenshot = f"stage28-public-{view}-{width}x{height}.png"
            page.screenshot(path=str(OUTPUT / screenshot), timeout=90000)
            im = Image.open(OUTPUT / screenshot).convert("RGB")
            assert im.size == (width, height)
            assert min(ImageStat.Stat(im).stddev) > 16, (view, im.size)
            rows.append({"camera": view, "viewport": [width, height],
                         "screenshot": screenshot, "runtime": state,
                         "glb_requests": glbs, "page_network_errors": errors})
            print("STAGE28_REAL_HOSTED_CHROMIUM_VERIFIED", screenshot, flush=True)
            page.close()
        browser.close()
    report = {
        "url": URL, "source": SHA, "published_for_owner_review": True,
        "photorealistic": False, "owner_art_approved": False,
        "physical_iphone_gpu_measured": False,
        "actual_hosted_chromium": True,
        "protected_sha256_reverified": protected_hashes,
        "metadata": meta, "screenshots": rows,
    }
    (OUTPUT / "public-stage28-verification.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print("STAGE28_PUBLIC_LIVE_REVIEW_RENDER_AND_GAME_VERIFIED", URL, flush=True)


if __name__ == "__main__":
    main()
