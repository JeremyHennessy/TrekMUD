#!/usr/bin/env python3
"""Stage36 NO-DEPLOY: append both real pilot-seat assemblies to pinned envelope.

Original 135 meshes, 27,848 triangles, scans, AO maps, all original glTF
materials and entire prior binary buffer remain byte-for-byte intact.
New unscanned upholstery proxy materials explicitly BLOCK full art acceptance.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from pathlib import Path
from asteria_stage36_pilot_hero import generate,preflight

ENVELOPE='models/asteria-realistic-architectural-envelope-08.glb'
PIN='b43096fed31334511f6d78b0b3b254863ec90349d7490059e44d957c9f2e688c'
APP_PIN='3a85cd7f60bb7523ff2f52d414de9be6e9c4b671a6b1a1c14e8ea73ee03c3baa'

def sha(b):return hashlib.sha256(b).hexdigest()
def pad(b):return b+b'\0'*(-len(b)%4)
def parse(b):
    assert struct.unpack_from('<4sII',b,0)==(b'glTF',2,len(b))
    n,typ=struct.unpack_from('<I4s',b,12)
    assert typ==b'JSON'
    doc=json.loads(b[20:20+n]);off=20+n
    n,typ=struct.unpack_from('<I4s',b,off)
    assert typ==b'BIN\x00' and off+8+n==len(b)
    raw=b[off+8:]
    assert doc['buffers'][0]['byteLength']==len(raw)
    return doc,raw
def encode(doc,raw):
    js=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode()
    js+=b' '*(-len(js)%4);raw=pad(raw)
    return (struct.pack('<4sII',b'glTF',2,28+len(js)+len(raw))+
            struct.pack('<I4s',len(js),b'JSON')+js+
            struct.pack('<I4s',len(raw),b'BIN\x00')+raw)
def count_faces(doc):
    return sum(doc['accessors'][p['indices']]['count']//3
               for m in doc['meshes'] for p in m['primitives'])
def add_data(doc,raw,packed,target):
    packed=pad(packed)
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(raw),
        'byteLength':len(packed),'target':target})
    return raw+packed,len(doc['bufferViews'])-1
def access(doc,view,component,n,kind,bounds=None):
    a={'bufferView':view,'componentType':component,'count':n,'type':kind}
    if bounds is not None:a['min'],a['max']=bounds
    doc['accessors'].append(a)
    return len(doc['accessors'])-1

def splice(control,candidate,out):
    original=(control/ENVELOPE).read_bytes()
    assert sha(original)==PIN
    assert sha((control/'app.js').read_bytes())==APP_PIN
    doc,raw=parse(original)
    assert len(doc['meshes'])==len(doc['nodes'])==135 and count_faces(doc)==27848
    assert len(doc['scenes'])==1 and doc['scene']==0
    assert len(doc['scenes'][0]['nodes'])==135 and len(doc['buffers'])==1
    assert doc['materials'][1]['name']=='Architecture / original 112 exterior shell and capped edges / P'
    assert doc['materials'][3]['name']=='Asteria / captured satin trim'
    assert doc['materials'][7]['name']=='ZONE20 / engineered matte graphite hardware'
    original_json={k:json.dumps(doc[k],sort_keys=True) for k in
        ('meshes','nodes','materials','images','textures','samplers','bufferViews','accessors')}
    original_binary=raw
    # New private QA-colored PBR materials are NOT claimed as scanned. Must
    # replace with proven licensed CC0 velour and baked UV1 before release.
    proxy={'velour':([.38,.255,.34,1],.94,0),
           'velour_alt':([.49,.36,.43,1],.90,0),
           'gasket':([.11,.12,.145,1],.83,0)}
    materials={'graphite':7,'nickel':3}
    for name,(rgba,rough,metal) in proxy.items():
        materials[name]=len(doc['materials'])
        doc['materials'].append({'name':'STAGE36 / UNSCANNED QA-ONLY '+name,
            'pbrMetallicRoughness':{'baseColorFactor':rgba,
                'roughnessFactor':rough,'metallicFactor':metal},
            'doubleSided':False})
    parts=generate()
    assert len(parts)==46
    added=0;names=[]
    for part in parts:
        verts=part['vertices'];faces=part['faces'];uvs=part['face_uv']
        assert len(faces)==len(uvs) and part['material'] in materials
        position=[];normals=[];tex=[]
        for face,uv in zip(faces,uvs):
            a,b,c=(verts[i] for i in face)
            u=[b[k]-a[k] for k in range(3)]
            v=[c[k]-a[k] for k in range(3)]
            normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            mag=math.sqrt(sum(x*x for x in normal))
            assert mag>1e-10
            for p,coords in zip((a,b,c),uv):
                assert all(math.isfinite(x) for x in (*p,*coords))
                position.extend(p)
                normals.extend(x/mag for x in normal)
                tex.extend(coords)
        n=len(faces)*3
        views=[]
        for values in (position,normals,tex):
            raw,view=add_data(doc,raw,struct.pack('<%sf'%len(values),*values),34962)
            views.append(view)
        raw,index_view=add_data(doc,raw,struct.pack('<%sI'%n,*range(n)),34963)
        bounds=([min(position[k::3]) for k in range(3)],
                [max(position[k::3]) for k in range(3)])
        ap=access(doc,views[0],5126,n,'VEC3',bounds)
        an=access(doc,views[1],5126,n,'VEC3')
        au=access(doc,views[2],5126,n,'VEC2')
        ai=access(doc,index_view,5125,n,'SCALAR',([0],[n-1]))
        mesh_id=len(doc['meshes']);name=part['name']
        doc['meshes'].append({'name':name,'primitives':[{
            'attributes':{'POSITION':ap,'NORMAL':an,'TEXCOORD_0':au},
            'indices':ai,'material':materials[part['material']],'mode':4}]})
        node=len(doc['nodes'])
        doc['nodes'].append({'mesh':mesh_id,'name':name})
        doc['scenes'][0]['nodes'].append(node)
        names.append(name);added+=len(faces)
    assert added==preflight()['triangles']==6984
    assert count_faces(doc)==34832 and len(doc['meshes'])==len(doc['nodes'])==181
    assert raw[:len(original_binary)]==original_binary
    for key,old in original_json.items():
        assert json.dumps(doc[key][:len(json.loads(old))],sort_keys=True)==old,('Protected GLB',key)
    doc['buffers'][0]['byteLength']=len(raw)
    product=encode(doc,raw)
    assert count_faces(parse(product)[0])==34832
    (candidate/ENVELOPE).write_bytes(product)
    appfile=candidate/'app.js';app=appfile.read_text()
    token='be!==27848||Te!==135'
    assert app.count(token)==1
    appfile.write_text(app.replace(token,'be!==34832||Te!==181',1))
    meta_file=candidate/'models/envelope-manifest.json'
    meta=json.loads(meta_file.read_text())
    assert meta['newEnvelopeTriangles']==27848 and meta['meshObjects']==135
    meta.update(newEnvelopeTriangles=34832,meshObjects=181)
    meta['stage36PilotArtOnly']={
        'originalEnvelopeSHA256':PIN,'newMeshes':46,'newTriangles':added,
        'meshNames':names,'licensedScannedFabricProven':False,
        'newUV1OrGIProven':False,'artApproved':False,'releaseApproved':False}
    meta_file.write_text(json.dumps(meta,indent=2)+'\n')
    proof={'id':'AST_STAGE36_MATCHING_PILOT_SEAT_MACRO_TRIAL',
        'baseEnvelopeSHA256':PIN,'candidateEnvelopeSHA256':sha(product),
        'original135MeshesAndBinaryPreserved':True,'originalScansRetained':True,
        'newPilotParts':46,'newPilotTriangles':added,
        'oldPilotSourceFacesToRemove':32600,
        'sourceManifoldAndUV0':True,'fabricProxiesNotScanned':True,
        'newUV1AndGIProven':False,'artApproved':False,
        'productionChanged':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(proof,indent=2)+'\n')
    print('STAGE36_TWIN_PILOT_ENVELOPE_SPLICE',json.dumps(proof),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('control','candidate','proof'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args()
    splice(a.control,a.candidate,a.proof)
