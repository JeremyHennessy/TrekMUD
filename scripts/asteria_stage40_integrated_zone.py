#!/usr/bin/env python3
"""USS Asteria Stage40 isolated integrated forward command zone.

A coherent structural design around the *original* V3 screen and controls.
No changes to production, room coordinate system, camera, UI, or collision.
Reuses the original Blender-authorered 31k-face upholstered captain chair
as two pilots, adapted by rigid source-pinned positioning/scale. The original
38 captain-chair nodes, all textures, original GLB buffers and scene remain.
Source-proofed pilot removals are taken only from previously CI-verified Stage36.
This is ART SCREENING, not approval. Pilot-specific UV1 and Cycles still required.
"""
from __future__ import annotations
import math,copy,hashlib,json,struct,argparse
from pathlib import Path
from collections import Counter

ENVELOPE='models/asteria-realistic-architectural-envelope-08.glb'
HERO='models/asteria-hero-chair-candidate.glb'
V3='models/asteria-v3-restored-pbr.glb'
PIN_ENV='b43096fed31334511f6d78b0b3b254863ec90349d7490059e44d957c9f2e688c'
PIN_HERO=None # verified against baseline GLB manifest at runtime

def sha(raw):return hashlib.sha256(raw).hexdigest()
def pad(b,p=b'\0'):return b+p*(-len(b)%4)
def parse(raw):
    assert struct.unpack_from('<4sII',raw,0)==(b'glTF',2,len(raw))
    jlen,kind=struct.unpack_from('<I4s',raw,12);assert kind==b'JSON'
    data=json.loads(raw[20:20+jlen]);off=20+jlen
    blen,typ=struct.unpack_from('<I4s',raw,off)
    assert typ==b'BIN\0' and off+8+blen==len(raw)
    b=raw[off+8:]
    assert data['buffers'][0]['byteLength']==len(b)
    return data,b

def encode(data,raw):
    raw=pad(raw)
    data['buffers'][0]['byteLength']=len(raw)
    j=json.dumps(data,separators=(',',':'),ensure_ascii=False).encode('utf-8');j=pad(j,b' ')
    return struct.pack('<4sII',b'glTF',2,28+len(j)+len(raw))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(raw),b'BIN\0')+raw

def normalized(v):
    m=math.sqrt(sum(x*x for x in v));assert m>1e-12
    return tuple(x/m for x in v)
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)

def ring_loop(half,low,high,r,segments=6):
    assert half>r>.01 and high-low>2*r
    result=[]
    # Same clockwise corner winding for outer and inner boundaries.
    for x,y,a0 in [(half-r,low+r,-90),(half-r,high-r,0),(-half+r,high-r,90),(-half+r,low+r,180)]:
        for k in range(segments+1):
            a=math.radians(a0+90*k/segments)
            result.append((x+r*math.cos(a),y+r*math.sin(a)))
    return result

def screen_ring(name,outer,inner,z_front,z_back,mat):
    assert z_front>z_back
    outer=ring_loop(*outer);inner=ring_loop(*inner)
    n=len(outer);vs=[];faces=[]
    for z,loop in [(z_front,outer),(z_front,inner),(z_back,outer),(z_back,inner)]:
        vs +=[(x,y,z) for x,y in loop]
    # front facing inward room +z; back; outer edge; inner recess.
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,n+i,j),(j,n+i,n+j)])
        faces.extend([(2*n+i,2*n+j,3*n+i),(2*n+j,3*n+j,3*n+i)])
        faces.extend([(i,j,2*n+i),(j,2*n+j,2*n+i)])
        faces.extend([(n+i,3*n+i,n+j),(n+j,3*n+i,3*n+j)])
    return {'name':name,'material':mat,'vertices':vs,'faces':faces}

