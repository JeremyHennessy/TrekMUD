#!/usr/bin/env python3
"""Compare actually rendered USS Asteria command-platform GLB in Chromium.

Read-only software-WebGL verification against original V5 chair control. The
game collision and stage routes are not changed in this test. File names are
generated from actual browser screenshot pixels, never synthetic images.
"""
from __future__ import annotations
import functools,http.server,json,os,shutil,sys,threading
from pathlib import Path

import numpy as np
from PIL import Image,ImageStat
from playwright.sync_api import sync_playwright

source=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve()
out.mkdir(parents=True,exist_ok=True)
control="3d-preview-v5-chair"
candidate="3d-preview-v5-command"
for route in (control,candidate):
    assert (source/route/"index.html").is_file(),route

server=http.server.ThreadingHTTPServer(("127.0.0.1",0),
  functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(source)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_port}"
shots=[
    (candidate,"aft",1280,800),
    (candidate,"command",1280,800),
    (candidate,"commandDetail",1280,800),
    (candidate,"chairReview",1280,800),
    (candidate,"science",1280,800),
    (candidate,"flight",1280,800),
    (candidate,"aft",390,844),
    (candidate,"command",390,844),
    (control,"aft",1280,800),
    (control,"command",1280,800),
    (control,"flight",1280,800),
]
observed=[]
try:
 with sync_playwright() as playwright:
    executable=os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    if not executable:raise RuntimeError("Chromium required for real WebGL")
    browser=playwright.chromium.launch(executable_path=executable,headless=True,
        args=["--no-sandbox","--disable-dev-shm-usage","--enable-webgl",
              "--use-gl=angle","--use-angle=swiftshader",
              "--enable-unsafe-swiftshader"])
    for route,view,width,height in shots:
      page=browser.new_page(viewport={"width":width,"height":height},
                             device_scale_factor=1,has_touch=width<500)
      errors=[];requests=[]
      page.on("pageerror",lambda e:errors.append(str(e)))
      page.on("response",lambda response:errors.append(f"HTTP_{response.status} {response.url}")
              if response.status>=400 else None)
      page.on("request",lambda req:requests.append(req.url))
      response=page.goto(f"{origin}/{route}/?studioCapture={view}",
                        wait_until="domcontentloaded",timeout=60000)
      assert response and response.status==200
      page.wait_for_function(
        "document.body.dataset.rendererReady === 'true' || document.body.dataset.rendererReady === 'error'",
        timeout=120000)
      state=page.evaluate("""() => ({
        ready:document.body.dataset.rendererReady,
        heroFaces:Number(document.body.dataset.heroChairFaces),
        removedChair:Number(document.body.dataset.captainChairFacesRemoved),
        removedCommand:Number(document.body.dataset.commandFacesRemoved),
        commandFaces:Number(document.body.dataset.commandMeshFaces),
        commandMeshes:Number(document.body.dataset.commandMeshes),
        commandBakedAO:Number(document.body.dataset.commandBakedAoMaterials),
        originalGeometry:Number(document.body.dataset.geometryTriangles),
        missingMaterials:document.body.dataset.missingMaterials,
        originalSource:window.__asteriaV5?.sourceV3Sha,
        changesCampaign:window.__asteriaV5?.changesCampaign,
        sourceSegments:window.__asteriaCommandReview?.originalRanges || [],
        frames:Number(document.body.dataset.renderedFrames||0),
        errorText:document.getElementById('error')?.textContent || ''
      })""")
      assert state["ready"]=="true" and not state["errorText"],(route,view,state)
      assert state["heroFaces"]==31484
      assert state["removedChair"]==16272
      assert state["missingMaterials"]=="0"
      assert state["originalSource"]=="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
      assert state["changesCampaign"] is False
      if route==candidate:
        assert state["originalGeometry"]==82088,state
        if width<500:
          overlap=page.evaluate("""() => {
            const a=document.getElementById('topTitle').getBoundingClientRect();
            const b=document.getElementById('panel').getBoundingClientRect();
            return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                   Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
          }""")
          assert overlap==0,('Approved mobile title/minimap fix regressed',overlap)
        assert state["removedCommand"]==8628,state
        assert state["commandFaces"]==16292,state
        assert state["commandMeshes"]>=40,state
        assert state["commandBakedAO"]>=1,("UV1 Cycles AO missing from live PBR",state)
        assert [s["faces"] for s in state["sourceSegments"]]==[1784,6428,416]
      else:
        assert state["originalGeometry"]==90716,state
      assert not errors,errors
      assert all(url.startswith(origin) for url in requests if url.startswith("http"))
      asset_urls=[req for req in requests if req.endswith(".glb")]
      assert len(set(asset_urls))==(3 if route==candidate else 2),asset_urls
      page.wait_for_function("Number(document.body.dataset.renderedFrames||0)>=2",timeout=90000)
      filename=f"{route}-{view}-{width}x{height}.png"
      page.screenshot(path=str(out/filename),timeout=60000)
      pixels=np.array(Image.open(out/filename).convert("RGB"),dtype=np.float32)
      spread=float(pixels.std(axis=(0,1)).mean())
      assert spread>20,(filename,spread)
      item={"route":route,"view":view,"size":[width,height],
            "screenshot":filename,"pixelStddev":round(spread,3),
            "browser":state,"jsErrors":errors,"assetRequests":asset_urls}
      observed.append(item)
      print("SCENE_RENDER_OK",json.dumps(item),flush=True)
      page.close()
    def pixels(r,v):
      return np.asarray(Image.open(out/f"{r}-{v}-1280x800.png").convert("RGB"),dtype=np.int16)
    differences={}
    for view in ("aft","command"):
      a=pixels(control,view);b=pixels(candidate,view)
      assert a.shape==b.shape
      x=abs(a-b)
      # Source V3 command pylons are center foreground. The new cast housings
      # should make a visually measurable difference from identical waypoints.
      area=(slice(130,650),slice(300,980))
      delta=float(x[area].mean())
      differences[view]=round(delta,4)
      assert delta>.7,(view,delta,"Command model changes too few rendered pixels")
      print("MATCHED_COMMAND_SECTION_VISUAL_DIFFERENCE",view,delta,flush=True)
    # Run actual key presses and wait for rendered frames, not only wall time.
    page=browser.new_page(viewport={"width":860,"height":560})
    page.goto(f"{origin}/{candidate}/?studioCapture=aft",
             wait_until="domcontentloaded",timeout=60000)
    page.wait_for_function("document.body.dataset.rendererReady==='true'",timeout=120000)
    position=page.evaluate("window.__asteriaV5.getPosition()")
    n=page.evaluate("Number(document.body.dataset.renderedFrames||0)")
    page.keyboard.down("w")
    try:
      page.wait_for_function(
        "(n) => Number(document.body.dataset.renderedFrames||0)>=n+2",
        arg=n,timeout=90000)
    finally:
      page.keyboard.up("w")
    moved=page.evaluate("window.__asteriaV5.getPosition()")
    assert abs(moved["x"]-position["x"])+abs(moved["z"]-position["z"])>.025,(position,moved)
    page.locator('[data-go="command"]').click()
    target=page.evaluate("window.__asteriaV5.getPosition()")
    assert abs(target["x"]+2.32)<.01 and abs(target["z"]-2.15)<.01,target
    print("ACTUAL_KEYBOARD_NAVIGATION",json.dumps({"before":position,"after":moved,"station":target}),flush=True)
    page.close()
    phone=browser.new_page(viewport={"width":390,"height":844},has_touch=True)
    phone.goto(f"{origin}/{candidate}/?studioCapture=aft",
               wait_until="domcontentloaded",timeout=60000)
    phone.wait_for_function("document.body.dataset.rendererReady==='true'",timeout=120000)
    phone.locator('[data-go="flight"]').click()
    flight=phone.evaluate("window.__asteriaV5.getPosition()")
    assert abs(flight["z"]+1.32)<.01,flight
    print("ACTUAL_PHONE_VIEWPORT_STATION_CLICK",flight,flush=True)
    phone.close();browser.close()
finally:
 server.shutdown()

report={
 "sourceV3Blob":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
 "sourceRoomId":"AST-D01-BRIDGE",
 "retainedV3Triangles":82088,
 "removedCommandTriangles":8628,
 "removedChairTriangles":16272,
 "newCommandTriangles":16292,
 "newChairTriangles":31484,
 "screenshots":observed,
 "matchedViewDifferences":differences,
 "testScope":"Real Chromium software-WebGL and navigation, no production changes",
 "artApproved":False,
 "limitations":["Photorealism not proven by a passing render",
                "Physical mobile GPU performance not tested"]
}
(out/"command-browser-results.json").write_text(json.dumps(report,indent=2)+"\n")
print("COMMAND_BROWSER_SCREENSHOT_VERIFICATION_PASSED",len(observed),flush=True)
