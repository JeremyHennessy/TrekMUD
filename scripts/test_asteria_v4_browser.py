#!/usr/bin/env python3
"""Live Chromium first-person movement verification (isolated V4, no RPG actions)."""
import functools, http.server, json, shutil, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

site=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('_site').resolve()
assert (site/'3d-preview-v4/index.html').exists()
httpd=http.server.ThreadingHTTPServer(('127.0.0.1',8767),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(site)))
t=threading.Thread(target=httpd.serve_forever,daemon=True);t.start()
try:
    with sync_playwright() as p:
        exe=shutil.which('google-chrome') or shutil.which('chromium')
        assert exe, 'A local Chrome/Chromium installation is required for visual acceptance'
        browser=p.chromium.launch(executable_path=exe,headless=True,args=[
            '--no-sandbox','--disable-dev-shm-usage','--enable-webgl',
            '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':620,'height':520},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8767/3d-preview-v4/?capture=aft',wait_until='domcontentloaded',timeout=45000)
        page.wait_for_function('Boolean(window.__asteriaV4 && document.body.dataset.scene === "loaded")',timeout=60000)
        before=page.evaluate('window.__asteriaV4.getPosition()')
        before_frames=page.evaluate('Number(document.body.dataset.renderedFrames||0)')
        assert page.evaluate('window.__asteriaV4.roomId')=='AST-D01-BRIDGE'
        page.keyboard.down('w')
        page.wait_for_timeout(4500)
        page.keyboard.up('w')
        after=page.evaluate('window.__asteriaV4.getPosition()')
        after_frames=page.evaluate('Number(document.body.dataset.renderedFrames||0)')
        print(json.dumps({'keyboard_before':before,'keyboard_after':after,'frames_before':before_frames,'frames_after':after_frames}),flush=True)
        assert after_frames>before_frames, 'No render frames advanced during keyboard hold'
        assert after['z'] < before['z']-.025, {'before':before,'after':after}
        page.locator('[data-place="command"]').click(timeout=20000)
        command=page.evaluate('window.__asteriaV4.getPosition()')
        assert abs(command['x']+2.48)<.10,command
        assert page.evaluate('window.__asteriaV4.writesCampaign') is False
        assert len(errors)==0,errors
        print(json.dumps({'roomId':'AST-D01-BRIDGE','movementBefore':before,'movementAfter':after,'commandJump':command,'pageErrors':errors,'webgl':page.evaluate('document.body.dataset.webglVersion')},indent=2))
        browser.close()
finally:httpd.shutdown()