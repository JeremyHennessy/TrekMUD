#!/usr/bin/env python3
"""Exact-source 96-triangle original V3 under-console exclusion, opt-in art only.
Require original V3 Chromium arrays and independently measured source face proof.
No edits to frozen V3 or original builder, renderer, controls or production.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
V3='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
DETAILS='3716accf4490bf28da56be0ae21081ab3a3a0f17'
def parse_glb(raw):
 assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
 assert struct.unpack_from('<I',raw,8)[0]==len(raw)
 n,typ=struct.unpack_from('<I4s',raw,12);assert typ==b'JSON'
 data=json.loads(raw[20:20+n])
 m,typ=struct.unpack_from('<I4s',raw,20+n);assert typ==b'BIN\x00'
 assert 28+n+m==len(raw)
 return data,raw[28+n:]
def run(a):
 site=a.site;manifest=json.loads((site/'models/manifest.json').read_text())
 proof=json.loads(a.proof.read_text())
 assert (manifest['triangles'],manifest['original_triangles'])==(80846,106988)
 assert manifest['source_git_blob']==proof['sourceIndexGitBlob']==V3
 assert proof['setDetailsGitBlob']==DETAILS
 assert proof['hypotheticalPlateAndRibsFaces']==96 and proof['protectedRailAndTactileFaces']==216
 assert proof['candidateRemovalApplied'] is False
 ranges=proof['ranges'];assert len(ranges)==8 and len({x['name'] for x in ranges})==8
 removal=sorted([x for x in ranges if x['candidateRemovalOnly']],key=lambda x:x['start'])
 protected=[x for x in ranges if not x['candidateRemovalOnly']]
 assert [(x['side'],x['component'],x['faces']) for x in removal]==[
  (-1,'plate',12),(-1,'ribs',36),(1,'plate',12),(1,'ribs',36)]
 assert [(x['side'],x['component'],x['faces']) for x in protected]==[
  (-1,'rail',12),(-1,'switches',96),(1,'rail',12),(1,'switches',96)]
 old=(site/'models/asteria-v3-restored-pbr.glb').read_bytes()
 assert hashlib.sha256(old).hexdigest()==manifest['sha256']
 doc,binary=parse_glb(old)
 assert doc['extras']['remainingV3Triangles']==80846
 orig=np.load(a.capture/'positions.npy').reshape(-1,3,3)
 material=np.load(a.capture/'materials.npy').reshape(-1,3)
 assert len(orig)==len(material)==106988
 assert np.all(material==material[:,0,None])
 keep=np.ones(106988,dtype=bool)
 ranges_removed=[(14404,30676)]+[(s['start'],s['end']) for s in manifest['command_source_ranges']]
 for kind in ('three_rib_bays_source_ranges','envelope_source_ranges','forward_portal_source_ranges'):
  ranges_removed.extend((s['start'],s['end']) for s in manifest[kind])
 assert sum(hi-lo for lo,hi in ranges_removed)==106988-80846
 for lo,hi in ranges_removed:
  assert keep[lo:hi].all();keep[lo:hi]=False
 assert int(keep.sum())==80846
 main_regions=[(12620,14404),(14404,30676),(30676,37104),(93950,94366)]
 for x in removal+protected:
  lo,hi=x['start'],x['end']
  assert hi-lo==x['faces'] and keep[lo:hi].all()
  assert all(hi<=begin or lo>=end for begin,end in main_regions)
 original_ids=np.flatnonzero(keep & (material[:,0]==3))
 primitive=doc['meshes'][3]['primitives'][0]
 assert primitive['material']==3 and primitive['mode']==4 and 'indices' not in primitive
 attrs=primitive['attributes']
 assert set(attrs)=={'POSITION','NORMAL','COLOR_0','TEXCOORD_0'}
 posaccess=doc['accessors'][attrs['POSITION']]
 count=posaccess['count'];assert count==len(original_ids)*3
 bv=doc['bufferViews'][posaccess['bufferView']]
 actual=np.frombuffer(binary,dtype='<f4',count=count*3,offset=bv['byteOffset']).reshape(-1,3,3)
 assert np.allclose(actual,orig[original_ids],atol=1e-6,rtol=0),'GLB source order mismatch'
 removed=np.concatenate([np.arange(x['start'],x['end']) for x in removal])
 assert len(removed)==96 and np.all(material[removed]==3)
 selected=np.isin(original_ids,removed)
 assert int(selected.sum())==96
 vertex_keep=np.repeat(~selected,3)
 targets={doc['accessors'][index]['bufferView']:(name,index) for name,index in attrs.items()}
 assert len(targets)==4
 out=bytearray()
 for i,view in enumerate(doc['bufferViews']):
  raw=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
  assert len(raw)==view['byteLength']
  if i in targets:
   name,index=targets[i];acc=doc['accessors'][index]
   dtype={5126:np.float32,5121:np.uint8}[acc['componentType']]
   dims={'VEC3':3,'VEC2':2}[acc['type']]
   arr=np.frombuffer(raw,dtype=dtype).reshape(-1,dims)
   assert len(arr)==count
   arr=arr[vertex_keep]
   assert len(arr)==count-288
   raw=arr.tobytes();acc['count']=len(arr)
   if name=='POSITION':
    acc['min']=arr.min(axis=0).astype(float).tolist()
    acc['max']=arr.max(axis=0).astype(float).tolist()
  while len(out)%4:out.append(0)
  view['byteOffset']=len(out);view['byteLength']=len(raw);out.extend(raw)
 while len(out)%4:out.append(0)
 doc['buffers'][0]['byteLength']=len(out)
 doc['extras']['underConsolePlateRibsExcludedFaces']=96
 doc['extras']['underConsoleExactSourceRanges']=removal
 doc['extras']['remainingV3Triangles']=80750
 newjson=json.dumps(doc,separators=(',',':')).encode()
 newjson+=b' '*((-len(newjson))%4)
 glb=(struct.pack('<4sII',b'glTF',2,28+len(newjson)+len(out))+
      struct.pack('<I4s',len(newjson),b'JSON')+newjson+
      struct.pack('<I4s',len(out),b'BIN\x00')+out)
 assert parse_glb(glb)[0]['extras']['remainingV3Triangles']==80750
 newglb=a.out/'models/asteria-v3-restored-pbr.glb'
 newglb.parent.mkdir(parents=True,exist_ok=True);newglb.write_bytes(glb)
 manifest.update(sha256=hashlib.sha256(glb).hexdigest(),bytes=len(glb),triangles=80750,
                 under_console_original_faces_removed=96,under_console_source_ranges=removal)
 (newglb.parent/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 app=(site/'app.js').read_text()
 token='Se!==106988-Be-ft-174-864-204'
 assert app.count(token)==1, 'Pinned UI loader count changed, refusing candidate'
 updated=app.replace(token,token+'-96',1)
 assert updated.replace(token+'-96',token,1)==app
 (a.out/'app.js').write_text(updated)
 receipt={'sourceV3Blob':V3,'setDetailsBlob':DETAILS,'baselineGlbSHA256':hashlib.sha256(old).hexdigest(),
          'candidateGlbSHA256':manifest['sha256'],'excludedFaces':removal,
          'protectedRailAndSwitchFaces':protected,'retainedV3Faces':80750,
          'sourceVerified':True,'artApproved':False,'releaseApproved':False}
 (a.out/'stage33-source-exclusion-proof.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('STAGE33_EXACT_SOURCE_V3_96_FACE_REMOVAL',json.dumps(receipt),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ('site','capture','proof','out'):p.add_argument('--'+name,type=Path,required=True)
 run(p.parse_args())