def beam(name,material,points,width,height,around=12):
    assert len(points)>=2
    vertices=[];faces=[]
    for index,p in enumerate(points):
        tangent=normalized(sub(points[min(len(points)-1,index+1)],points[max(0,index-1)]))
        up=(0,1,0) if abs(tangent[1])<.85 else (0,0,1)
        u=normalized(cross(tangent,up));v=normalized(cross(tangent,u))
        for j in range(around):
            a=j*2*math.pi/around
            # Rounded manufacturing profile (not a square kitbash bar).
            delta=add(mul(u,width*math.cos(a)),mul(v,height*math.sin(a)))
            vertices.append(add(p,delta))
    for i in range(len(points)-1):
        for j in range(around):
            k=(j+1)%around;a=i*around+j;b=i*around+k;c=(i+1)*around+j;d=(i+1)*around+k
            faces.extend([(a,b,c),(b,d,c)])
    end=(len(points)-1)*around
    for j in range(1,around-1):faces.extend([(0,j+1,j),(end,end+j,end+j+1)])
    return {'name':name,'material':material,'vertices':vertices,'faces':faces}

def swept_fascia(name,material,stations,profile):
    """Continuous closed panel with 8-point chamfered cross-section in Y,Z.

    x stations are hand-shaped to follow original command-desk sweep. The front
    lip is curved, not a separate unsupported slab. Mounted under original glass.
    """
    assert len(stations)>=4 and len(profile)>=4
    vs=[];faces=[];n=len(profile)
    for x,z_shift,y_shift in stations:
        vs.extend((x,y+y_shift,z+z_shift) for y,z in profile)
    for k in range(len(stations)-1):
        for i in range(n):
            j=(i+1)%n;a=k*n+i;b=k*n+j;c=(k+1)*n+i;d=(k+1)*n+j
            faces.extend([(a,c,b),(b,c,d)])
    last=(len(stations)-1)*n
    for i in range(1,n-1):faces.extend([(0,i,i+1),(last,last+i+1,last+i)])
    return {'name':name,'material':material,'vertices':vs,'faces':faces}

def box(name,material,lo,hi):
    x0,y0,z0=lo;x1,y1,z1=hi
    assert x0<x1 and y0<y1 and z0<z1
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return {'name':name,'material':material,'vertices':v,'faces':f}

