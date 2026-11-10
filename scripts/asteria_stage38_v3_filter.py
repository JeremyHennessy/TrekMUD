#!/usr/bin/env python3
"""Stage38 exact 32,600-triangle V3 pilot-chair substitution, isolated art trial.

No original V3/hero/set-details edits. Retain pilot footrests, captain,
tactical, forward screens, controls and all other source faces.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
from asteria_stage33_v3_filter import parse_glb

V3='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
HERO='95ac0fc2d480736ddf2f38f596d1115a4193f926'
DETAILS='3716accf4490bf28da56be0ae21081ab3a3a0f17'
BASE=80750
REMOVE=32600
FINAL=48150
EXPECTED=[(43592,59820),(59832,76060),
          (103036,103048),(103048,103060),(103060,103108),
          (103356,103368),(103368,103380),(103380,103428)]

def run(site,capture,proof,receipt):
    audit=json.loads(proof.read_text())
    assert (audit['sourceV3Blob'],audit['sourceHeroBlob'],audit['sourceDetailsBlob'])==(V3,HERO,DETAILS)
    assert audit['originalFaceCount']==106988 and audit['hypotheticalOriginalFacesRemoved']==REMOVE
    assert audit['candidateRemovalApplied'] is False
    selected=sorted((r for r in audit['ranges'] if r['candidateOnly']),key=lambda r:r['start'])
    assert len(selected)==8
    ranges=[(r['start'],r['end']) for r in selected]
    assert ranges==EXPECTED,(ranges,EXPECTED)
    assert all(r['faces']==r['end']-r['start'] for r in selected)
    protected=audit['protectedSourceRanges']
    for p in protected.values():
        assert all(b<=p['start'] or a>=p['end'] for a,b in ranges)
    manifest_path=site/'models/manifest.json'
    manifest=json.loads(manifest_path.read_text())
    assert manifest['triangles']==BASE and manifest['under_console_original_faces_removed']==96
    glb_path=site/'models/asteria-v3-restored-pbr.glb'
    prior_glb=glb_path.read_bytes()
    assert hashlib.sha256(prior_glb).hexdigest()==manifest['sha256']
    doc,binary=parse_glb(prior_glb)
    source=np.load(capture/'positions.npy').reshape(-1,3,3)
    mats=np.load(capture/'materials.npy').reshape(-1,3)
    assert len(source)==len(mats)==106988 and np.all(mats==mats[:,0,None])
    # Pinned V5 exporter (unchanged) reclassifies exactly two starfield faces
    # from original material 7 to unlit material 9. Match source geometry.
    pos=source.reshape(-1,3)
    groups=mats.reshape(-1)
    star=(groups==7)&(np.abs(pos[:,2]+6.06)<.0005)&(np.abs(pos[:,0])<=3.101)
    assert int(star.sum())==6
    assert np.all(star.reshape(-1,3)==star.reshape(-1,3)[:,0,None])
    mats=mats.copy();mats.reshape(-1)[star]=9
    assert int((mats[:,0]==9).sum())==2
    keep=np.ones(106988,dtype=bool)
    prior=[(14404,30676)]
    for key in ('command_source_ranges','three_rib_bays_source_ranges',
                'envelope_source_ranges','forward_portal_source_ranges','under_console_source_ranges'):
        prior.extend((r['start'],r['end']) for r in manifest[key])
    for a,b in prior:
        assert keep[a:b].all(),('prior source overlap',a,b)
        keep[a:b]=False
    assert int(keep.sum())==BASE
    removed=np.concatenate([np.arange(a,b) for a,b in ranges])
    assert len(removed)==REMOVE and keep[removed].all()
    updates={};count_removed=0
    for idx,mesh in enumerate(doc['meshes']):
        prim=mesh['primitives'][0]
        assert prim['material']==idx and prim['mode']==4 and 'indices' not in prim
        attrs=prim['attributes']
        assert set(attrs)=={'POSITION','NORMAL','COLOR_0','TEXCOORD_0'}
        ids=np.flatnonzero(keep & (mats[:,0]==idx))
        hit=np.isin(ids,removed,assume_unique=True)
        n=int(hit.sum());count_removed+=n
        vk=np.repeat(~hit,3)
        for name,ai in attrs.items():
            access=doc['accessors'][ai]
            view=doc['bufferViews'][access['bufferView']]
            offset=view.get('byteOffset',0)
            rawview=binary[offset:offset+view['byteLength']]
            dtype={5126:'<f4',5121:'u1'}[access['componentType']]
            dim={'VEC3':3,'VEC2':2}[access['type']]
            arr=np.frombuffer(rawview,dtype=dtype).reshape(-1,dim)
            assert len(arr)==access['count']==len(ids)*3,(idx,name,len(arr),access['count'],len(ids))
            if name=='POSITION':
                assert np.allclose(arr.reshape(-1,3,3),source[ids],atol=1e-6,rtol=0),('source order',idx)
            if n:
                arr=arr[vk]
                assert len(arr)==(len(ids)-n)*3
                access['count']=len(arr)
                if name=='POSITION':
                    assert len(arr)>0
                    access['min']=arr.min(axis=0).astype(float).tolist()
                    access['max']=arr.max(axis=0).astype(float).tolist()
                updates[access['bufferView']]=arr.tobytes()
    assert count_removed==REMOVE
    output=bytearray()
    for idx,view in enumerate(doc['bufferViews']):
        offset=view.get('byteOffset',0)
        old=binary[offset:offset+view['byteLength']]
        updated=updates.get(idx,old)
        output.extend(b'\0'*(-len(output)%4))
        view['byteOffset']=len(output);view['byteLength']=len(updated)
        output.extend(updated)
    output.extend(b'\0'*(-len(output)%4))
    doc['buffers'][0]['byteLength']=len(output)
    doc['extras'].update(stage38PilotOriginalFacesRemoved=REMOVE,
        stage38PilotExactSourceRanges=selected,remainingV3Triangles=FINAL)
    js=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode()
    js+=b' '*(-len(js)%4)
    final=(struct.pack('<4sII',b'glTF',2,28+len(js)+len(output))+
        struct.pack('<I4s',len(js),b'JSON')+js+
        struct.pack('<I4s',len(output),b'BIN\x00')+output)
    assert parse_glb(final)[0]['extras']['remainingV3Triangles']==FINAL
    glb_path.write_bytes(final)
    manifest.update(sha256=hashlib.sha256(final).hexdigest(),bytes=len(final),
        triangles=FINAL,stage38_pilot_original_faces_removed=REMOVE,
        stage38_pilot_source_ranges=selected)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    appfile=site/'app.js';app=appfile.read_text()
    guard='Se!==106988-Be-ft-174-864-204-96'
    assert app.count(guard)==1
    appfile.write_text(app.replace(guard,guard+'-32600',1))
    result={'sourceV3Blob':V3,'heroBlob':HERO,'detailsBlob':DETAILS,
        'oldModelSHA256':hashlib.sha256(prior_glb).hexdigest(),
        'newModelSHA256':manifest['sha256'],
        'removedExactOriginalPilotFaces':REMOVE,'protectedFacesRetained':True,
        'remainingOriginalV3Faces':FINAL,'actualMaterialPartitionProven':True,
        'artApproved':False,'productionUnchanged':True}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print('STAGE38_EXACT_PILOT_SOURCE_REPLACEMENT',json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('site','capture','proof','receipt'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args()
    run(a.site,a.capture,a.proof,a.receipt)
