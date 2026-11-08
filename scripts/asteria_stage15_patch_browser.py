#!/usr/bin/env python3
"""Apply ONE QA-only change to the generated Stage12 envelope browser source.

The glTF/GLBs, AO maps, original UI, controls, camera, source meshes and
collision are never touched. A copy of its renderer receives two separate
Blender/Cycles diffuse-indirect PNGs as Three.js r187 UV1 lightmaps.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ANCHOR = "document.body.dataset.envelopeLoaded='true';"
PATCH = """               document.body.dataset.envelopeLoaded='true';
               // STAGE15 REVIEW-ONLY: real Cycles diffuse INDIRECT, not AO
               // or another direct-light proxy. Existing PBR + UV1 AO remain.
               const giFiles=[
                 './models/asteria-stage15-wall-indirect.png',
                 './models/asteria-stage15-ceiling-indirect.png'
               ];
               const textureLoader=new THREE.TextureLoader();
               Promise.all(giFiles.map(url=>textureLoader.loadAsync(url)))
                 .then(textures=>{
                   const encountered=new Set();
                   let receivers=0;
                   for(const texture of textures){
                     texture.flipY=false; // same glTF-export UV1 orientation
                     texture.channel=1;  // Three r187 TEXCOORD_1 / uv1
                     texture.colorSpace=THREE.SRGBColorSpace; // 8-bit PNG transfer
                     texture.wrapS=THREE.ClampToEdgeWrapping;
                     texture.wrapT=THREE.ClampToEdgeWrapping;
                   }
                   architecture.traverse(object=>{
                     if(!object.isMesh || !object.material?.aoMap)return;
                     const name=(object.name||'').toLowerCase();
                     const target=name.includes('wall')?'wall':
                                  name.includes('ceiling')?'ceiling':null;
                     if(!target || encountered.has(target) ||
                        !object.geometry.attributes.uv1 || !object.geometry.attributes.uv)
                       throw new Error('Stage15 missing unique wall/ceiling UV1 GI receiver: '+object.name);
                     const texture=textures[target==='wall'?0:1];
                     const material=object.material.clone();
                     material.lightMap=texture;
                     material.lightMapIntensity=1.0;
                     material.needsUpdate=true;
                     object.material=material;
                     encountered.add(target);receivers++;
                   });
                   if(receivers!==2 || encountered.size!==2)
                     throw new Error('Stage15 expected exactly two original AO receivers, got '+receivers);
                   document.body.dataset.stage15GILoaded='true';
                   document.body.dataset.stage15GIReceivers=String(receivers);
                   window.__asteriaGIReview={
                     mode:'real-Cycles-diffuse-indirect-only',
                     diffuseBounces:3,textureChannel:1,
                     receiverNames:[...encountered],
                     originalGlbsUnchanged:true,
                     originalAOStillEnabled:true,
                     noChangesToCampaignOrControls:true,
                     notArtApproved:true
                   };
                 })
                 .catch(e=>fail('Stage15 indirect lightmap rejected: '+String(e.message||e)));"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    a = p.parse_args()
    original = a.source.read_text(encoding="utf-8")
    assert original.count(ANCHOR) == 1, "Stage12 browser loader drifted"
    assert "74a154ae62bccb0c16d03c2ecf791a64ab19ce81" in original
    assert "stage15GILoaded" not in original
    patched = original.replace(ANCHOR, PATCH)
    assert patched.count(PATCH) == 1
    assert patched.replace(PATCH, ANCHOR) == original, "Only one surgical loader patch allowed"
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(patched, encoding="utf-8")
    report = {
        "id": "ASTERIA_STAGE15_TEMPORARY_SINGLE_PATCH",
        "sourceSha256": hashlib.sha256(original.encode()).hexdigest(),
        "candidateSha256": hashlib.sha256(patched.encode()).hexdigest(),
        "onlyChange": "Two independently baked Cycles indirect-only lightmaps added to original UV1 wall/ceiling AO receivers in copied QA renderer",
        "originalGLBsOrPBRMaterialsRebuilt": False,
        "originalAOMapsPreserved": True,
        "gameUICollisionAndWalkwayUnchanged": True,
        "publicOrProductionChange": False,
        "notArtApproved": True,
    }
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("STAGE15_TEMPORARY_BROWSER_GI_PATCH", json.dumps(report))


if __name__ == "__main__":
    main()