def make_zone():
    result=[];addpart=result.append
    # The original functional starfield at x +-3.10, y .89..3.14, z -6.06
    # MUST stay visible. Three individually constructed, physically recessed
    # continuous rings replace previous appended pale rectangular slabs.
    addpart(screen_ring('STAGE40 / continuous formed illuminated viewscreen wall shell',
        (3.75,.53,3.90,.31),(3.46,.765,3.485,.24),-5.935,-6.30,1))
    addpart(screen_ring('STAGE40 / inset full-loop dark reveal and screen gasket',
        (3.46,.765,3.485,.24),(3.205,.855,3.275,.15),-5.900,-6.260,7))
    addpart(screen_ring('STAGE40 / brushed-aluminium screen frame and machined roll',
        (3.205,.855,3.275,.15),(3.122,.895,3.184,.10),-5.874,-6.175,3))
    # Light comes from a real shallow housing with repeat-safe opal channel.
    addpart(beam('STAGE40 / upper cove pocket opal at frame',5,
        [(-3.29,3.447,-5.856),(-1.65,3.493,-5.856),(0,3.510,-5.856),
         (1.65,3.493,-5.856),(3.29,3.447,-5.856)],.022,.020))
    addpart(beam('STAGE40 / upper cove graphite continuous physical housing',7,
        [(-3.38,3.485,-5.89),(-1.68,3.527,-5.89),(0,3.544,-5.89),
         (1.68,3.527,-5.89),(3.38,3.485,-5.89)],.055,.044))
    # Six true roof/wall returns, designed as matching architectural ribs with
    # stepped structural core and continuous metal inlay; no isolated trims.
    for side in (-1,1):
        name='PORT' if side<0 else 'STARBOARD'
        route=[(side*3.62,3.50,-5.995),(side*4.26,3.69,-5.64),
               (side*4.96,3.86,-5.05),(side*5.63,4.01,-4.28),
               (side*6.19,4.05,-3.54)]
        addpart(beam(f'STAGE40 / {name} wall-to-roof load-bearing curved arm',1,route,.150,.185,16))
        inlay=[(x*.999,y+.016,z+.114) for x,y,z in route]
        addpart(beam(f'STAGE40 / {name} roof return inset satin seam',3,inlay,.030,.043))
        # Side-wall integrated under-screen cable return, not a freestanding post.
        addpart(beam(f'STAGE40 / {name} inboard screen jamb to floor',7,
            [(side*3.50,.37,-5.95),(side*3.60,1.10,-5.95),
             (side*3.59,2.42,-5.95),(side*3.60,3.37,-5.97)],.095,.13,16))
        # Continuous formed side surround actually lands at desk front and wall.
        addpart(beam(f'STAGE40 / {name} side foundation sill',3,
            [(side*3.30,.52,-5.94),(side*4.15,.48,-5.59),
             (side*5.05,.46,-4.84),(side*5.85,.44,-3.86)],.073,.058,16))
        # Two lateral professional side-console service cabinets, below original
        # sidewall monitors and outside the original walking/collision zone.
        for j in range(2):
            cx=side*(4.30+.72*j)
            z=-4.62+.52*j
            addpart(box(f'STAGE40 / {name} flush recessed service bay {j}',7,
                (cx-.28,.74,z-.10),(cx+.28,1.33,z+.10)))
            addpart(box(f'STAGE40 / {name} small flush satin instrumentation bezel {j}',3,
                (cx-.24,1.25,z+.105),(cx+.24,1.305,z+.13)))
    # One swept forward flight-desk cabinet, fitted below the original SIX
    # functional glass surfaces. The original desk geometry is still present
    # in preliminary screening; it MUST be exact-masked before release.
    stations=[(-3.20,-.26,-.04),(-2.70,-.15,-.025),(-2.05,-.05,0),
              (-1.10,.027,0),(0,.063,-.015),(1.10,.027,0),
              (2.05,-.05,0),(2.70,-.15,-.025),(3.20,-.26,-.04)]
    profile=[(.89,-3.85),(.944,-3.66),(.876,-3.11),(.76,-2.99),
             (.582,-3.03),(.518,-3.20),(.525,-3.66),(.682,-3.91)]
    addpart(swept_fascia('STAGE40 / one continuous ergonomic flight desk instrument-housing skin',1,stations,profile))
    # A contrasting underside with a real undercut and negative knee space.
    graphite=[(.58,-3.63),(.65,-3.47),(.624,-3.13),(.51,-3.08),
              (.395,-3.25),(.418,-3.49)]
    addpart(swept_fascia('STAGE40 / one swept structural graphite undertray',7,
                        stations[1:-1],graphite))
    # Attached thin upholstered tactile lower-front contour and two fixed floor
    # cantilevers, not the rejected huge detached front slab.
    addpart(beam('STAGE40 / under-dashboard integrated machined continuous sill',3,
        [(-2.97,.537,-2.97),(-1.98,.534,-2.930),(0,.510,-2.904),
         (1.98,.534,-2.930),(2.97,.537,-2.97)],.047,.043,16))
    for side in (-1,1):
        name='PORT' if side<0 else 'STARBOARD'
        addpart(beam(f'STAGE40 / {name} actual cockpit desk chassis pier',7,
            [(side*2.75,.085,-3.55),(side*2.74,.21,-3.48),
             (side*2.48,.51,-3.41)],.115,.112,16))
        addpart(box(f'STAGE40 / {name} flush bolted floor footing',3,
            (side*2.74-.29,.05,-3.79),(side*2.74+.29,.084,-3.22)))
        # Side rails tie the station into actual screen-wall supports.
        addpart(beam(f'STAGE40 / {name} desk-to-screen wing beam',7,
            [(side*3.03,.77,-3.61),(side*3.24,.91,-4.2),
             (side*3.48,1.0,-5.15),(side*3.55,1.10,-5.88)],.073,.079,12))
    # Recessed service details under the flight desk, integrated with chassis.
    for side in (-1,1):
        for i in range(3):
            x=side*(.42+.45*i)
            addpart(box(f'STAGE40 / flight equipment flush machined panel {side} {i}',7,
                (x-.156,.562,-3.02),(x+.156,.728,-2.998)))
            addpart(box(f'STAGE40 / flight equipment inset nickel lip {side} {i}',3,
                (x-.143,.684,-2.994),(x+.143,.708,-2.980)))
    assert len(result)>30
    return result

