#!/usr/bin/env python3
"""Stage39 ART-SCREEN ONLY: replace rejected domestic wood with joined aircraft seat shells
around exactly retained Poly Haven CC0 leather cushions. Not a release gate.
"""
import argparse,copy,hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from asteria_stage38_real_pilot_merge import parse,encode

STAGE38="5497a1ad7d7e2ad15e16158e306e126dd4f5ce20c98a0b96b5f744092d50204b"
MASKED_V3="27b9622ebbef0e9d31cebb4a3baaf027df344839f27d1511580fbd9224819dee"
parts=[]
def solid(name,verts,faces,material):
 v=np.asarray(verts,dtype=np.float64);f=np.asarray(faces,dtype=np.int64)
 edges=Counter()
 for a,b,c in f:
  for x,y in ((a,b),(b,c),(c,a)):edges[tuple(sorted((int(x),int(y))))]+=1
 assert len(v)>20 and len(f)>20 and all(x==2 for x in edges.values())
 tri=v[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
 assert np.all(np.linalg.norm(n,axis=1)>1e-10)
 vol=np.einsum('ij,ij->i',tri[:,0],n).sum()/6
 assert abs(vol)>1e-5
 if vol<0:f=f[:,[0,2,1]];n=-n
 vn=np.zeros_like(v)
 for j in range(3):np.add.at(vn,f[:,j],n)
 length=np.linalg.norm(vn,axis=1);assert np.all(length>1e-9)
 vn/=length[:,None]
 uv=np.column_stack((v[:,0]*1.7+v[:,2]*.47+.5,v[:,1]*1.6+v[:,2]*.33+.5))
 parts.append((name,v.astype('<f4'),f.astype('<u4'),vn.astype('<f4'),uv.astype('<f4'),material))
def lathe(name,rings,material,N=64):
 v=[]
 for y,w,front,back,xc,zc in rings:
  for k in range(N):
   a=2*math.pi*k/N
   v.append((xc+w*math.cos(a),y,zc+(front-back)/2+(front+back)*math.sin(a)/2))
 f=[]
 for r in range(len(rings)-1):
  for k in range(N):
   a=r*N+k;b=r*N+(k+1)%N;c=(r+1)*N+k;d=(r+1)*N+(k+1)%N
   f.extend(((a,c,b),(b,c,d)))
 for k in range(1,N-1):
  f.append((0,k,k+1));t=(len(rings)-1)*N;f.append((t,t+k+1,t+k))
 solid(name,v,f,material)
def generate():
 N=48;R=2*(N+1);v=[];f=[]
 profile=[(.384,.333,-.392,.170),(.460,.382,-.434,.205),(.580,.425,-.465,.195),
 (.720,.430,-.512,.196),(.860,.407,-.571,.176),(.974,.380,-.626,.151),
 (1.067,.344,-.652,.108)]
 for y,w,rear,reach in profile:
  for inner in (0,1):
   for k in range(N+1):
    a=-math.pi/2+math.pi*k/N
    v.append(((w-.026*inner)*math.sin(a),y,
              rear+.026*inner+reach*(1-math.cos(a))-.019*math.cos(2*a)*(y-.30)))
 for j in range(len(profile)-1):
  for side in (0,1):
   for k in range(N):
    a=j*R+side*(N+1)+k;b=a+1;c=a+R;d=c+1
    f.extend(((a,c,b),(b,c,d)) if side==0 else ((a,b,c),(b,d,c)))
  for k in (0,N):
   a=j*R+k;b=j*R+N+1+k;c=a+R;d=b+R;f.extend(((a,b,c),(b,d,c)))
 for j in (0,len(profile)-1):
  for k in range(N):
   a=j*R+k;b=a+1;c=j*R+N+1+k;d=c+1
   f.extend(((a,b,c),(b,d,c)) if j==0 else ((a,c,b),(b,c,d)))
 solid('joined upholstered curved shell',v,f,1)
 lathe('continuous bucket under-pan',[
 (.270,.310,.33,.32,0,-.025),(.290,.383,.41,.42,0,-.015),
 (.327,.424,.44,.45,0,-.015),(.372,.431,.44,.46,0,-.015),
 (.410,.408,.408,.42,0,-.017),(.448,.376,.379,.386,0,-.018)],7)
 lathe('internally landed rear shear backbone',[
 (.259,.095,.106,.104,0,-.158),(.364,.120,.094,.118,0,-.188),
 (.467,.142,.073,.088,0,-.342),(.585,.115,.051,.071,0,-.448),
 (.710,.089,.040,.066,0,-.503)],7,48)
 for side in (-1,1):
  lathe('continuous arm cockpit '+str(side),[
   (.515,.035,.110,.113,side*.366,-.125),(.563,.043,.117,.119,side*.377,-.100),
   (.623,.054,.193,.184,side*.399,0),(.681,.066,.256,.205,side*.408,.046),
   (.717,.066,.259,.206,side*.409,.056),(.738,.054,.240,.205,side*.407,.064)],7,48)
 lathe('joined satin hydraulic seat neck',[
 (.025,.205,.185,.185,0,-.015),(.045,.220,.201,.201,0,-.015),
 (.066,.203,.185,.185,0,-.015),(.089,.125,.133,.128,0,-.015),
 (.118,.096,.094,.090,0,-.015),(.174,.086,.090,.089,0,-.015),
 (.270,.112,.114,.113,0,-.015),(.319,.155,.168,.167,0,-.015)],3)
 lathe('closed broad floor shoe',[
 (.012,.272,.28,.27,0,-.015),(.026,.290,.300,.300,0,-.015),
 (.048,.284,.292,.292,0,-.015),(.060,.237,.255,.254,0,-.015)],7)
 assert len(parts)==7 and sum(len(p[2]) for p in parts)==5568
def run(site,receipt):
 generate();model=site/'models/asteria-realistic-architectural-envelope-08.glb'
 b=model.read_bytes()
 assert hashlib.sha256(b).hexdigest()==STAGE38
 assert hashlib.sha256((site/'models/asteria-v3-restored-pbr.glb').read_bytes()).hexdigest()==MASKED_V3
 doc,raw=parse(b)
 assert len(doc['meshes'])==136 and len(doc['nodes'])==137
 src=doc['meshes'][135]['primitives']
 assert [p['material'] for p in src]==[10,11]
 assert [doc['accessors'][p['indices']]['count']//3 for p in src]==[5608,3308]
 assert doc['nodes'][135]['translation']==[-1.15,0,-2.13]
 assert doc['nodes'][136]['translation']==[1.15,0,-2.13]
 assert doc['nodes'][135]['rotation']==doc['nodes'][136]['rotation']==[0,1,0,0]
 orig=hashlib.sha256(json.dumps(doc['meshes'][:135],sort_keys=True).encode()).hexdigest()
 doc['meshes'][135]['primitives']=[copy.deepcopy(src[1])]
 def accessor(arr,typ,kind,bounds=False):
  raw.extend(b'\0'*(-len(raw)%4));off=len(raw);raw.extend(arr.tobytes())
  i=len(doc['bufferViews']);doc['bufferViews'].append(dict(buffer=0,byteOffset=off,byteLength=arr.nbytes))
  a=dict(bufferView=i,componentType=typ,count=len(arr),type=kind)
  if bounds:a.update(min=arr.min(0).astype(float).tolist(),max=arr.max(0).astype(float).tolist())
  j=len(doc['accessors']);doc['accessors'].append(a);return j
 for name,v,f,n,uv,mat in parts:
  attrs=dict(POSITION=accessor(v,5126,'VEC3',True),NORMAL=accessor(n,5126,'VEC3'),
             TEXCOORD_0=accessor(uv,5126,'VEC2'))
  indices=accessor(f.reshape(-1),5125,'SCALAR')
  doc['meshes'][135]['primitives'].append(dict(attributes=attrs,indices=indices,material=mat,
                                               mode=4,extras={'Stage39':name}))
 assert hashlib.sha256(json.dumps(doc['meshes'][:135],sort_keys=True).encode()).hexdigest()==orig
 doc['meshes'][135]['name']='STAGE39 CC0 leather in continuous cockpit composite'
 for side,n in zip((-1,1),doc['nodes'][-2:]):
  assert n['translation']==[side*1.15,0,-2.13]
  n['name']='STAGE39 isolated cockpit seat '+str(side)
 after=encode(doc,raw);verified,_=parse(after)
 assert len(verified['meshes'][135]['primitives'])==8
 count=2*(3308+sum(len(p[2]) for p in parts));objects=2*(1+len(parts))
 assert (count,objects)==(17752,16)
 env=site/'models/envelope-manifest.json';meta=json.loads(env.read_text())
 trial=meta['stage38ScanPilotTrial']
 assert (meta['newEnvelopeTriangles'],meta['meshObjects'])==(45680,139)
 assert trial['licensedScannedFabricProven'] and trial['newTriangles']==17832
 meta['newEnvelopeTriangles']=27848+count;meta['meshObjects']=135+objects
 trial['newTriangles']=count;trial['newMeshInstances']=objects
 trial.update(stage39LeatherOnly=True,domesticWoodRemoved=True,artApproved=False,
              newUV1OrGIProven=False)
 meta['stage39CompositeTrial']=dict(originalV3RemovedFaces=32600,
   scannedLeatherFaces=6616,woodFacesRemoved=11216,
   structuralFaces=2*sum(len(p[2]) for p in parts),source='https://polyhaven.com/a/modern_arm_chair_01',
   license='https://polyhaven.com/license',artApproved=False,fullGatePassed=False)
 apppath=site/'app.js';app=apppath.read_text();guard='be!==45680||Te!==139'
 assert app.count(guard)==1 and app.count('Se!==106988-Be-ft-174-864-204-96-32600')==1
 app=app.replace(guard,f'be!=={27848+count}||Te!=={135+objects}',1)
 model.write_bytes(after);env.write_text(json.dumps(meta,indent=2)+'\n');apppath.write_text(app)
 proof=dict(id='STAGE39_ART_FIRST_ONLY',inputSHA256=STAGE38,
   outputSHA256=hashlib.sha256(after).hexdigest(),sourceOriginalFaceRemoved=32600,
   woodTrianglesRemoved=11216,scannedLeatherFacesRetained=6616,
   closedNewStructuralFaces=2*sum(len(p[2]) for p in parts),
   newUV1ContactAO=False,cyclesControlAB=False,artApproved=False,deployed=False)
 receipt.parent.mkdir(parents=True,exist_ok=True)
 receipt.write_text(json.dumps(proof,indent=2)+'\n')
 print('STAGE39_ART_FIRST_COMPOSITE',json.dumps(proof),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True)
 p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();run(a.site,a.receipt)
