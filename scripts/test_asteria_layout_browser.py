#!/usr/bin/env python3
"""Browser smoke for the isolated USS Asteria layout study (no gameplay state)."""
from pathlib import Path
import json, os, sys
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
url = (root / "3d-layout" / "index.html").as_uri()
chrome = os.environ.get("CHROME") or "/usr/bin/google-chrome"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome, headless=True, args=[
        "--no-sandbox", "--disable-dev-shm-usage", "--enable-webgl",
        "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    ])
    page = browser.new_page(viewport={"width": 960, "height": 640}, device_scale_factor=1)
    page_errors = []
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.goto(url + "?capture=aft", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_function('document.body.dataset.viewerReady === "true"', timeout=60000)
    before = page.evaluate('window.__asteriaLayout.getPosition()')
    frames_before = page.evaluate('window.__asteriaLayout.frames()')
    page.keyboard.down("w")
    page.wait_for_timeout(1650)
    page.keyboard.up("w")
    after = page.evaluate('window.__asteriaLayout.getPosition()')
    frames_after = page.evaluate('window.__asteriaLayout.frames()')
    delta = abs(before["x"]-after["x"])+abs(before["z"]-after["z"])
    assert frames_after > frames_before, "No new rendered frames after moving"
    assert delta > .07, f"W key produced no movement: {before} -> {after}"
    page.locator('[data-view="science"]').click()
    science = page.evaluate('window.__asteriaLayout.getPosition()')
    assert abs(science["x"]-3.65) < .02, f"Science station jump failed: {science}"
    page.keyboard.press("r")
    reset = page.evaluate('window.__asteriaLayout.getPosition()')
    assert abs(reset["z"]-4.75) < .02, f"R reset failed: {reset}"
    assert not page_errors, f"Page JavaScript errors: {page_errors}"
    print(json.dumps({"result": "success", "roomId": "AST-D01-BRIDGE", "before": before,
        "after": after, "distanceMoved": round(delta, 3), "scienceJump": science,
        "reset": reset, "renderedFrames": frames_after, "pageErrors": page_errors}, indent=2))
    page.close()
    touch = browser.new_page(viewport={"width":390,"height":844},has_touch=True,is_mobile=True)
    touch.goto(url,wait_until="domcontentloaded",timeout=30000)
    touch.wait_for_function('document.body.dataset.viewerReady === "true"',timeout=60000)
    assert not touch.locator('#joy').get_attribute('hidden'), "Touch joystick missing"
    touch.close()
    browser.close()