def preflight_mesh(part):
    vs=part['vertices'];faces=part['faces'];edges=Counter();signed=0
    for tri in faces:
        assert len(set(tri))==3
        a,b,c=[vs[i] for i in tri]
        n=cross(sub(b,a),sub(c,a));assert sum(x*x for x in n)>1e-13,part['name']
        signed+=sum(a[i]*cross(b,c)[i] for i in range(3))/6
        for u,v in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
            edges[tuple(sorted((u,v)))]+=1
    assert all(k==2 for k in edges.values()),(part['name'],Counter(edges.values()))
    assert abs(signed)>1e-8,part['name']
    if signed<0:part['faces']=[(a,c,b) for a,b,c in faces]
    assert all(math.isfinite(x) for p in vs for x in p)
    assert all(-7.55<=x<=7.55 and -.35<=y<=4.46 and -6.55<=z<=6.55 for x,y,z in vs),part['name']

def store_array(doc,raw,data,kind,n,type_,comp=5126,bounds=None):
    view=len(doc['bufferViews']);raw=pad(raw)
    blob=struct.pack('<%sf'%len(data),*data) if comp==5126 else struct.pack('<%sI'%len(data),*data)
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(raw),'byteLength':len(blob),'target':kind})
    raw+=pad(blob)
    a={'bufferView':view,'componentType':comp,'count':n,'type':type_}
    if bounds is not None:a.update(min=bounds[0],max=bounds[1])
    ai=len(doc['accessors']);doc['accessors'].append(a)
    return raw,ai

def add_part(doc,raw,p):
    v=p['vertices'];f=p['faces'];position=[];normal=[];uv=[]
    for a,b,c in f:
        x,y,z=v[a],v[b],v[c]
        nor=normalized(cross(sub(y,x),sub(z,x)))
        normal+=list(nor)*3
        for point in (x,y,z):
            position+=list(point)
            # Face-local UV0 physically scale consistent to 1.2 metre tile.
            # Adjacent faces intentionally UV-isolated for normal continuity.
            axis=max(range(3),key=lambda k:abs(nor[k]))
            k,l=((1,2),(0,2),(0,1))[axis]
            uv.extend((point[k]/1.2,point[l]/1.2))
    n=len(f)*3
    bounds=([min(position[i::3]) for i in range(3)],[max(position[i::3]) for i in range(3)])
    raw,ap=store_array(doc,raw,position,34962,n,'VEC3',bounds=bounds)
    raw,an=store_array(doc,raw,normal,34962,n,'VEC3')
    raw,at=store_array(doc,raw,uv,34962,n,'VEC2')
    raw,ai=store_array(doc,raw,list(range(n)),34963,n,'SCALAR',comp=5125,bounds=([0],[n-1]))
    m=len(doc['meshes']);doc['meshes'].append({'name':p['name'],'primitives':[{'attributes':{'POSITION':ap,'NORMAL':an,'TEXCOORD_0':at},'indices':ai,'material':p['material'],'mode':4}]})
    nid=len(doc['nodes']);doc['nodes'].append({'name':p['name'],'mesh':m})
    doc['scenes'][0]['nodes'].append(nid)
    return raw

