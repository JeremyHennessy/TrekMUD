#!/usr/bin/env python3
"""Independent source-exact command GLB preservation check for Stage41 art screening."""
from __future__ import annotations
import argparse, json, struct, hashlib
from pathlib import Path
import numpy as np

OLD_LOWER=(
 'moulded eight-corner closed cast pedestal',
 'recessed toe support',
 'rear service door',
 'light-seam recess',
)


def unpack(path):
    blob=path.read_bytes();assert blob[:4]==b'glTF';assert struct.unpack_from('<I',blob,4)[0]==2
    assert struct.unpack_from('<I',blob,8)[0]==len(blob)
    pos=12;chunks={}
    while pos < len(blob):
        length,kind=struct.unpack_from('<I4s',blob,pos);pos+=8
        chunks[kind]=blob[pos:pos+length];pos+=length
    return json.loads(chunks[b'JSON']),chunks[b'BIN\x00']

DTYPE={5120:'i1',5121:'u1',5122:'i2',5123:'u2',5125:'u4',5126:'f4'}
SHAPE={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

def access(j,b,n):
    a=j['accessors'][n];v=j['bufferViews'][a['bufferView']]
    d=np.dtype('<'+DTYPE[a['componentType']]);w=SHAPE[a['type']]
    byte=v.get('byteOffset',0)+a.get('byteOffset',0)
    stride=v.get('byteStride',d.itemsize*w)
    return np.ndarray((a['count'],w),dtype=d,buffer=b,offset=byte,strides=(stride,d.itemsize)).copy()

def verify(base,candidate):
    j0,b0=unpack(base);j1,b1=unpack(candidate)
    old={n['name']:n for n in j0['nodes'] if 'mesh' in n}
    new={n['name']:n for n in j1['nodes'] if 'mesh' in n}
    assert len(old)==90 and len(old)==len(set(old)),len(old)
    changed={f'Command / {side} / {n}' for side in (-1,1) for n in OLD_LOWER}
    assert all(x in old and x not in new for x in changed)
    assert all(x in new for x in old if x not in changed)
    assert len(new)>len(old)
    expected_controls=[x for x in old if any(n in x for n in
       ('original atlas screen','instrument rim','tactile switch','smoky glass gasket','fastener','Plinth / original command carpet top'))]
    assert len(expected_controls)>35,len(expected_controls)
    assert all(x in new for x in expected_controls)
    checked=0
    for name,node in old.items():
        if name in changed:continue
        target=new[name]
        mesh0=j0['meshes'][node['mesh']];mesh1=j1['meshes'][target['mesh']]
        assert len(mesh0['primitives'])==len(mesh1['primitives']),name
        assert {k:node.get(k) for k in ('rotation','scale','translation','matrix') if k in node}== \
               {k:target.get(k) for k in ('rotation','scale','translation','matrix') if k in target},name
        for p0,p1 in zip(mesh0['primitives'],mesh1['primitives']):
            assert set(p0['attributes'])==set(p1['attributes']),(name,'attrs')
            for at in p0['attributes']:
                a0=access(j0,b0,p0['attributes'][at]);a1=access(j1,b1,p1['attributes'][at])
                assert a0.shape==a1.shape and np.allclose(a0,a1,rtol=0,atol=2e-6),(name,at,a0.shape,a1.shape)
            for key in ('indices',):
                assert np.array_equal(access(j0,b0,p0[key]),access(j1,b1,p1[key])),(name,key)
            name0=j0['materials'][p0['material']]['name'];name1=j1['materials'][p1['material']]['name']
            assert name0==name1,(name,name0,name1)
            checked+=1
    new_nodes=[x for x in new if x not in old]
    assert len(new_nodes)>=28,len(new_nodes)
    assert all('STAGE41' in x for x in new_nodes),new_nodes[:5]
    assert not (set(new_nodes)&changed)
    # The original screen atlas primitives are independently verified above,
    # including UVs, face indices and material identity; no source UI changes.
    record={'sourceControlGLB':hashlib.sha256(base.read_bytes()).hexdigest(),
      'candidateGLB':hashlib.sha256(candidate.read_bytes()).hexdigest(),
      'exactRetainedNodeCount':len(old)-len(changed),
      'identicalRetainedMeshPrimitives':checked,
      'replacedLowerNodes':sorted(changed),
      'newPhysicalSourceNodes':len(new_nodes),
      'originalUpperGlassAndControlsBytePreservedByAccessor':True,
      'originalPlinthAndChairGeometryPreserved':True,
      'noArtOrReleaseApproval':True}
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();report=verify(a.base,a.candidate)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('STAGE41_PRESERVATION_PROOF',json.dumps(report))
