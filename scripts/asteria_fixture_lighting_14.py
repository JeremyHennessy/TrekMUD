#!/usr/bin/env python3
"""Build an entirely optional Asteria fixture-aligned lighting test source.

This file alters ONLY the six unshadowed simulated roof spotlights in a
temporary, QA-generated JavaScript source. The original source and all old
published routes remain untouched. This is a lighting proxy (not baked GI).
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

OLD="""  for(const x of [-3.4,3.4])for(const z of [-3.4,1.35,4.05]){
    const lamp=new THREE.SpotLight(0xffdfc4,2.8,11,Math.PI/3,.94,2);
    lamp.position.set(x,4.07,z);
    lamp.target.position.set(x*.74,0,z*.82);
    scene.add(lamp,lamp.target);
  }"""
NEW="""  // STAGE14 REVIEW-ONLY: 12 diffuse roof practicals at the precise
  // positions authored into build_ceiling() (k=0,8,...,88, r=.77).
  // Replaces six unrelated studio spots, not extra lights or edited UI.
  // This is physically located direct fixture illumination, NOT GI.
  for(let k=0;k<96;k+=8){
    const a=(k+.5)*Math.PI*2/96,r=.77;
    const x=7.55*Math.sin(a)*r,z=6.55*Math.cos(a)*r;
    const y=4.38-(r-.36)/(.985-.36)*.66-.055;
    const lamp=new THREE.SpotLight(0xffd9bc,2.2,8,Math.PI/3,.90,2);
    lamp.position.set(x,y,z);
    lamp.target.position.set(x*.74,.80,z*.74);
    lamp.castShadow=false;
    scene.add(lamp,lamp.target);
  }
  document.body.dataset.fixtureLighting='12';
  document.body.dataset.fixtureLightingMode='qa-only-no-indirect-gi';"""

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--report",type=Path,required=True)
 args=p.parse_args()
 source=args.source.read_text(encoding="utf-8")
 assert source.count(OLD)==1, "Original V5 lighting baseline drifted; refuse patch"
 assert 'dataset.fixtureLighting' not in source
 assert '74a154ae62bccb0c16d03c2ecf791a64ab19ce81' in source
 candidate=source.replace(OLD,NEW)
 assert candidate.count(NEW)==1
 assert candidate.replace(NEW,OLD)==source
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(candidate,encoding="utf-8")
 report={
   "id":"ASTERIA_LIGHT14_FIXTURE_LOCATION_ONLY",
   "originalSceneSourceSha256":hashlib.sha256(source.encode()).hexdigest(),
   "temporaryCandidateSourceSha256":hashlib.sha256(candidate.encode()).hexdigest(),
   "onlyPatch":"replace existing six roof studio spotlights with 12 fixture-coincident spots",
   "existingSpotlightsRemoved":6,"newFixtures":12,
   "physicalRoofSectorIndices":list(range(0,96,8)),
   "noGameOrUIChanges":True,
   "noExportedLightmapOrTrueBrowserGI":True,
   "notApproved":True,
 }
 args.report.parent.mkdir(parents=True,exist_ok=True)
 args.report.write_text(json.dumps(report,indent=2)+"\n")
 print("FIXTURE_LOCATION_ONLY_QA_PATCH",json.dumps(report))

if __name__=="__main__":
 main()
