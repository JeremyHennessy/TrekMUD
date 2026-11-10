#!/usr/bin/env python3
"""Fail-closed exported Stage33 glTF geometry and Cycles UV1 AO proof.
Only a command-art engineering check, not full scene/release approval.
"""
from __future__ import annotations
import argparse,json,struct
from pathlib import Path
import numpy as np

def load(path):
    raw=path.read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<II',raw,4)==(2,len(raw))
    size,typ=struct.unpack_from('<I4s',raw,12)
    assert typ==b'JSON'
    doc=json.loads(raw[20:20+size])
    n,typ=struct.unpack_from('<I4s',raw,20+size)
    assert typ==bytes((66,73,78,0))
    binary=raw[28+size:28+size+n]
    assert len(binary)==n
    return doc,binary

def read(doc,binary,index):
    acc=doc['accessors'][index]
    view=doc['bufferViews'][acc['bufferView']]
    dtype=np.dtype({5126:'<f4',5121:'u1',5123:'<u2',5125:'<u4'}[acc['componentType']])
    cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[acc['type']]
    width=cols*dtype.itemsize
    stride=view.get('byteStride',width)
    start=view.get('byteOffset',0)+acc.get('byteOffset',0)
    end=start+(acc['count']-1)*stride+width
    assert stride>=width and end<=len(binary)
    return np.ndarray(shape=(acc['count'],cols),dtype=dtype,buffer=binary,
                      offset=start,strides=(stride,dtype.itemsize)).copy()

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--glb',required=True,type=Path)
    a.add_argument('--report',required=True,type=Path)
    a.add_argument('--require-contact-ao',action='store_true',help='Fail if exported UV1 AO is not bound for all 14 Stage33 parts')
    args=a.parse_args()
    doc,binary=load(args.glb)
    meshes=0
    triangles=0
    cells=set()
    materials=set()
    ao_parts=0
    for mesh in doc['meshes']:
        if not mesh['name'].startswith('STAGE33 / command '):
            continue
        meshes+=1
        assert len(mesh['primitives'])==1
        p=mesh['primitives'][0]
        attrs=p['attributes']
        assert p.get('mode',4)==4 and all(k in attrs for k in
               ('POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1'))
        mat=doc['materials'][p['material']]
        materials.add(mat['name'])
        ao=mat.get('occlusionTexture',{})
        if ao:
            assert ao.get('texCoord')==1,('Stage33 AO not mapped to UV1',mesh['name'])
            ao_parts+=1
        assert 'pbrMetallicRoughness' in mat and 'normalTexture' in mat
        xyz=read(doc,binary,attrs['POSITION'])
        normal=read(doc,binary,attrs['NORMAL'])
        uv0=read(doc,binary,attrs['TEXCOORD_0'])
        uv1=read(doc,binary,attrs['TEXCOORD_1'])
        assert len(xyz)==len(normal)==len(uv0)==len(uv1)
        assert np.isfinite(xyz).all() and np.isfinite(normal).all()
        assert (np.linalg.norm(normal,axis=1)>.8).all()
        indices=(read(doc,binary,p['indices']).ravel()
                 if 'indices' in p else np.arange(len(xyz)))
        assert len(indices)%3==0 and int(indices.max())<len(xyz)
        for attr in (uv0,uv1):
            assert np.isfinite(attr).all()
            t=attr[indices].reshape(-1,3,2)
            edge1=t[:,1]-t[:,0]
            edge2=t[:,2]-t[:,0]
            area=edge1[:,0]*edge2[:,1]-edge1[:,1]*edge2[:,0]
            assert (np.abs(area)>1e-9).all(),('UV0 or UV1 degenerate',mesh['name'])
        centers=uv1[indices].reshape(-1,3,2).mean(axis=1)
        cr=np.floor(centers*30).astype(int)
        assert ((cr>=0)&(cr<30)).all(),('UV1 out of atlas',mesh['name'])
        for col,row in cr:
            xy=(int(col),int(row))
            assert xy not in cells,('overlapping Stage33 AO triangle atlas cell',xy)
            cells.add(xy)
        triangles+=len(indices)//3
    assert meshes==14 and triangles==840 and len(cells)==840,(meshes,triangles,len(cells))
    assert len(materials)==3,materials
    assert ao_parts in (0,14),('Partial Stage33 local AO would be invalid',ao_parts)
    if args.require_contact_ao:assert ao_parts==14,('Missing real baked Stage33 AO',ao_parts)
    assert len(doc.get('images',[]))>=1
    receipt={'id':'STAGE33_GENUINE_CYCLES_AO_EXPORTED_UV1_VALIDATION',
             'meshCount':meshes,'triangleCount':triangles,
             'nonoverlappingUv1Triangles':len(cells),'distinctAOMaterials':len(materials),
             'glTFUV1OcclusionBound':ao_parts==14,
             'contactAORequiredForThisRun':bool(args.require_contact_ao),
             'normalTextureRetained':True,
             'licensedMaterialsMustStillBeChecked':True,
             'fullIndirectGI':False,'ownerArtApproved':False}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(receipt,indent=2)+'\n')
    print('STAGE33_EXPORTED_UV1_AO_PASS',json.dumps(receipt),flush=True)

if __name__=='__main__':main()
