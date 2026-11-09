#!/usr/bin/env python3
"""Stage20 3 physical wall/soffit/plinth bays versus frozen Stage12 cameras.

Original Stage04 source three-bay control (81,914 source triangles) against same
exact model with 864 further original wall and roof faces removed, retaining
81,050 original source faces plus a scan-textured, Cycles AO authored envelope.
No modifications to camera, approved UI, game or collision; view only.
"""
from __future__ import annotations
import functools,http.server,hashlib,json,os,shutil,sys,threading
from pathlib import Path
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

root=Path(sys.argv[1]).resolve()
out=Path(sys.argv[2]).resolve()
out.mkdir(parents=True,exist_ok=True)
control="3d-preview-v5-command-three-bays"
candidate="3d-preview-v5-command-envelope"
for item in (control,candidate):
    assert (root/item/"index.html").is_file(),item

server=http.server.ThreadingHTTPServer(("127.0.0.1",0),
    functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f"http://127.0.0.1:{server.server_port}"
shots=[("aft",1280,800),("command",1280,800),("science",1280,800),
       ("envelopeWall",1280,800),("envelopeCeiling",1280,800),("aft",390,844),("command",390,844)]
metadata=json.loads((root/candidate/"models/envelope-manifest.json").read_text())
expected_envelope_faces=int(metadata["newEnvelopeTriangles"])
assert 1000<expected_envelope_faces<50000
items=[]
try:
 with sync_playwright() as playwright:
    chrome=os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:raise RuntimeError("Actual Chromium executable is required")
    browser=playwright.chromium.launch(executable_path=chrome,headless=True,
        args=["--no-sandbox","--disable-dev-shm-usage","--enable-webgl",
              "--use-gl=angle","--use-angle=swiftshader",
              "--enable-unsafe-swiftshader"])
    for view,width,height in shots:
      for route in (control,candidate):
        page=browser.new_page(viewport={"width":width,"height":height},
                              device_scale_factor=1,has_touch=width<500)
        errors=[];requests=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("response",lambda r:errors.append(f"HTTP_{r.status}: {r.url}")
                if r.status>=400 else None)
        page.on("request",lambda req:requests.append(req.url))
        resp=page.goto(f"{origin}/{route}/?studioCapture={view}",
                       wait_until="domcontentloaded",timeout=60000)
        assert resp and resp.status==200
        page.wait_for_function(
          "document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",
          timeout=120000)
        if route in (control,candidate):
          page.wait_for_function(
            "document.body.dataset.threeBayLoaded==='true'||document.body.dataset.rendererReady==='error'",
            timeout=120000)
        if route==candidate:
          page.wait_for_function("document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",
                                 timeout=180000)
        page.wait_for_function("Number(document.body.dataset.renderedFrames||0)>=4",timeout=90000)
        obs=page.evaluate("""() => ({
          ready:document.body.dataset.rendererReady,
          error:document.getElementById('error')?.textContent||'',
          room:window.__asteriaV5?.roomId,
          sourceV3:window.__asteriaV5?.sourceV3Sha,
          writes:window.__asteriaV5?.changesCampaign,
          originalFaces:Number(document.body.dataset.geometryTriangles),
          chairFaces:Number(document.body.dataset.heroChairFaces),
          removedCaptain:Number(document.body.dataset.captainChairFacesRemoved),
          removedCommand:Number(document.body.dataset.commandFacesRemoved),
          commandFaces:Number(document.body.dataset.commandMeshFaces),
          commandAO:Number(document.body.dataset.commandBakedAoMaterials),
          threeBayLoaded:document.body.dataset.threeBayLoaded||'none',
          threeBayFaces:Number(document.body.dataset.threeBayFaces||0),
          threeBayMeshes:Number(document.body.dataset.threeBayMeshes||0),
          envelopeLoaded:document.body.dataset.envelopeLoaded||'none',
          envelopeFaces:Number(document.body.dataset.envelopeFaces||0),
          envelopeMeshes:Number(document.body.dataset.envelopeMeshes||0),
          envelopeAOMaterials:Number(document.body.dataset.envelopeAOMaterials||0),
          envelopeOriginalRemoved:Number(document.body.dataset.envelopeOriginalRemoved||0),
          sourceExclusions:window.__asteriaThreeBayReview?.excludedOriginalFaces??0,
          renderedFrames:Number(document.body.dataset.renderedFrames||0)
        })""")
        assert obs["ready"]=="true" and not obs["error"],(route,obs)
        assert obs["room"]=="AST-D01-BRIDGE"
        assert obs["sourceV3"]=="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
        assert obs["writes"] is False
        assert obs["chairFaces"]==31484 and obs["removedCaptain"]==16272
        assert obs["removedCommand"]==8628 and obs["commandFaces"]==16292
        assert obs["commandAO"]>=1
        assert obs["threeBayLoaded"]=="true",obs
        assert obs["threeBayFaces"]==13098 and obs["threeBayMeshes"]==105,obs
        assert obs["sourceExclusions"]==174,obs
        if route==candidate:
          assert obs["originalFaces"]==81050,obs
          assert obs["envelopeLoaded"]=="true",obs
          assert obs["envelopeFaces"]==expected_envelope_faces,obs
          assert obs["envelopeMeshes"]==52 and obs["envelopeAOMaterials"]>=2,obs
          assert obs["envelopeOriginalRemoved"]==864,obs
        else:
          assert obs["originalFaces"]==81914,obs
          assert obs["envelopeLoaded"]=="none",obs
        if width<500:
          overlap=page.evaluate("""() => {
            const a=document.getElementById('topTitle').getBoundingClientRect();
            const b=document.getElementById('panel').getBoundingClientRect();
            return Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)) *
                   Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
          }""")
          assert overlap==0,(route,overlap)
        assert not errors,(route,errors)
        assert all(u.startswith(origin) for u in requests if u.startswith("http"))
        glbs=set(u for u in requests if u.endswith(".glb"))
        assert len(glbs)==(5 if route==candidate else 4),(route,glbs)
        file=f"{route}-{view}-{width}x{height}.png"
        page.screenshot(path=str(out/file),timeout=60000)
        pixels=np.asarray(Image.open(out/file).convert("RGB"))
        assert pixels.std(axis=(0,1)).mean()>16,(route,view)
        items.append({"route":route,"camera":view,"size":[width,height],
                      "screenshot":file,"observation":obs,"assetRequests":sorted(glbs),
                      "pageErrors":errors})
        print("BROWSER_SCENE_LOADED",file,json.dumps(obs),flush=True)
        page.close()
    comparisons={}
    for view,width,height in shots:
      a=np.asarray(Image.open(out/f"{control}-{view}-{width}x{height}.png").convert("RGB"),
                   dtype=np.int16)
      b=np.asarray(Image.open(out/f"{candidate}-{view}-{width}x{height}.png").convert("RGB"),
                   dtype=np.int16)
      delta=np.abs(a-b)
      mean=float(delta.mean())
      frac=float((delta.max(axis=2)>10).mean())
      comparisons[f"{view}/{width}"]={"meanAbsoluteRgb":round(mean,5),
                                     "changedPixelFraction":round(frac,6)}
      print("SOURCE_REPLACEMENT_VISUAL_DELTA",view,width,round(mean,5),round(frac,6))
    # Compare against independent, immutable Stage12 screenshot ZIP from
    # completed real browser workflow run 42524417159 / artifact 13634679552.
    # Stage12 already omits all protruding roof rails; Stage20 adds three
    # broad structural wall-to-ceiling junctions; all player assets retained.
    zone_deltas={}
    stage12=Path("_stage12_reference/_stage08_browser")
    pinned_sha={
      "3d-preview-v5-command-envelope-envelopeCeiling-1280x800.png":"bbcca2e4044698fcb3a09881200b9a8d3bd2454cacd13655c079e45134ede28f",
      "3d-preview-v5-command-envelope-aft-1280x800.png":"33bb54f41021ac37009cb0dc15e7a2462504eb1fbab7bbd4c892af1060f306f0",
      "3d-preview-v5-command-envelope-command-1280x800.png":"f70e4955c06cd22cf063bf403f7b00dc13e8004a8327533c8ddf1c25d0c16b02",
    }
    for name,sha in pinned_sha.items():
      f=stage12/name
      assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==sha,("Altered Stage12 reference",str(f))
    for view,width,height in shots:
      name=f"{candidate}-{view}-{width}x{height}.png"
      baseline=stage12/name
      assert baseline.is_file(),("Missing pinned Stage12 screenshot",str(baseline))
      baseline_rgb=Image.open(baseline).convert("RGB")
      candidate_rgb=Image.open(out/name).convert("RGB")
      assert baseline_rgb.size==candidate_rgb.size==(width,height)
      a=np.asarray(baseline_rgb,dtype=np.int16)
      b=np.asarray(candidate_rgb,dtype=np.int16)
      diff=np.abs(a-b)
      zone_deltas[f"{view}/{width}"]={
          "meanAbsoluteRgb":round(float(diff.mean()),5),
          "changedPixelFractionOver10":round(float((diff.max(axis=2)>10).mean()),6)}
      if width==1280 and view in ("aft","command","envelopeCeiling","envelopeWall"):
        ab=Image.new("RGB",(width*2,height))
        ab.paste(baseline_rgb,(0,0))
        ab.paste(candidate_rgb,(width,0))
        ab.save(out/f"stage12-vs-manufactured-zone20-{view}-ab.jpg",quality=89)
      print("STAGE12_VS_MANUFACTURED_ZONE20",view,width,json.dumps(zone_deltas[f"{view}/{width}"]),flush=True)
    # Stage20 must visibly affect the intended near-wall camera. This floor
    # does NOT establish artistic acceptance, which requires inspected pixels.
    assert zone_deltas["envelopeWall/1280"]["changedPixelFractionOver10"]>.035,zone_deltas["envelopeWall/1280"]
    # Walking and waypoints in candidate only. Do not modify source controls.
    page=browser.new_page(viewport={"width":860,"height":560})
    page.goto(f"{origin}/{candidate}/?studioCapture=aft",wait_until="domcontentloaded")
    page.wait_for_function("document.body.dataset.envelopeLoaded==='true'",timeout=180000)
    before=page.evaluate("window.__asteriaV5.getPosition()")
    n=page.evaluate("Number(document.body.dataset.renderedFrames||0)")
    page.keyboard.down("w")
    try:
      page.wait_for_function("(n) => Number(document.body.dataset.renderedFrames||0)>=n+3",
                             arg=n,timeout=90000)
    finally:page.keyboard.up("w")
    after=page.evaluate("window.__asteriaV5.getPosition()")
    assert abs(after["x"]-before["x"])+abs(after["z"]-before["z"])>.025,(before,after)
    page.locator('[data-go="command"]').click()
    position=page.evaluate("window.__asteriaV5.getPosition()")
    assert abs(position["x"]+2.32)<.01 and abs(position["z"]-2.15)<.01,position
    page.close();browser.close()
finally:
 server.shutdown()

report={
 "review":"QA-only actual software-WebGL comparison, not production",
 "sourceV3":"74a154ae62bccb0c16d03c2ecf791a64ab19ce81",
 "commandAndChairUnchanged":True,"threeBayUnchanged":True,"campaignAndUiUnchanged":True,
 "originalSourceFaceSpansRemoved":864,"originalFacesBefore":81914,
 "originalFacesAfter":81050,"newArchitecturalEnvelopeTriangles":expected_envelope_faces,
 "realScreenshots":items,"matchedDeltas":comparisons,
 "stage12ReferenceCommit":"e5b5a58fbd284fac98e4f1e367a3b9cb0a86811b",
 "stage12ReferenceArtifact":13634679552,
 "onlyGeometryVariable":"three broad manufactured wall/ceiling/plinth bays with inset physical practical lights",
 "stage12VsManufacturedZone20MatchedCameraDeltas":zone_deltas,
 "walkingAndCommandWaypointsPass":True,
 "artApproved":False,"photorealismProven":False,
 "physicalIphoneGpuVerified":False
}
(out/"envelope-browser-report.json").write_text(json.dumps(report,indent=2)+"\n")
print("MANUFACTURED_STAGE20_REAL_BROWSER_A_B_COMPLETE",json.dumps(comparisons),flush=True)
