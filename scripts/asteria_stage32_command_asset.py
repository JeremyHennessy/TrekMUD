#!/usr/bin/env python3
"""Stage32 experimental formed command support, NOT approved art. Frozen screens/controls are retained."""
from __future__ import annotations
from math import sin,cos,pi,isfinite
from collections import Counter

def volume(v,f):
    s=0.
    for i,j,k in f:
        a,b,c=(v[n] for n in (i,j,k))
        s+=a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
    return s/6

def loft(P,rings,n=40):
    v=[]
    for y,w,front,rear in rings:
        assert .275<=y<=1.11 and .055<w<.42 and front>.015 and rear>.015
        for j in range(n):
            a=2*pi*j/n;c,s=cos(a),sin(a)
            t=(abs(c)**6+abs(s)**6)**(-1/6)
            v.append(P(w*c*t,y,(rear if s>=0 else front)*s*t))
    f=[]
    for r in range(len(rings)-1):
        for j in range(n):
            nxt=(j+1)%n;a,b=r*n+j,r*n+nxt
            c,d=(r+1)*n+j,(r+1)*n+nxt
            f.extend(((a,b,c),(b,d,c)))
    for j in range(1,n-1):
        f.append((0,j+1,j))
        end=(len(rings)-1)*n
        f.append((end,end+j,end+j+1))
    if volume(v,f)<0:f=[(a,c,b) for a,b,c in f]
    return v,f

def validate(v,f):
    assert volume(v,f)>.0001
    assert all(isfinite(x) for p in v for x in p)
    count=Counter();directed=Counter()
    for face in f:
        assert len(set(face))==3
        for a,b in zip(face,face[1:]+face[:1]):
            count[tuple(sorted((a,b)))]+=1;directed[(a,b)]+=1
    assert all(n==2 for n in count.values())
    assert all(directed[(a,b)]==directed[(b,a)]==1 for a,b in count)
    uvs=[]
    for face in f:
        a,b,c=(v[i] for i in face)
        d=[b[i]-a[i] for i in range(3)];e=[c[i]-a[i] for i in range(3)]
        n=(d[1]*e[2]-d[2]*e[1],d[2]*e[0]-d[0]*e[2],d[0]*e[1]-d[1]*e[0])
        axis=max(range(3),key=lambda i:abs(n[i]))
        ix,iy=((1,2),(0,2),(0,1))[axis]
        tri=[(p[ix]/1.35,p[iy]/1.35) for p in (a,b,c)]
        area=abs((tri[1][0]-tri[0][0])*(tri[2][1]-tri[0][1])-(tri[2][0]-tri[0][0])*(tri[1][1]-tri[0][1]))
        assert area>1e-9,('Collapsed Stage32 UV0',face)
        uvs.append(tri)
    return uvs

def generate(side):
    assert side in (-1,1)
    x0,z0=side*1.27,.58
    ang=side*.24;ca,sa=cos(ang),sin(ang)
    def P(x,y,z):return (x0+x*ca-z*sa,y,z0+x*sa+z*ca)
    specs=(
      ('seated graphite floor socket','powder_graphite',
       ((.282,.200,.182,.184),(.315,.207,.190,.193),(.362,.177,.159,.164)),0.0),
      ('integral tapered center spine','powder_graphite',
       ((.317,.145,.124,.132),(.405,.165,.139,.148),(.625,.171,.157,.173),
        (.790,.200,.196,.216),(.888,.250,.252,.266),(.963,.306,.317,.334)),0.0),
      ('physically attached shallow instrument cradle','powder_graphite',
       ((.914,.296,.302,.314),(.964,.346,.347,.363),
        (1.072,.354,.361,.367),(1.103,.345,.351,.355)),0.0),
      ('small inlaid metal service cassette','satin_nickel',
       ((.488,.097,.027,.027),(.514,.116,.028,.028),
        (.714,.132,.029,.030),(.753,.122,.028,.028)),.155),
      ('short ivory composite upper shield','powder_ivory',
       ((.780,.113,.024,.024),(.803,.139,.024,.024),
        (.852,.167,.024,.024),(.868,.165,.024,.024)),.215),
    )
    results=[]
    for name,mat,rings,dz in specs:
        v,f=loft(lambda x,y,z,dz=dz:P(x,y,z+dz),rings)
        uv=validate(v,f)
        assert all(-2.2<x<2.2 and .275<=y<1.12 and -.5<z<1.5 for x,y,z in v)
        results.append(dict(name=f'STAGE32 / command {side} / {name}',
                            material=mat,vertices=v,faces=f,uv=uv))
    return results

def build(side,model,pipe,mats):
    for part in generate(side):
        ob=model(part['name'],part['vertices'],part['faces'],mats[part['material']])
        uv=ob.data.uv_layers.new(name='STAGE32_FACE_METRIC_PBR_UV0')
        assert len(ob.data.polygons)==len(part['uv'])
        for face,tri in zip(ob.data.polygons,part['uv']):
            for loop,xy in zip(face.loop_indices,tri):uv.data[loop].uv=xy
    x0,z0=side*1.27,.58;ang=side*.24;ca,sa=cos(ang),sin(ang)
    def P(x,y,z):return (x0+x*ca-z*sa,y,z0+x*sa+z*ca)
    # A single slender structural member either side, embedded in cradle and foot.
    for sign in (-1,1):
        pipe(f'STAGE32 / command {side} / mounted satin shear brace {sign}',
             [P(sign*.155,.335,.005),P(sign*.182,.535,.012),
              P(sign*.216,.746,.023),P(sign*.302,.930,.045)],
             .017,mats['satin_nickel'],segments=4)
    pipe(f'STAGE32 / command {side} / bronze cradle seam',
         [P(-.298+i*.596/20,.938,.370) for i in range(21)],
         .009,mats['rose_bronze'])
    for sign in (-1,1):
        pipe(f'STAGE32 / command {side} / flush service joint {sign}',
             [P(sign*.105,.530,.190),P(sign*.120,.730,.190)],
             .004,mats['console_gasket'])

def preflight():
    parts=generate(-1)+generate(1)
    return dict(stage='ASTERIA_STAGE32_CAST_SPINE_CRADLE',
                meshCount=len(parts),triangles=sum(len(p['faces']) for p in parts),
                manifold=True,uv0PerFaceNondegenerate=True,
                originalDisplayAndPlayerCodeUnchanged=True,
                UV1ContactAOBaked=False,artApproved=False)
if __name__=='__main__':
    import json
    print(json.dumps(preflight(),indent=2))
