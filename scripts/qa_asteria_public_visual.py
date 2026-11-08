#!/usr/bin/env python3
"""Read-only live visual QA for the PUBLIC USS Asteria chair bridge.

Collect actual browser screenshots and inspectable per-view metadata. Never
rewrite site assets or confuse a successful HTTP request with a rendered scene.
This uses software WebGL in CI; it does not represent physical iPhone FPS.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps, ImageStat
from playwright.sync_api import sync_playwright

SOURCE_V3 = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
LIVE_URL = "https://jeremyhennessy.github.io/TrekMUD/3d-preview-v5-chair/"

# HUD-inclusive and clean views deliberately test different UI states.
SHOTS = [
    ("aft", 1280, 800, True),
    ("aft", 1280, 800, False),
    ("chairReview", 1280, 800, False),
    ("command", 1280, 800, False),
    ("science", 1280, 800, False),
    ("flight", 1280, 800, False),
    ("viewer", 1280, 800, False),
    ("aft", 390, 844, True),
    ("chairReview", 390, 844, False),
    ("command", 390, 844, True),
]

def photo_metrics(path: Path):
    with Image.open(path) as im:
        image = im.convert("RGB")
        stat = ImageStat.Stat(image)
        levels = image.convert("L").histogram()
        count = image.width * image.height
        return {
            "resolution": [image.width, image.height],
            "meanRgb": [round(x, 2) for x in stat.mean],
            "stdRgb": [round(x, 2) for x in stat.stddev],
            "darkFraction": round(sum(levels[:20]) / count, 4),
            "brightFraction": round(sum(levels[245:]) / count, 4),
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--url", default=LIVE_URL)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as playwright:
        chrome = shutil.which("google-chrome") or shutil.which("chromium")
        if not chrome:
            raise RuntimeError("A real Chromium executable must be available.")
        browser = playwright.chromium.launch(
            executable_path=chrome,
            headless=True,
            args=[
                "--no-sandbox", "--disable-dev-shm-usage", "--enable-webgl",
                "--use-gl=angle", "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ],
        )
        for view, width, height, hud in SHOTS:
            label = "hud" if hud else "clean"
            filename = f"live-{view}-{width}x{height}-{label}.png"
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
                has_touch=width < 500,
            )
            errors = []
            network_errors = []
            requests = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda response: network_errors.append(
                {"status": response.status, "url": response.url}
            ) if response.status >= 400 else None)
            page.on("requestfinished", lambda request: requests.append(request.url))
            url = args.url + "?studioCapture=" + view
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
                if response is None or response.status != 200:
                    raise RuntimeError(f"Page unavailable: {url}")
                page.wait_for_function(
                    """() => document.body.dataset.rendererReady === 'true'
                           || document.body.dataset.rendererReady === 'error'""",
                    timeout=120000,
                )
                data = page.evaluate("""() => ({
                  ready: document.body.dataset.rendererReady,
                  source: window.__asteriaV5?.sourceV3Sha,
                  heroFaces: Number(document.body.dataset.heroChairFaces),
                  removedFaces: Number(document.body.dataset.captainChairFacesRemoved),
                  retainedFaces: Number(document.body.dataset.geometryTriangles),
                  missingMaterials: document.body.dataset.missingMaterials,
                  frames: Number(document.body.dataset.renderedFrames || 0),
                  changesCampaign: window.__asteriaV5?.changesCampaign,
                  sceneVersion: document.body.dataset.sceneVersion,
                  splashHidden: document.getElementById('splash')?.classList.contains('off'),
                  errorText: document.getElementById('error')?.textContent || '',
                  canvas: (() => {const r=document.getElementById('scene').getBoundingClientRect();
                                  return {w:r.width,h:r.height}})()
                })""")
                assert data["ready"] == "true", data
                assert data["source"] == SOURCE_V3, data
                assert data["heroFaces"] == 31484, data
                assert data["removedFaces"] == 16272, data
                assert data["retainedFaces"] == 90716, data
                assert data["missingMaterials"] == "0", data
                assert data["changesCampaign"] is False, data
                assert data["splashHidden"] is True, data
                assert not data["errorText"], data
                assert abs(data["canvas"]["w"] - width) < 2, data
                assert abs(data["canvas"]["h"] - height) < 2, data
                # Two actual rendered frames before judging pixel content.
                page.wait_for_function(
                    """() => Number(document.body.dataset.renderedFrames || 0) >= 2""",
                    timeout=90000,
                )
                if not hud:
                    page.locator("#hide").click(timeout=30000)
                    assert page.locator("body").evaluate(
                        "(el) => el.classList.contains('hideHud')"
                    )
                page.screenshot(path=str(out / filename), timeout=90000)
                metrics = photo_metrics(out / filename)
                assert min(metrics["stdRgb"]) > 18, (filename, metrics)
                assert metrics["darkFraction"] < 0.88, (filename, metrics)
                assert not errors and not network_errors, (
                    filename, errors, network_errors
                )
                assets = [s for s in requests if s.endswith(".glb")]
                assert len(set(assets)) == 2, assets
                row = {
                    "view": view,
                    "size": [width, height],
                    "hudVisible": hud,
                    "filename": filename,
                    "renderedFrameCount": page.evaluate(
                        "Number(document.body.dataset.renderedFrames || 0)"
                    ),
                    "runtime": data,
                    "image": metrics,
                    "assetResponses": assets,
                    "pageErrors": errors,
                    "networkErrors": network_errors,
                    "verified": True,
                }
                print("SCREENSHOT_PASS", json.dumps({
                    "filename": filename,
                    "std": metrics["stdRgb"],
                    "dark": metrics["darkFraction"],
                    "frames": row["renderedFrameCount"],
                }), flush=True)
                records.append(row)
            finally:
                page.close()
        browser.close()

    # Assemble a convenient actual-pixel contact sheet, not a simulated render.
    cols, rows = 2, (len(records) + 1) // 2
    cell_w, cell_h = 650, 420
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (23, 25, 32))
    draw = ImageDraw.Draw(sheet)
    for n, item in enumerate(records):
        x0 = (n % cols) * cell_w
        y0 = (n // cols) * cell_h
        source = Image.open(out / item["filename"]).convert("RGB")
        thumb = ImageOps.contain(source, (610, 365), method=Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x0 + (cell_w-thumb.width)//2, y0+12))
        draw.text((x0+18, y0+383),
                  f"{item['view']} | {item['size'][0]}x{item['size'][1]} | "
                  f"{'HUD' if item['hudVisible'] else 'clean'}",
                  fill=(238, 230, 218))
    sheet.save(out / "asteria-live-contact-sheet.jpg", quality=88, optimize=True)

    report = {
        "sourceUrl": args.url,
        "liveSiteOnly": True,
        "screenshotCount": len(records),
        "referenceV3Source": SOURCE_V3,
        "testsPassed": True,
        "screenshots": records,
        "limitations": [
            "Software-WebGL CI screenshot quality is not physical iPhone FPS.",
            "No model quality or user artistic approval is implied.",
            "Screenshots are from real live page pixels, not image-generation previews."
        ],
    }
    (out / "visual-qa.json").write_text(json.dumps(report, indent=2) + "\n")
    assert len(records) == len(SHOTS)
    print("VISUAL_SCREENSHOT_AUDIT_PASS", len(records), flush=True)

if __name__ == "__main__":
    main()
