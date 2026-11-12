#!/usr/bin/env python3
"""Read-only actual Chromium QA: eight preset camera angles on desktop and mobile."""
import argparse,functools,hashlib,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright

CAMERAS=("command","commandDetail","flight","science","viewer","aft","chairReview","envelopeCeiling")
DEVICES=(("desktop",1280,800),("mobile",390,844))
GLBS=("asteria-v3-restored-pbr.glb","asteria-hero-chair-candidate.glb",
      "asteria-command-set-candidate.glb","asteria-three-original-pitch-rib-bays-04.glb",
      "asteria-realistic-architectural-envelope-08.glb")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--site",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--chrome",required=True)
    a=ap.parse_args()
    assert (a.site/"app.js").exists() and (a.site/"index.html").exists()
    hashes={k:hashlib.sha256((a.site/"models"/k).read_bytes()).hexdigest() for k in GLBS}
    a.out.mkdir(parents=True,exist_ok=True)
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(a.site)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin="http://127.0.0.1:"+str(server.server_port)
    report={"kind":"ASTERIA_MULTIANGLE_ORIGINAL_CHROMIUM_READONLY",
            "inputGLBSHA256":hashes,"screenshots":[],"completed":False,
            "artApproved":False,"productionChanged":False}
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=a.chrome,headless=True,
                args=["--no-sandbox","--disable-dev-shm-usage","--enable-webgl",
                      "--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
            for device,w,h in DEVICES:
                for camera in CAMERAS:
                    page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1,has_touch=device=="mobile")
                    faults=[];requests=[]
                    page.on("pageerror",lambda e:faults.append("JS "+str(e)))
                    page.on("response",lambda r:faults.append("HTTP "+str(r.status)+" "+r.url) if r.status>=400 else None)
                    page.on("request",lambda r:requests.append(r.url))
                    response=page.goto(origin+"/?studioCapture="+camera,wait_until="domcontentloaded",timeout=60000)
                    assert response and response.status==200
                    page.wait_for_function("document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",timeout=180000)
                    state=page.evaluate("""() => ({ready:document.body.dataset.rendererReady,
                        error:document.getElementById('error')?.textContent||'',
                        envelope:document.body.dataset.envelopeLoaded,
                        threeBay:document.body.dataset.threeBayLoaded,
                        frames:Number(document.body.dataset.renderedFrames||0),
                        room:window.__asteriaV5?.roomId,
                        source:window.__asteriaV5?.sourceV3Sha,
                        writes:window.__asteriaV5?.changesCampaign})""")
                    if state["ready"]=="true":
                        page.wait_for_function("Number(document.body.dataset.renderedFrames||0)>=4",timeout=90000)
                        state["frames"]=page.evaluate("Number(document.body.dataset.renderedFrames||0)")
                    file=f"{device}-{camera}-{w}x{h}.png"
                    page.screenshot(path=str(a.out/file),timeout=60000)
                    glbs=sorted({u.split("?")[0].split("/")[-1] for u in requests if ".glb" in u})
                    item={"camera":camera,"device":device,"size":[w,h],"file":file,
                          "renderer":state,"glbRequests":glbs,"errors":faults}
                    report["screenshots"].append(item)
                    assert state["ready"]=="true" and not state["error"],item
                    assert state["room"]=="AST-D01-BRIDGE" and state["writes"] is False,item
                    assert state["frames"]>=4 and state["envelope"]==state["threeBay"]=="true",item
                    assert not faults and set(GLBS).issubset(glbs),item
                    page.close()
            browser.close()
            report["completed"]=True
    finally:
        server.shutdown()
        (a.out/"multiangle-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MULTIANGLE_REAL_BROWSER_SCREENS",len(report["screenshots"]),"PASS",report["completed"])
if __name__=="__main__":main()
