#!/usr/bin/env python3
"""Read-only, browser-measured V3 under-command joinery provenance.

Execute the immutable V3 source with IN-MEMORY draw-call markers. Never edit
the original source, the frozen V3 geometry, the game's UI, or production.
This proves exact source face boundaries, not that removing them is approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "ui/3d-preview-v3"
V3_BLOB = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
DETAILS_BLOB = "3716accf4490bf28da56be0ae21081ab3a3a0f17"
TRIANGLES = 106988

def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path)], cwd=ROOT, text=True
    ).strip()

def replace_exact(source: str, old: str, new: str, label: str) -> str:
    assert source.count(old) == 1, (label, source.count(old))
    return source.replace(old, new, 1)

def mark_call(source: str, token: str, region: str) -> str:
    pre = ("window.__astAuditUnder=window.__astAuditUnder||{};"
           "window.__astAuditUnder[s]=window.__astAuditUnder[s]||{};"
           f"window.__astAuditUnder[s]['{region}Start']=api.faceCount();")
    post = f"window.__astAuditUnder[s]['{region}End']=api.faceCount();"
    return replace_exact(source, token, pre + "\n" + token + "\n" + post, region)

def instrument() -> str:
    assert git_blob(V3 / "index.html") == V3_BLOB, "V3 index drift"
    assert git_blob(V3 / "set-details.js") == DETAILS_BLOB, "V3 dressing drift"
    html = (V3 / "index.html").read_text()
    details = (V3 / "set-details.js").read_text()

    # Main-scene command/chair boundaries: independently read from the same
    # literal source calls used by the validated V5 extractor.
    anchors = [
        ("captain", "ellipse(0,.297,1.14,.48,.55,0x554e5e,1,44);",
         "chair(0,1.20,0,true);", True),
        ("platform",
         "if(window.AsteriaHero){window.AsteriaHero.commandPlatform({smoothSurface,box,cyl,ellipse,ring,tube});}",
         "const shadowCasterStart=P.length/3;", False),
        ("pylons",
         "if(window.AsteriaHero){window.AsteriaHero.commandPylons({smoothSurface,box,tube,surface});}",
         "// Forward continuous flight island, original crescent design with separate seats.", False),
        ("trim",
         "// Command plinth joinery: detailed brass edge lugs, inset upholstery seams and foot-level kick plates.",
         "const setDressing=(typeof window.AsteriaSetDetails==='function')?", False),
    ]
    for name, begin, end, end_after in anchors:
        start_code = (
            "window.__astAuditProtected=window.__astAuditProtected||{};"
            f"window.__astAuditProtected['{name}']={{start:P.length/9}};"
        )
        stop_code = f"window.__astAuditProtected['{name}'].end=P.length/9;"
        html = replace_exact(html, begin, start_code + begin, name + " start")
        html = replace_exact(html, end, end + stop_code if end_after
                             else stop_code + end, name + " end")

    # Supply draw-call count only to the transient inline set-dressing API.
    html = replace_exact(
        html, "wallPos,W,D}):{pieces:0};",
        "wallPos,W,D,faceCount:()=>P.length/9}):{pieces:0};",
        "in-memory V3 detail instrumentation API"
    )
    tokens = {
        "rail": "B(x,1.138,.50,.71,.02,.78,C.gunmetal,4,s*.22);",
        "plate": "B(x,.425,.605,.55,.028,.84,0x948987,3,s*.22);",
        "switches": ("for(let j=0;j<8;j++){\n"
                     "      const zz=.16+j*.10;\n"
                     "      B(x+s*.20,1.18,zz,.046,.018,.04,j%3===0?C.cyan:C.bronze,8,s*.22);\n"
                     "    }"),
        "ribs": ("for(let j=0;j<3;j++)"
                 "B(x+s*.33,.60+j*.19,.64,.025,.06,.12,0x6c6165,3,s*.22);"),
    }
    for region, token in tokens.items():
        details = mark_call(details, token, region)

    for file in ("hero-v3.js", "furniture.js", "set-details.js"):
        tag = f'<script src="{file}"></script>'
        raw = details if file == "set-details.js" else (V3 / file).read_text()
        html = replace_exact(html, tag, "<script>" + raw + "</script>",
                             "inline original " + file)

    marker = "window.__asteriaWalkthrough={roomId:"
    html = replace_exact(
        html, marker,
        "window.__astAuditPositions=P;" + marker,
        "read-only mesh positions exposure"
    )
    stub = """<script>(()=>{
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
    return replace_exact(html, "</head>", stub + "</head>", "WebGL no-op capture")

def verify(observed: dict) -> dict:
    assert observed["triangles"] == TRIANGLES, observed["triangles"]
    result = []
    for side in ("-1", "1"):
        data = observed["under"].get(side)
        assert isinstance(data, dict), (side, observed["under"])
        for name, faces, proposed in (
            ("rail", 12, False), ("plate", 12, True),
            ("switches", 96, False), ("ribs", 36, True)
        ):
            start, end = data.get(name + "Start"), data.get(name + "End")
            assert isinstance(start, (int, float)) and isinstance(end, (int, float))
            assert 0 <= start == int(start) < end == int(end) <= TRIANGLES
            assert end - start == faces, (side, name, start, end, faces)
            result.append({"name": f"underPylon{side}/{name}",
                           "side": int(side), "component": name,
                           "start": int(start), "end": int(end),
                           "faces": faces, "candidateRemovalOnly": proposed})
    result.sort(key=lambda item: item["start"])
    for a, b in zip(result, result[1:]):
        assert a["end"] <= b["start"], (a, b, "overlapping draw-call intervals")
    protected = observed["protected"]
    for name, span in protected.items():
        assert 0 <= span["start"] == int(span["start"]) < span["end"] == int(span["end"]) <= TRIANGLES
        for r in result:
            assert r["end"] <= span["start"] or r["start"] >= span["end"], (
                name, r, "protected captain or command face overlap")
    removable = [r for r in result if r["candidateRemovalOnly"]]
    assert len(removable) == 4
    assert sum(r["faces"] for r in removable) == 96
    assert sum(r["faces"] for r in result if not r["candidateRemovalOnly"]) == 216
    return {
        "id": "AST_D01_ORIGINAL_UNDER_CONSOLE_V3_READ_ONLY_EXACT_FACE_PROOF",
        "sourceIndexGitBlob": V3_BLOB, "setDetailsGitBlob": DETAILS_BLOB,
        "totalOriginalFaces": TRIANGLES, "ranges": result,
        "hypotheticalPlateAndRibsFaces": 96,
        "protectedRailAndTactileFaces": 216,
        "protectedMainRegions": protected,
        "frozenFilesModified": False, "productionChanged": False,
        "candidateRemovalApplied": False, "artApproved": False,
        "meaning": "Source-exact original face intervals only; not permission to remove live geometry",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    executable = shutil.which("google-chrome") or shutil.which("chromium")
    assert executable, "Real Chromium required for exact original source capture"
    html = instrument()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=executable, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 460, "height": 340})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(html, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("window.__astAuditUnder !== undefined", timeout=90000)
        observed = page.evaluate("""() => ({
          triangles: window.__asteriaWalkthrough.meshTriangles,
          under: window.__astAuditUnder,
          protected: window.__astAuditProtected
        })""")
        assert not errors, errors
        report = verify(observed)
        browser.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("ASTERIA_EXACT_UNDER_PYLON_PROVENANCE", json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