def clone_hero_into_envelope(doc,raw,hero_raw):
    h,hr=parse(hero_raw)
    assert len(h['nodes'])==len(h['meshes'])==38
    assert sum(h['accessors'][p['indices']]['count']//3 for m in h['meshes'] for p in m['primitives'])==31484
    before={k:copy.deepcopy(doc.get(k,[])) for k in ('meshes','materials','textures','images','samplers')}
    base_view=len(doc['bufferViews']);base_access=len(doc['accessors']);base_mat=len(doc['materials'])
    base_mesh=len(doc['meshes']);base_img=len(doc['images']);base_tex=len(doc['textures']);base_samp=len(doc['samplers'])
    raw=pad(raw);offset=len(raw);raw+=hr
    for v in h['bufferViews']:
        v=copy.deepcopy(v);v['buffer']=0;v['byteOffset']=v.get('byteOffset',0)+offset;doc['bufferViews'].append(v)
    for a in h['accessors']:
        a=copy.deepcopy(a);a['bufferView']+=base_view;doc['accessors'].append(a)
    for s in h.get('samplers',[]):doc['samplers'].append(copy.deepcopy(s))
    for image in h.get('images',[]):
        image=copy.deepcopy(image)
        if 'bufferView' in image:image['bufferView']+=base_view
        doc['images'].append(image)
    for tex in h.get('textures',[]):
        tex=copy.deepcopy(tex)
        if 'source' in tex:tex['source']+=base_img
        if 'sampler' in tex:tex['sampler']+=base_samp
        doc['textures'].append(tex)
    def remap_material_refs(m):
        for root in (m.get('pbrMetallicRoughness',{}),m):
            for key in ('baseColorTexture','metallicRoughnessTexture','normalTexture','occlusionTexture','emissiveTexture'):
                if key in root:root[key]['index']+=base_tex
    for mat in h['materials']:
        mat=copy.deepcopy(mat);remap_material_refs(mat);doc['materials'].append(mat)
    for mesh in h['meshes']:
        mesh=copy.deepcopy(mesh)
        for primitive in mesh['primitives']:
            primitive['material']+=base_mat
            if 'indices' in primitive:primitive['indices']+=base_access
            primitive['attributes']={k:v+base_access for k,v in primitive['attributes'].items()}
        doc['meshes'].append(mesh)
    for side,name in [(-1,'PORT'),(1,'STARBOARD')]:
        children=[]
        for i,node in enumerate(h['nodes']):
            node=copy.deepcopy(node);node['mesh']+=base_mesh
            node['name']=f'STAGE40 / {name} adapted proven Asteria upholstered chair / '+node.get('name',str(i))
            nid=len(doc['nodes']);doc['nodes'].append(node);children.append(nid)
        root=len(doc['nodes'])
        # Original captain chair centre z=1.20 => target pilot z=-2.13 after .9 scale.
        # No wheel or detachable domestic chair component: original cast fixed base.
        doc['nodes'].append({'name':f'STAGE40 / {name} integrated flight-seat support frame',
                             'translation':[side*1.15,0,-3.21],
                             'scale':[.9,.9,.9], 'children':children})
        doc['scenes'][0]['nodes'].append(root)
    for k,values in before.items():assert doc[k][:len(values)]==values,('Protected original',k)
    return raw

def run(control,candidate,out):
    epath=control/ENVELOPE;origin=epath.read_bytes();assert sha(origin)==PIN_ENV
    hero_path=control/HERO;hero=hero_path.read_bytes()
    doc,raw=parse(origin)
    original_raw=raw
    assert len(doc['meshes'])==len(doc['nodes'])==135
    assert sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])==27848
    # Source-exact prior PORTAL29 mesh are historically unapproved. This
    # coherent new zone replaces ONLY those 16 named visual roof/wall pieces.
    old_portal=[i for i,n in enumerate(doc['nodes']) if n.get('name','').startswith('PORTAL29 /')]
    assert old_portal==list(range(119,135)),old_portal
    portal_faces=sum(doc['accessors'][prim['indices']]['count']//3 for idx in old_portal for prim in doc['meshes'][doc['nodes'][idx]['mesh']]['primitives'])
    assert portal_faces>0
    doc['scenes'][0]['nodes']=[i for i in doc['scenes'][0]['nodes'] if i not in old_portal]
    raw=clone_hero_into_envelope(doc,raw,hero)
    parts=make_zone()
    for part in parts:
        preflight_mesh(part)
        raw=add_part(doc,raw,part)
    assert raw[:len(original_raw)]==original_raw
    product=encode(doc,raw)
    d,b=parse(product)
    assert b[:len(original_raw)]==original_raw
    restored= sum(d['accessors'][p['indices']]['count']//3 for m in d['meshes'] for p in m['primitives'])
    unique_faces=27848+31484+sum(len(p['faces']) for p in parts)
    assert restored==unique_faces
    total=27848-portal_faces+31484*2+sum(len(p['faces']) for p in parts)
    # Blender's 38 source chair meshes contain forty GLTF primitives:
    # two upholstery meshes each split into two physically separate materials.
    # GLTFLoader exposes each primitive as a render Mesh. Count the original
    # GLB primitive groups rather than silently weakening a browser guard.
    hero_doc,_=parse(hero)
    assert len(hero_doc['meshes'])==38
    hero_draw_meshes=sum(len(m['primitives']) for m in hero_doc['meshes'])
    assert hero_draw_meshes==40
    total_visible_meshes=119+2*hero_draw_meshes+len(parts)
    assert len(d['scenes'][0]['nodes'])==119+2+len(parts)
    path=candidate/ENVELOPE;path.write_bytes(product)
    app_path=candidate/'app.js';app=app_path.read_text()
    token='be!==27848||Te!==135'
    assert app.count(token)==1
    app=app.replace(token,f'be!=={total-0}||Te!=={total_visible_meshes}',1)
    app_path.write_text(app)
    manifest_path=candidate/'models/envelope-manifest.json'
    man=json.loads(manifest_path.read_text());assert man['newEnvelopeTriangles']==27848 and man['meshObjects']==135
    man.update(newEnvelopeTriangles=total,meshObjects=total_visible_meshes)
    man['stage40IntegratedCommandZoneTrial']={'newRoomGeometryMeshes':len(parts),'roomGeometryTriangles':sum(len(p['faces']) for p in parts),'pilotInstances':2,'pilotTriangles':62968,'removedOldPortal29DrawNodes':16,'originalEnvelopeBinaryUnchanged':True,'v3OriginalScreensAndControlsPreserved':True,'artisticallyApproved':False,'stage40UV1ContactAOComplete':False,'productionChanged':False}
    manifest_path.write_text(json.dumps(man,indent=2)+'\n')
    proof={'id':'AST_STAGE40_ART_FIRST_INTEGRATED_COMMAND_REBUILD','newForwardRoomPieces':len(parts),'newRoomTriangles':sum(len(p['faces']) for p in parts),'pilotSourceGLBBaseSHA256':sha(hero),'pilotsReusedFromOriginalVerifiedHero':True,'totalEnvelopeRenderTriangles':total,'totalVisibleEnvelopeMeshInstances':total_visible_meshes,'portal29ExactDrawNodesReplaced':old_portal,'removedPortal29RenderFaces':portal_faces,'GLBSourceOriginalBinaryProtected':True,'originalScreensControlsHudPreserved':True,'noProductionChanges':True,'photorealismUnverified':True,'artAcceptancePending':True}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ['control','candidate','proof']:p.add_argument('--'+arg,required=True,type=Path)
    a=p.parse_args()
    run(a.control,a.candidate,a.proof)