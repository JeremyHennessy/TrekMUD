#!/usr/bin/env python3
"""Read-only Stage36 original pilot-seat provenance using actual V3 Chromium.

Shared approved V3 hero generator and original files remain untouched.
This identifies exact hypothetical replacement intervals; no geometry deletion.
"""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from asteria_source_underconsole_audit import (
    instrument as original_instrument,
    replace_exact, git_blob, V3, V3_BLOB, DETAILS_BLOB, TRIANGLES,
)

HERO_BLOB = "95ac0fc2d480736ddf2f38f596d1115a4193f926"


def marker(html: str, token: str, label: str, prefix: str, suffix: str) -> str:
    return replace_exact(html, token, prefix + token + suffix, label)


def instrument() -> str:
    assert git_blob(V3 / "hero-v3.js") == HERO_BLOB
    html = original_instrument()  # already verified original source & no-op WebGL
    html = marker(
        html, "chair(s*1.15,-2.13,0,false);", "original pilot pair",
        "window.__pilot=window.__pilot||{};window.__pilot[String(s)]={start:P.length/9};",
        "window.__pilot[String(s)].end=P.length/9;",
    )
    html = marker(
        html, "box(s*1.1,.27,-3.42,.53,.25,.12,0xb1a39f,2);",
        "keep original adjacent flight footrest",
        "window.__pilotFoot=window.__pilotFoot||{};"
        "window.__pilotFoot[String(s)]={start:P.length/9};",
        "window.__pilotFoot[String(s)].end=P.length/9;",
    )
    html = marker(
        html, "chair(3.85,-1.1,-.36);", "keep tactical chair",
        "window.__pilotTactical={start:P.length/9};",
        "window.__pilotTactical.end=P.length/9;",
    )
    original_glass = (
        "for(let i=0;i<6;i++){let x=(i-2.5)*.88,z=-3.19+"
        ".23*Math.pow(x/2.45,2);surface(x,1.087,z-.09,.77,.76,"
        "Math.atan2(.18*x,1),0xffffff,i%2===0?0:1,.085);}"
    )
    html = marker(
        html, original_glass, "keep six original forward screens",
        "window.__pilotGlass={start:P.length/9};",
        "window.__pilotGlass.end=P.length/9;",
    )
    for label, token in {
        "base": "B(s*1.14,.56,-2.13,.41,.07,.18,C.gunmetal,4);",
        "rail": "B(s*1.14,.83,-1.84,.43,.024,.05,C.bronze,4);",
        "horiz": (
            "for(let k=0;k<4;k++)B(s*1.14,.89+k*.145,"
            "-1.73+k*.014,.42,.018,.022,0xb4a1a7,4);"
        ),
    }.items():
        html = marker(
            html, token, "pilot-dressing-" + label,
            "window.__pilotDress=window.__pilotDress||{};"
            "window.__pilotDress[String(s)]=window.__pilotDress[String(s)]||{};"
            f"window.__pilotDress[String(s)]['{label}Start']=api.faceCount();",
            f"window.__pilotDress[String(s)]['{label}End']=api.faceCount();",
        )
    return html


def check(result: dict) -> dict:
    assert result["total"] == TRIANGLES == 106988
    spans = []
    for side in ("-1", "1"):
        ch = result["pilot"][side]
        ft = result["feet"][side]
        assert 1000 < ch["end"] - ch["start"] < 20000, ch
        assert ft["end"] - ft["start"] == 12, ft
        spans += [
            dict(name="pilotChair" + side, side=int(side),
                 component="sharedHeroChairLargeFalse", start=int(ch["start"]),
                 end=int(ch["end"]), candidateOnly=True),
            dict(name="pilotFrontFootrest" + side, side=int(side),
                 component="originalFootrest", start=int(ft["start"]),
                 end=int(ft["end"]), candidateOnly=False),
        ]
        dr = result["dressing"][side]
        for label, expected in (("base", 12), ("rail", 12), ("horiz", 48)):
            start, end = dr[label + "Start"], dr[label + "End"]
            assert end - start == expected, (side, label, start, end)
            spans.append(dict(name=f"pilotDress{side}/{label}", side=int(side),
                              component=label, start=int(start), end=int(end),
                              candidateOnly=True))
    spans.sort(key=lambda x: x["start"])
    for s in spans:
        assert 0 <= s["start"] < s["end"] <= TRIANGLES, s
        s["faces"] = s["end"] - s["start"]
    for a, b in zip(spans, spans[1:]):
        assert a["end"] <= b["start"], ("overlap", a, b)
    protected = dict(result["protected"], tactical=result["tactical"],
                     originalFlightGlass=result["glass"])
    for name, r in protected.items():
        assert 0 <= r["start"] < r["end"] <= TRIANGLES, (name, r)
        for s in spans:
            assert s["end"] <= r["start"] or r["end"] <= s["start"], (name, s)
    chairs = [s for s in spans if s["component"] == "sharedHeroChairLargeFalse"]
    assert len(chairs) == 2 and chairs[0]["faces"] == chairs[1]["faces"]
    selected = [s for s in spans if s["candidateOnly"]]
    assert len(selected) == 8
    removed = sum(s["faces"] for s in selected)
    assert removed == 2 * chairs[0]["faces"] + 144
    return dict(
        id="AST_D01_STAGE36_PILOT_CHAIRS_EXACT_SOURCE_SPANS_READ_ONLY",
        sourceV3Blob=V3_BLOB, sourceHeroBlob=HERO_BLOB,
        sourceDetailsBlob=DETAILS_BLOB, originalFaceCount=TRIANGLES,
        ranges=spans, protectedSourceRanges=protected,
        pilotChairFacesEach=chairs[0]["faces"],
        pilotDressingFacesTotal=144,
        hypotheticalOriginalFacesRemoved=removed,
        candidateRemovalApplied=False, frozenSourceModified=False,
        productionChanged=False, artApproved=False, releaseApproved=False,
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    out = p.parse_args().output
    executable = shutil.which("google-chrome") or shutil.which("chromium")
    assert executable, "Real Chromium required"
    html = instrument()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=executable, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 460, "height": 340})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(html, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_function("window.__asteriaWalkthrough !== undefined", timeout=90000)
        observed = page.evaluate("""() => ({
          total: window.__asteriaWalkthrough.meshTriangles,
          pilot: window.__pilot, feet: window.__pilotFoot,
          dressing: window.__pilotDress,
          protected: window.__astAuditProtected,
          tactical: window.__pilotTactical, glass: window.__pilotGlass
        })""")
        assert not errors, errors
        report = check(observed)
        browser.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("STAGE36_GENUINE_CHROMIUM_PILOT_SOURCE_PROOF", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
