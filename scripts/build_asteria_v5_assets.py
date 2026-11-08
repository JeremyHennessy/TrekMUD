#!/usr/bin/env python3
"""Build an original Asteria V5 glTF scene from exact, measured V3 model vertices.

Independent color/normal/ORM maps add material response; original art layout and
screen atlas, furniture positions, and one-room topology are preserved exactly.
No third-party geometry, game state or private campaign materials are loaded.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import json, struct, io, math, hashlib, os
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('ASTERIA_V5_SOURCE_DIR',str(ROOT/'_v5_mesh_capture')))
OUT=Path(os.environ.get('ASTERIA_V5_OUT_DIR',str(ROOT/'_site/3d-preview-v5/models')))
OUT.mkdir(exist_ok=True,parents=True)
rng=np.random.default_rng(63542)
def srgb_to_linear(c):
    return np.where(c<=0.04045,c/12.92, ((c+0.055)/1.055)**2.4)
P=np.load(SOURCE/'positions.npy').reshape(-1,3).astype('<f4')
N=np.load(SOURCE/'normals.npy').reshape(-1,3).astype('<f4')
C=np.load(SOURCE/'colors.npy').reshape(-1,3).astype('<f4')
M=np.load(SOURCE/'materials.npy').astype('u1')
UV=np.load(SOURCE/'uv.npy').reshape(-1,2).astype('<f4')
original_triangle_count=len(P)//3
assert original_triangle_count==106988,"Frozen V3 geometry count changed"
# Optional independent art-review scene exclusions. Both use exact measured
# frozen-V3 generator draw-call indices, never proximity or guessed rectangles.
drop_captain=os.environ.get('ASTERIA_V5_EXCLUDE_CAPTAIN_CHAIR')=='1'
drop_command=os.environ.get('ASTERIA_V5_EXCLUDE_COMMAND_SECTION')=='1'
drop_bay=os.environ.get('ASTERIA_V5_EXCLUDE_INLAID_BAY')=='1'
captain_removed=0
command_removed=0
command_spans=[]
bay_removed=0
bay_spans=[]
if drop_bay:
    assert drop_captain and drop_command, 'Inlaid bay only tested alongside source-measured chair and command removal'
if drop_command:
    assert drop_captain, 'New command section is only reviewed with the proven independent hero chair'
if drop_captain or drop_command or drop_bay:
    assert os.environ.get('ASTERIA_V5_CHAIR_WINDING_REPAIR')!='1', (
      'Do not repair old chair faces that are being removed')
    keep=np.ones(original_triangle_count,dtype=bool)
    if drop_captain:
        span=json.loads((SOURCE/'captain-chair-source-span.json').read_text())
        assert span['sourceV3Blob']=='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
        assert span['totalFaces']==original_triangle_count
        start,end=span['firstFaceIncluded'],span['lastFaceExcluded']
        captain_removed=span['captainSeatFaces']
        assert end-start==captain_removed==16272
        assert keep[start:end].all()
        keep[start:end]=False
    if drop_command:
        report=json.loads((SOURCE/'command-section-source-spans.json').read_text())
        assert report['sourceV3Blob']=='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
        assert report['totalFaces']==original_triangle_count
        command_spans=report['ranges']
        assert [r['name'] for r in sorted(command_spans,key=lambda x:x['start'])]==[
            'platform','pylons','trim'],command_spans
        assert len(command_spans)==3
        for segment in command_spans:
            first,last=segment['start'],segment['end']
            assert 0<first<last<original_triangle_count
            assert last-first==segment['faces']
            assert keep[first:last].all(),f"Command segment overlaps another protected segment: {segment}"
            keep[first:last]=False
            command_removed+=segment['faces']
        assert 3000<command_removed<35000
        assert command_removed==report['commandFaces']
    if drop_bay:
        bay=json.loads((SOURCE/'inlaid-bay-source-spans.json').read_text())
        assert bay['sourceV3Blob']=='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
        assert bay['totalFaces']==original_triangle_count
        assert bay['structuralWallSubstrateRetained'] and bay['neighborRibsAndConsolesRetained']
        bay_spans=bay['ranges']
        assert {r['name'] for r in bay_spans}=={
            'wallBayDecor24','ceilingWedge36','ceilingWedge37'}
        for segment in bay_spans:
            first,last=segment['start'],segment['end']
            assert 0<first<last<original_triangle_count
            assert last-first==segment['faces']
            assert keep[first:last].all(),f'Bay cannot remove chair, command or neighboring geometry: {segment}'
            keep[first:last]=False
            bay_removed+=segment['faces']
        assert bay_removed==bay['removedFaces']==62
    def filter_faces(arr):
        shape=arr.shape[1:]
        return arr.reshape((-1,3)+shape)[keep].reshape((-1,)+shape)
    P=filter_faces(P);N=filter_faces(N);C=filter_faces(C)
    M=filter_faces(M);UV=filter_faces(UV)
    assert len(P)//3==original_triangle_count-captain_removed-command_removed-bay_removed
    print('Excluded frozen source face spans: captain',captain_removed,
          'command',command_removed,'remaining',len(P)//3,flush=True)
# Identify exactly the two original forward starfield screen triangles. The PBR
# shader must not reflect ceiling lights off an image meant to depict deep space.
star=(M==7)&(np.abs(P[:,2]+6.06)<.0005)&(np.abs(P[:,0])<=3.101)
assert int(star.sum())==6, f'V3 star-pane geometry drift: {star.sum()} vertices'
M[star]=9
assert len(P)==len(N)==len(C)==len(M)==len(UV)==3*(106988-captain_removed-command_removed-bay_removed)
assert np.isfinite(P).all() and np.isfinite(N).all()
assert len(P)%3==0 and (M.reshape(-1,3)==M.reshape(-1,3)[:,0:1]).all()
print('Exact original V3:',len(P)//3,'triangles',flush=True)
# Optional verified A/B correction for the V3 chair-front shading defect.
# Default OFF: existing V5 outputs remain unchanged. This changes face ordering
# only for the command-chair upholstery whose normals oppose triangle winding.
# Original captured arrays on disk and all vertex coordinates remain untouched.
CHAIR_WINDING_REPAIR=os.environ.get("ASTERIA_V5_CHAIR_WINDING_REPAIR")=="1"
chair_winding_faces_reordered=0
if CHAIR_WINDING_REPAIR:
    tri=P.reshape(-1,3,3)
    n=N.reshape(-1,3,3)
    m=M.reshape(-1,3)
    mid=tri.mean(axis=1)
    near=(np.abs(mid[:,0])<.95)&(mid[:,1]>.45)&(mid[:,1]<2.3)&(np.abs(mid[:,2]-1.2)<.9)
    g=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    g/=np.maximum(1e-12,np.linalg.norm(g,axis=1,keepdims=True))
    sn=n.mean(axis=1)
    sn/=np.maximum(1e-12,np.linalg.norm(sn,axis=1,keepdims=True))
    alignment=np.einsum("ij,ij->i",g,sn)
    repair=(m[:,0]==5)&near&(alignment<-.5)
    chair_winding_faces_reordered=int(repair.sum())
    assert chair_winding_faces_reordered==5136, (
      f"Unexpected chair winding condition: {chair_winding_faces_reordered}; refuse repair")
    for array,dimensions in ((P,3),(N,3),(C,3),(UV,2)):
        face=array.reshape(-1,3,dimensions)
        original=face[repair].copy()
        face[repair]=original[:,[0,2,1],:]
    print('V5 chair winding A/B repair:',chair_winding_faces_reordered,'faces',flush=True)

# Materials correspond to V3's carefully tuned physical set categories.
MATS={
 0:('architectural_accent',.01,.87,'composite'),
 1:('carpet_pile',.0,.96,'carpet'),
 2:('acoustic_wall_shell',.0,.83,'composite'),
 3:('powder_coated_cast',.19,.67,'cast'),
 4:('satin_metal_joinery',.55,.42,'metal'),
 5:('upholstered_furniture',.0,.81,'fabric'),
 6:('asteria_live_instruments',.0,1.,'atlas'),
 7:('smoked_instrument_glass',.12,.22,'glass'),
 8:('diffused_practical_lights',.0,.95,'glow'),
 9:('forward_starfield_unlit',0.,1.,'starfield'),
}

# Pattern maps are low-amplitude microstructure, not a replacement for good geometry.
# Approximate material type using spatially continuous physical surface variations.
S=512
textures={}
for style in ['composite','carpet','cast','metal','fabric','glass','glow']:
    y,x=np.mgrid[0:S,0:S].astype(np.float32)
    fine=rng.normal(0,1,(S,S)).astype(np.float32)
    low=np.asarray(Image.fromarray(np.uint8(np.clip(rng.normal(127,40,(64,64)),0,255))).resize((S,S),Image.Resampling.BICUBIC)).astype(np.float32)
    low=(low-127)/40
    if style=='composite':
        height=low*.28+fine*.17
        albedo=0.965+.012*low+.006*fine
        rough=.84+.025*low
    elif style=='carpet':
        fiber=np.sin(x*2.61+y*.82)*np.cos(x*.97-y*1.45)
        height=low*.2+fiber*.19+fine*.20
        albedo=.935+.006*low+.012*fiber+.005*fine
        rough=.96+.008*low
    elif style=='fabric':
        weave=np.sin(x*2.25)*np.sin(y*1.9)
        height=weave*.30+low*.11+fine*.07
        albedo=.93+.025*weave+.006*low
        rough=.83+.04*weave
    elif style=='metal':
        brushed=np.sin(y*4.77)+np.sin(y*10.12)*.23
        height=brushed*.21+low*.08+fine*.028
        albedo=.98+.008*brushed+.004*low
        rough=.43+.025*low
    elif style=='cast':
        height=low*.13+fine*.15
        albedo=.962+.012*low
        rough=.68+.032*low
    elif style=='glass':
        height=low*.03+fine*.015
        albedo=.986+.006*low
        rough=.24+.02*low
    else:
        height=low*.02+fine*.01
        albedo=.988+.003*low
        rough=.93+.008*low
    # Height derivatives converted to shallow tangent-space normals. Microtexture only.
    dy,dx=np.gradient(height)
    strength={'fabric':.18,'carpet':.08,'metal':.09,'composite':.09,'glass':.018,'cast':.10,'glow':.005}[style]
    nn=np.stack([-dx*strength,-dy*strength,np.ones_like(dx)],axis=2)
    nn/=np.maximum(1e-6,np.linalg.norm(nn,axis=2,keepdims=True))
    ntex=np.uint8(np.clip((nn*.5+.5)*255,0,255))
    al=np.uint8(np.clip(albedo*255,0,255));acol=np.stack([al,al,al,np.full_like(al,255)],axis=2)
    orm=np.stack([np.uint8(np.full_like(al,255)),np.uint8(np.clip(rough*255,0,255)),np.zeros_like(al)],axis=2)
    for suffix,pix in [('base',acol),('normal',ntex),('orm',orm)]:
        ob=io.BytesIO(); Image.fromarray(pix).save(ob,format='PNG',optimize=True)
        textures[(style,suffix)]=ob.getvalue()

buf=bytearray();bufferViews=[];accessors=[];gltfMeshes=[];image_specs=[];texturesSpecs=[];materials=[]

def add_view(raw,target=None):
    pad=(-len(buf))%4
    if pad:buf.extend(bytes(pad))
    offset=len(buf);buf.extend(raw)
    view={'buffer':0,'byteOffset':offset,'byteLength':len(raw)}
    if target:view['target']=target
    bufferViews.append(view)
    return len(bufferViews)-1

def accessor(raw,componentType,count,gltype,minima=None,maxima=None,normalized=None,target=34962):
    view=add_view(raw,target)
    a={'bufferView':view,'componentType':componentType,'count':count,'type':gltype}
    if minima is not None:a['min']=[float(v) for v in minima]
    if maxima is not None:a['max']=[float(v) for v in maxima]
    if normalized is not None:a['normalized']=normalized
    accessors.append(a);return len(accessors)-1

def png_texture(data,repeat=True):
    view=add_view(data)
    image_specs.append({'bufferView':view,'mimeType':'image/png'})
    image_id=len(image_specs)-1
    sampler_idx=0 if repeat else 1
    texturesSpecs.append({'source':image_id,'sampler':sampler_idx})
    return len(texturesSpecs)-1
texmap={}
for st in ['composite','carpet','cast','metal','fabric','glass','glow']:
 for kind in ['base','normal','orm']:
    texmap[(st,kind)]=png_texture(textures[(st,kind)])
texmap[('atlas','base')]=png_texture((SOURCE/'atlas.png').read_bytes(),False)

# A stable world-space texel scale; console UVs remain byte-for-byte original.
def generate_uv(p,n,material):
 if material==6:
  flip=UV[M==6].copy()
  flip[:,1]=1-flip[:,1]  # V3 atlas uploaded flipped in WebGL; glTF uses unflipped image
  return flip
 n=np.abs(n)
 # Dominant plane axis per triangle avoids corrupted texture stretching on geometry.
 f=n.reshape(-1,3,3).mean(axis=1)
 axis=np.argmax(f,axis=1)
 v=np.empty((len(p)//3,3,2),np.float32)
 a=p.reshape(-1,3,3)
 for dim in (0,1,2):
  idx=np.where(axis==dim)[0]
  if not len(idx):continue
  if dim==1:coords=a[idx][:,:,[0,2]]
  elif dim==0:coords=a[idx][:,:,[2,1]]
  else:coords=a[idx][:,:,[0,1]]
  # Real units: tile every .5 m, avoid cartoon-sized texture repeats
  v[idx]=coords*2.1
 return v.reshape(-1,2)

for i in range(10):
 name,metallic,rough,style=MATS[i]
 mask=M==i
 pos=P[mask]
 normal=N[mask]
 color=C[mask]
 uv=generate_uv(pos,normal,i)
 if i!=6:
  # Material texture is near-neutral; vertex colors provide the actual authored palette.
  color=srgb_to_linear(color)
  # Preserve more of the v3 palette response than hard sRGB-to-linear conversion alone.
  color=np.clip(color**.85,0,1)
 else:
  color=np.ones_like(color)
 pos=pos.astype('<f4',copy=False)
 norm=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-7)
 normal=(normal/norm).astype('<f4')
 # Trim color to 8 bit; important for fast loading on desktop and mobile.
 rgba=np.uint8(np.clip(np.round(color*255),0,255))
 attrs={
  'POSITION':accessor(pos.tobytes(),5126,len(pos),'VEC3',pos.min(0),pos.max(0)),
  'NORMAL':accessor(normal.tobytes(),5126,len(pos),'VEC3'),
  'COLOR_0':accessor(rgba.tobytes(),5121,len(pos),'VEC3',normalized=True),
  'TEXCOORD_0':accessor(uv.astype('<f4').tobytes(),5126,len(pos),'VEC2'),
 }
 if style in ('atlas','starfield'):
  m={'name':name,'doubleSided':True,'pbrMetallicRoughness':{
     'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}}
  if style=='atlas':m['pbrMetallicRoughness']['baseColorTexture']={'index':texmap[('atlas','base')]}
 else:
  m={'name':name,'doubleSided':True,
   'pbrMetallicRoughness':{'baseColorTexture':{'index':texmap[(style,'base')]},'metallicFactor':metallic,'roughnessFactor':rough,'metallicRoughnessTexture':{'index':texmap[(style,'orm')]}},
   'normalTexture':{'index':texmap[(style,'normal')],'scale':.45},
   'occlusionTexture':{'index':texmap[(style,'orm')],'strength':.3}}
  if style=='glow':
   m['emissiveFactor']=[.22,.18,.17]
  if style=='glass':m['alphaMode']='OPAQUE'
 materials.append(m)
 gltfMeshes.append({'name':f'V3_{name}_preserved','primitives':[{'attributes':attrs,'material':i,'mode':4}]})
 print(i,name,'vertices',len(pos),'triangles',len(pos)//3,'color',color.mean(axis=0),flush=True)
assert sum(accessors[mesh['primitives'][0]['attributes']['POSITION']]['count'] for mesh in gltfMeshes)==len(P)
manifest={
 'asset':{'version':'2.0','generator':'Asteria V5 exact-V3 geometry and PBR import','copyright':'Original TrekMUD Asteria room'},
 'scene':0,'scenes':[{'nodes':list(range(len(gltfMeshes)))}],
 'nodes':[{'name':mesh['name'],'mesh':i} for i,mesh in enumerate(gltfMeshes)],
 'meshes':gltfMeshes,'materials':materials,'accessors':accessors,'bufferViews':bufferViews,
 'buffers':[{'byteLength':len(buf)}],
 'images':image_specs,'textures':texturesSpecs,
 'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497},{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],
 'extensionsUsed':['KHR_materials_unlit'],
 'extras':{'ship':'USS Asteria','registry':'NCC-63542','roomId':'AST-D01-BRIDGE','source':'git blob 74a154ae62bccb0c16d03c2ecf791a64ab19ce81','originalV3Triangles':original_triangle_count,
          'captainChairRemovedFaces':captain_removed,
          'commandSectionRemovedFaces':command_removed,
          'commandSourceRanges':command_spans,
          'inlaidBayRemovedFaces':bay_removed,
          'inlaidBaySourceRanges':bay_spans,
          'remainingV3Triangles':len(P)//3,
          'physicalSize':[15.1,4.46,13.12], 'simulationWrites':False}
}
assert all(v.get('buffer',0)==0 for v in bufferViews)
manifest['buffers'][0]['byteLength']=len(buf)
js=json.dumps(manifest,separators=(',',':')).encode('utf-8');js+=b' '*((-len(js))%4)
raw=bytes(buf);raw+=bytes((-len(raw))%4)
total=12+8+len(js)+8+len(raw)
header=struct.pack('<4sII',b'glTF',2,total)
glb=header+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(raw),b'BIN\x00')+raw
out=OUT/'asteria-v3-restored-pbr.glb';out.write_bytes(glb)
report={'path':str(out),'sha256':hashlib.sha256(glb).hexdigest(),'bytes':len(glb),'triangles':len(P)//3,'original_triangles':original_triangle_count,
        'captain_chair_source_faces_removed':captain_removed,
        'command_section_source_faces_removed':command_removed,
        'command_source_ranges':command_spans,
        'inlaid_bay_source_faces_removed':bay_removed,
        'inlaid_bay_source_ranges':bay_spans,
        'chair_winding_faces_reordered':chair_winding_faces_reordered,'material_groups':len(MATS),'position_bounds':{'min':P.min(0).tolist(),'max':P.max(0).tolist()},'source_git_blob':'74a154ae62bccb0c16d03c2ecf791a64ab19ce81'}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2))
print('REPORT',json.dumps(report,indent=2),flush=True)