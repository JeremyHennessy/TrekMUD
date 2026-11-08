#!/usr/bin/env python3
"""Read-only MOBILE-HUD CSS A/B on the live Asteria browser page.

The proposed change is injected into a Playwright page only, never deployed.
Capture actual public site pixels before/after with identical 3D camera,
and prove the title no longer collides with the map on narrow viewports.
"""
from __future__ import annotations
import json,shutil,sys
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

LIVE="https://jeremyhennessy.github.io/TrekMUD/3d-preview-v5-chair/?studioCapture=aft"
CSS="""@media (max-width:760px) {
  #topTitle { width:calc(100vw - 194px); max-width:210px; }
  #topTitle small { display:block; max-width:100%;
    white-space:normal; letter-spacing:.12em; line-height:1.4; font-size:8px; }
  #topTitle h1 { margin-top:7px; font-size:25px; }
}"""

def rects(page):
    return page.evaluate("""() => {
      const r1=document.getElementById('topTitle').getBoundingClientRect();
      const r2=document.getElementById('panel').getBoundingClientRect();
      const intersection=Math.max(0,Math.min(r1.right,r2.right)-Math.max(r1.left,r2.left)) *
                         Math.max(0,Math.min(r1.bottom,r2.bottom)-Math.max(r1.top,r2.top));
      return {
        title:{x:r1.x,y:r1.y,w:r1.width,h:r1.height},
        minimapPanel:{x:r2.x,y:r2.y,w:r2.width,h:r2.height},
        intersectionArea:intersection,
        screen:{w:innerWidth,h:innerHeight}
      };
    }""")

def main():
    output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=True)
    report=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=shutil.which("google-chrome"),
          headless=True,args=["--no-sandbox","--disable-dev-shm-usage",
              "--enable-webgl","--use-gl=angle","--use-angle=swiftshader",
              "--enable-unsafe-swiftshader"])
        for width,height in ((390,844),(375,812)):
            page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1)
            errors=[]
            page.on("pageerror",lambda err:errors.append(str(err)))
            page.goto(LIVE,wait_until="domcontentloaded",timeout=60000)
            page.wait_for_function(
                "document.body.dataset.rendererReady==='true'",timeout=120000)
            page.wait_for_function(
                "Number(document.body.dataset.renderedFrames||0)>=2",timeout=90000)
            original=rects(page)
            original_img=output/f"mobile-{width}-original.png"
            page.screenshot(path=str(original_img),timeout=60000)
            page.add_style_tag(content=CSS)
            fixed=rects(page)
            trial_img=output/f"mobile-{width}-css-trial.png"
            page.screenshot(path=str(trial_img),timeout=60000)
            assert original['intersectionArea']>0,original
            assert fixed['intersectionArea']==0,fixed
            assert fixed["title"]["w"]<=210,fixed
            assert original['title']['x']==fixed['title']['x']
            assert original['minimapPanel']==fixed['minimapPanel']
            assert not errors,errors
            before=Image.open(original_img).convert("RGB")
            after=Image.open(trial_img).convert("RGB")
            assert before.size==after.size==(width,height)
            # Intentional change in top UI area; actual rendering exists in both.
            delta=ImageChops.difference(before.crop((0,0,width,210)),
                                         after.crop((0,0,width,210)))
            assert delta.getbbox() is not None
            row={"width":width,"height":height,"before":original,"after":fixed,
                 "originalScreenshot":original_img.name,
                 "candidateScreenshot":trial_img.name,"pageErrors":errors}
            report.append(row)
            print("MOBILE_HUD_AB_PASS",json.dumps(row),flush=True)
            page.close()
        browser.close()
    (output/"mobile-hud-ab.json").write_text(json.dumps({
        "cssChange":CSS,"sourceUrl":LIVE,"screenshots":report,
        "liveSiteUnmodified":True,"approved":False},indent=2)+"\n")
    print("LIVE_MOBILE_CSS_COLLISION_FIXED_IN_TEST",len(report),flush=True)

if __name__=="__main__":main()
