#!/usr/bin/env python3
"""Stage40 opt-in prototype: source-exact V3 mask from independently passed Stage36.

Pinned original and Stage36 artifacts are immutable. No source clipping by
position; only the exact historical 32,600 original pilot-face mask and the
96 proven obsolete under-console faces are re-used. No production changes.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
from asteria_stage40_integrated_zone import run as build

SOURCE_BLOB='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
STAGE36_V3_SHA='00c42fbff86498bbbfc021d8afbf7348caa2b0528b7fd77c7b6e1c710f1ee886'
STAGE36_RUN_SHA='1920ca11124b03c0a90a8a37e09c0774f867e4a3'

def run(base,prior,output):
    control=output/'control';candidate=output/'candidate'
    assert not control.exists() and not candidate.exists(), 'Never overwrite existing trial'
    shutil.copytree(base/'site',control);shutil.copytree(base/'site',candidate)
    source=prior/'_pilot_site/candidate/models/asteria-v3-restored-pbr.glb'
    v3=source.read_bytes()
    assert hashlib.sha256(v3).hexdigest()==STAGE36_V3_SHA
    proof=json.loads((prior/'_pilot_evidence/stage36-exact-v3-source-mask.json').read_text())
    audit=json.loads((prior/'_pilot_evidence/stage36-original-pilot-provenance.json').read_text())
    old=json.loads((prior/'_pilot_evidence/underconsole-original-provenance.json').read_text())
    assert proof['removedExactOriginalPilotFaces']==32600
    assert proof['remainingOriginalV3Faces']==48150
    assert proof['sourceV3Blob']==audit['sourceV3Blob']==SOURCE_BLOB
    assert audit['sourceHeroBlob']=='95ac0fc2d480736ddf2f38f596d1115a4193f926'
    assert audit['sourceDetailsBlob']=='3716accf4490bf28da56be0ae21081ab3a3a0f17'
    assert old['sourceIndexGitBlob']==SOURCE_BLOB
    pilot_ranges=[r for r in audit['ranges'] if r['candidateOnly']]
    assert len(pilot_ranges)==8 and sum(r['faces'] for r in pilot_ranges)==32600
    under_ranges=[r for r in old['ranges'] if r['candidateRemovalOnly']]
    assert len(under_ranges)==4 and sum(r['faces'] for r in under_ranges)==96
    (candidate/'models/asteria-v3-restored-pbr.glb').write_bytes(v3)
    manifest_path=candidate/'models/manifest.json';meta=json.loads(manifest_path.read_text())
    assert meta['triangles']==80846 and meta['source_git_blob']==SOURCE_BLOB
    meta.update(sha256=STAGE36_V3_SHA,bytes=len(v3),triangles=48150,
                under_console_original_faces_removed=96,under_console_source_ranges=under_ranges,
                stage40_original_pilot_faces_removed=32600,stage40_pilot_source_ranges=pilot_ranges)
    manifest_path.write_text(json.dumps(meta,indent=2)+'\n')
    appfile=candidate/'app.js';app=appfile.read_text()
    original_guard='Se!==106988-Be-ft-174-864-204'
    assert app.count(original_guard)==1
    appfile.write_text(app.replace(original_guard,original_guard+'-96-32600',1))
    build(control,candidate,output/'stage40-forward-command-proof.json')
    assert (control/'models/asteria-hero-chair-candidate.glb').read_bytes()==(candidate/'models/asteria-hero-chair-candidate.glb').read_bytes()
    print('STAGE40_PINNED_SOURCE_MASK_AND_INTEGRATED_FORWARD_SET',json.dumps({
        'v3ProtectedGitBlob':SOURCE_BLOB,'exactPilotsRemoved':32600,
        'exactOldUnderConsoleRemoved':96,'candidateV3SHA256':STAGE36_V3_SHA,
        'defaultControlsAndUIChanged':False,'productionChanged':False,
        'artApproved':False}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for key in ('base','prior','output'):ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args();run(a.base,a.prior,a.output)