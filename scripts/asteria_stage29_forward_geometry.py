#!/usr/bin/env python3
"""Optional forward-command portal on the exact original Asteria screen geometry.

Sixteen closed real supports, sidewall returns and roof landings. The frozen V3
starbase screen picture, player movement, HUD, source and production never change.
Only provenance-checked old trim boxes/posts are excluded in the opt-in build.
"""
from math import isfinite, hypot
from collections import Counter

def per_face_scanned_uv(vertices, faces):
    """Metric PBR UV0 for face corners; retains shared 3D mesh topology.

    Front/top/raked planes cannot use one 2D mapping at shared corner vertices.
    Blender glTF exporter splits only the UV seams, not the authored 3D faces.
    """
    texel_meters=1.9
    mapped=[]
    for face in faces:
        a,b,c=(vertices[k] for k in face)
        ab=tuple(b[i]-a[i] for i in range(3))
        ac=tuple(c[i]-a[i] for i in range(3))
        normal=(ab[1]*ac[2]-ab[2]*ac[1],
                ab[2]*ac[0]-ab[0]*ac[2],
                ab[0]*ac[1]-ab[1]*ac[0])
        horizontal=hypot(normal[0],normal[2])
        if abs(normal[1])>=horizontal:
            uv=[(p[0]/texel_meters,p[2]/texel_meters) for p in (a,b,c)]
        else:
            # Vertically aligned, metric texel scale on raked wall facets.
            tangent=(normal[2]/horizontal,-normal[0]/horizontal)
            uv=[((p[0]*tangent[0]+p[2]*tangent[1])/texel_meters,
                 p[1]/texel_meters) for p in (a,b,c)]
        twice_area=abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-
                       (uv[2][0]-uv[0][0])*(uv[1][1]-uv[0][1]))
        assert twice_area>1e-10, ('Degenerate face UV0',face,normal,uv)
        mapped.append(tuple(uv))
    return mapped

def box(name, material, x0, x1, y0, y1, z0, z1):
    assert x0<x1 and y0<y1 and z0<z1,name
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
       (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),
       (0,1,5),(0,5,4),(1,2,6),(1,6,5),
       (2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return dict(name=name,material=material,vertices=v,faces=f,
                face_uv=per_face_scanned_uv(v,f))

def wing(name,material,side,inset=False):
    if not inset:
        footprint=[(3.45,-6.18),(3.82,-6.10),(4.82,-4.65),(4.63,-4.49)]
        lo,hi=.58,3.75
    else:
        footprint=[(3.40,-5.985),(3.65,-5.975),(4.61,-4.56),(4.43,-4.53)]
        lo,hi=.80,3.59
    if side<0:footprint=[(-x,z) for x,z in reversed(footprint)]
    v=[(x,lo,z) for x,z in footprint]+[(x,hi,z) for x,z in footprint]
    f=[(3,1,0),(3,2,1),(4,5,7),(5,6,7)]
    for i in range(4):
        j=(i+1)%4
        f.extend([(i,j,j+4),(i,j+4,i+4)])
    # Consistently outward-wound, including mirrored port side.
    f=[(a,c,b) for a,b,c in f]
    return dict(name=name,material=material,vertices=v,faces=f,
                face_uv=per_face_scanned_uv(v,f))

def generate():
    """Starfield and screen visible at x±3.10, y .89–3.14 and z -6.06."""
    out=[
      box("screen portal / continuous upper CC0 structural load beam","wall",-3.73,3.73,3.245,3.80,-6.39,-6.022),
      box("screen portal / lower continuous PBR fascia","wall",-3.73,3.73,.36,.865,-6.39,-6.018),
      box("screen portal / port full-depth side pier","wall",-3.74,-3.128,.64,3.78,-6.38,-5.99),
      box("screen portal / starboard full-depth side pier","wall",3.128,3.74,.64,3.78,-6.38,-5.99),
      box("screen portal / recessed metal upper seal","structural",-3.18,3.18,3.183,3.235,-6.18,-6.008),
      box("screen portal / recessed metal lower seal","structural",-3.18,3.18,.86,.887,-6.18,-6.012),
    ]
    for side,word in ((-1,"port"),(1,"starboard")):
        out.append(wing(word+" wall / connected full-height raked shell","wall",side))
        out.append(wing(word+" wall / inset continuous scanned-PBR panel","ceiling",side,True))
        out.append(box(word+" wall / real crown structural tie","structural",
            -4.72 if side<0 else 3.45,-3.40 if side<0 else 4.72,3.58,3.78,-6.16,-4.50))
        out.append(box(word+" wall / continuous floor plinth landing","structural",
            -4.69 if side<0 else 3.48,-3.45 if side<0 else 4.69,.49,.60,-6.14,-4.50))
    out.extend([
       box("screen roof / uninterrupted upper crown return","ceiling",-3.83,3.83,3.79,3.87,-6.40,-5.89),
       box("screen roof / recessed upper graphite reveal","structural",-3.37,3.37,3.76,3.82,-6.085,-5.93)
    ])
    assert len(out)==16,len(out)
    return out

def preflight():
    parts=generate();names=set();triangles=0
    for ob in parts:
        assert ob['name'] not in names,ob['name']
        names.add(ob['name'])
        assert ob['material'] in ('wall','ceiling','structural')
        v=ob['vertices'];f=ob['faces']
        assert len(v)==8 and len(ob['face_uv'])==len(f)==12
        assert all(all(isfinite(n) for n in p) for p in v)
        assert all(abs(p[0])>=3.12 or p[1]<.89 or p[1]>3.14 for p in v),ob['name']
        edges=Counter()
        for face, face_uv in zip(f,ob['face_uv']):
            assert len(face_uv)==3 and all(all(isfinite(n) for n in u) for u in face_uv)
            twice_area=abs((face_uv[1][0]-face_uv[0][0])*(face_uv[2][1]-face_uv[0][1]) -
                           (face_uv[2][0]-face_uv[0][0])*(face_uv[1][1]-face_uv[0][1]))
            assert twice_area>1e-10,(ob['name'],'UV0 collapsed',face)
            assert len(set(face))==3 and all(0<=i<len(v) for i in face)
            for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))]+=1
            a,b,c=(v[i] for i in face)
            q=[b[i]-a[i] for i in range(3)]
            r=[c[i]-a[i] for i in range(3)]
            cross=(q[1]*r[2]-q[2]*r[1],q[2]*r[0]-q[0]*r[2],q[0]*r[1]-q[1]*r[0])
            assert sum(n*n for n in cross)>1e-12,(ob['name'],face)
        assert len(edges)==18 and all(count==2 for count in edges.values()),ob['name']
        triangles+=len(f)
    assert len(parts)==16 and triangles==192
    return {'id':'ASTERIA_STAGE29_SOURCE_FIT_FORWARD_PORTAL',
      'meshCount':16,'triangles':192,'allMeshesClosed':True,'UV0Present':True,
      'UV0PerFaceLoopMapped':True,'UV0DegenerateTriangles':0,'UV0NondegenerateTriangles':192,
      'originalScreenAndStarfieldRetained':True,'sourceFaceRemovalRequiresIndependentCapture':True,
      'noGameOrControlsWrites':True,'pbrScan':'Poly Haven CC0 unchanged',
      'ownerArtApproved':False}

if __name__=='__main__':
    import json
    print(json.dumps(preflight(),indent=2))
