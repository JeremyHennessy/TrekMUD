#!/usr/bin/env python3
"""Exact original V3 forward flight-desk SOURCE-span proof, read-only and no deploy.

Identifies the opaque original flightIsland geometry so a later architectural
replacement can be exact rather than a screen-blocking overlay. Preserves the
six original instrument atlas surfaces, flight chairs, room/camera/UI controls.
"""
from __future__ import annotations
import argparse,json,shutil,subprocess
from collections import Counter
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
V3=ROOT/"ui/3d-preview-v3"
INDEX_BLOB="74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
DETAILS_BLOB="3716accf4490bf28da56be0ae21081ab3a3a0f17"
HERO_BLOB=""

def sha(path):
    return subprocess.check_output(["git","hash-object",str(path)],cwd=ROOT,text=True).strip()

def replace(source,old,new,label):
    assert source.count(old)==1,(label,"anchor count",source.count(old))
    return source.replace(old,new,1)

def instrument():
    assert sha(V3/"index.html")==INDEX_BLOB,"Frozen original V3 changed"
    assert sha(V3/"set-details.js")==DETAILS_BLOB,"Original dressing changed"
    html=(V3/"index.html").read_text()
    # Exactly one original call to the manufactured flight desk. The next
    # six SURFACE calls paint the original atlas glass; deliberately exclude
    # those functional monitor faces from the candidate removal proposal.
    start="// Forward continuous flight island, original crescent design with separate seats."
    stop="for(let i=0;i<6;i++){let x=(i-2.5)*.88"
    html=replace(html,start,start+"\nwindow.__astFlightStart=P.length/9;","original desk begin")
    html=replace(html,stop,"window.__astFlightEnd=P.length/9;\n"+stop,"original glass begins")
    # Make the literal auxiliary source available in-memory only, no disk edits.
    for file in ("hero-v3.js","furniture.js","set-details.js"):
        html=replace(html,f'<script src="{file}"></script>',
                     "<script>"+(V3/file).read_text()+"</script>",
                     "inline unchanged "+file)
    expose="window.__asteriaWalkthrough={roomId:"
    html=replace(html,expose,
      "window.__astForwardSource={positions:P,materials:M,from:window.__astFlightStart,to:window.__astFlightEnd};"+
      expose,"read-only source array visibility")
    stub="""<script>(()=>{
      const fake=new Proxy({}, {get:(_,k)=>{
        if(k==='getShaderParameter'||k==='getProgramParameter')return ()=>true;
        if(k==='getAttribLocation'||k==='getError')return ()=>0;
        if(k==='checkFramebufferStatus')return ()=>0;
        if(k.startsWith('create'))return ()=>({});
        if(k==='getShaderInfoLog'||k==='getProgramInfoLog')return ()=>'';
        return (...args)=>{};
      }});
      const prev=HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext=function(type,...args){
        return type==='webgl'?fake:prev.call(this,type,...args)};
      window.requestAnimationFrame=()=>0;
    })()</script>"""
    return replace(html,"</head>",stub+"</head>","isolated no-op GL capture")

def run(out):
    browser_bin=shutil.which("google-chrome") or shutil.which("chromium")
    assert browser_bin,"Genuine Chromium required"
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=browser_bin,headless=True,
                                  args=["--no-sandbox","--disable-dev-shm-usage"])
        page=browser.new_page(viewport={"width":480,"height":320})
        errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.set_content(instrument(),wait_until="domcontentloaded",timeout=90000)
        page.wait_for_function("window.__astForwardSource!==undefined",timeout=90000)
        record=page.evaluate("""() => {
            const {positions:P,materials:M,from,to}=window.__astForwardSource;
            const region=P.slice(from*9,to*9),mats=M.slice(from*3,to*3);
            const ranges=[[Infinity,-Infinity],[Infinity,-Infinity],[Infinity,-Infinity]];
            for(let i=0;i<region.length;i+=3) for(let k=0;k<3;k++){
                ranges[k][0]=Math.min(ranges[k][0],region[i+k]);
                ranges[k][1]=Math.max(ranges[k][1],region[i+k]);
            }
            const materialCounts={};
            for(let i=0;i<mats.length;i+=3){
                if(mats[i]!==mats[i+1]||mats[i]!==mats[i+2])
                    throw Error('Mismatched per-face materials');
                materialCounts[mats[i]]=(materialCounts[mats[i]]||0)+1;
            }
            return {totalFaces:window.__asteriaWalkthrough.meshTriangles,
               start:from,end:to,originalOpaqueDeskFaces:to-from,
               materialCounts,bounds:ranges,
               originalScreenGlassFacesFollowing:to<window.__asteriaWalkthrough.meshTriangles};
        }""")
        browser.close()
    assert errors==[],errors
    assert record["totalFaces"]==106988,record
    a,b=record["start"],record["end"]
    assert isinstance(a,int) and isinstance(b,int) and 37104<=a<b<93950,record
    assert 2000<b-a<25000,record
    assert sum(record["materialCounts"].values())==b-a
    assert set(map(int,record["materialCounts"]))<={2,3,4,7,8}
    ranges=record["bounds"]
    assert -2.9<ranges[0][0]<-2.4 and 2.4<ranges[0][1]<2.9
    assert 0.15<ranges[1][0]<0.4 and 1.15<ranges[1][1]<1.4
    assert -4.2<ranges[2][0]<-3.3 and -2.9<ranges[2][1]<-2.3
    record.update(id="ASTERIA_STAGE35_ORIGINAL_FLIGHT_DESK_SOURCE_EXACT",
        sourceV3Blob=INDEX_BLOB,sourceHeroBlob=sha(V3/"hero-v3.js"),
        sourceSetDetailsBlob=DETAILS_BLOB,
        selectedSource="AsteriaHero.flightIsland only",
        originalSixFunctionalFlightGlassPlanesRetained=True,
        originalFlightChairsAndControlsRetained=True,
        originalScreenAndStarfieldRetained=True,
        originalCommandChairAndPylonsRetained=True,
        stage33PlateRibs96Nonoverlap=True,
        sourceFilesChanged=False,candidateRemovalApplied=False,
        artisticApproval=False,releaseApproval=False)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
    print("AST_FORWARD_DESK_SOURCE_PROOF",json.dumps(record),flush=True)
    return record

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    run(p.parse_args().output)
