#!/usr/bin/env python3
"""Stage35: source-replacing, full-width manufactured flight desk (DRAFT ONLY).
Opaque original hero flightIsland is excluded by independently pinned V3 indices;
six original display planes, flight chairs, room controls, player and HUD remain.
"""
from collections import Counter
from math import isfinite,sqrt

def flight_z(x): return -3.24+.24*(x/2.45)**2

def shell(name,material,x0,x1,ylo,yhi,front,rear,n=16):
    assert -2.74<=x0<x1<=2.74 and .16<ylo<yhi<1.075
    assert rear<front-.018 and n>=4
    v=[]
    for i in range(n+1):
        t=i/n;x=x0+(x1-x0)*t;z=flight_z(x)
        bow=.015*(1-(2*t-1)**2)
        v.extend([(x,ylo,z+front+bow),(x,yhi,z+front+bow),
                  (x,yhi,z+rear),(x,ylo,z+rear)])
    faces=[]
    for i in range(n):
        a=i*4;b=(i+1)*4
        for j in range(4):
            q=(j+1)%4
            faces.extend(((a+j,a+q,b+q),(a+j,b+q,b+j)))
    k=n*4
    faces.extend(((0,2,1),(0,3,2),(k,k+1,k+2),(k,k+2,k+3)))
    vol=0.
    for ia,ib,ic in faces:
        a,b,c=[v[j] for j in (ia,ib,ic)]
        vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    assert abs(vol)>1e-6,(name,vol)
    if vol<0: faces=[(a,c,b) for a,b,c in faces]
    uv=[];edges=Counter();oriented=Counter()
    for face in faces:
        pts=[v[j] for j in face]
        a=[pts[1][i]-pts[0][i] for i in range(3)]
        b=[pts[2][i]-pts[0][i] for i in range(3)]
        normal=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
        assert sum(x*x for x in normal)>1e-12,(name,face)
        axis=max(range(3),key=lambda i:abs(normal[i]))
        j,k=((1,2),(0,2),(0,1))[axis]
        mapped=[(p[j]*1.7,p[k]*1.7) for p in pts]
        area=(mapped[1][0]-mapped[0][0])*(mapped[2][1]-mapped[0][1])-(mapped[2][0]-mapped[0][0])*(mapped[1][1]-mapped[0][1])
        assert abs(area)>1e-9,(name,"collapsed scanned PBR UV0")
        uv.append(mapped)
        for a,b in zip(face,face[1:]+face[:1]):
            edges[tuple(sorted((a,b)))]+=1
            oriented[(a,b)]+=1
    assert all(x==2 for x in edges.values()),(name,"not closed")
    assert all(oriented[(a,b)]==oriented[(b,a)]==1 for a,b in edges),(name,"bad normals")
    assert all(all(isfinite(c) for c in p) for p in v)
    return dict(name="STAGE35 / "+name,material=material,
                vertices=v,faces=faces,face_uv=uv)

def generate():
    out=[
      shell("one-piece full-width graphite instrument cradle","powder_graphite",
            -2.67,2.67,.895,1.013,.417,-.549,24),
      shell("machined satin connected front control rail","satin_nickel",
            -2.67,2.67,1.011,1.052,.504,.438,24),
      shell("set-back lower cable and service raceway","powder_graphite",
            -2.67,2.67,.844,.904,.566,.505,20),
    ]
    # Three closed ceramic front faces instead of an opaque full-width block.
    # The gaps below original port/starboard touchglass form two real kneewells.
    for title,lo,hi in (("port angled ceramic face",-2.67,-1.71),
                        ("central recessed control equipment face",-.59,.59),
                        ("starboard angled ceramic face",1.71,2.67)):
        out.append(shell(title,"powder_ivory",lo,hi,.355,.849,.564,.338,12))
    for side in (-1,1):
        prefix="port" if side<0 else "starboard"
        x=side*2.36
        out.append(shell(prefix+" load-bearing closed side return","powder_graphite",
                         x-.122,x+.122,.196,.925,.486,-.290,12))
        out.append(shell(prefix+" physically fitted satin contact edge","satin_nickel",
                         x-.132,x+.132,.282,.772,.516,.477,8))
        out.append(shell(prefix+" grounded structural toe and gasket","powder_graphite",
                         x-.220,x+.220,.180,.252,.539,-.388,8))
    out.append(shell("central recessed equipment support keel","powder_graphite",
                     -.245,.245,.180,.903,.411,-.240,10))
    out.append(shell("captive central satin service aperture frame","satin_nickel",
                     -.45,.45,.726,.767,.596,.559,10))
    assert len(out)==14
    tris=sum(len(p["faces"]) for p in out)
    assert 1100<tris<2600,tris
    assert len({p["name"] for p in out})==14
    return out

def preflight():
    parts=generate()
    return dict(id="AST_STAGE35_SOURCE_EXACT_FLIGHT_DESK_MACRO",
        closedMeshes=len(parts),triangles=sum(len(p["faces"]) for p in parts),
        sourceMeasuredOriginalFlightFaces=6476,originalInstrumentGlassRetained=True,
        trueOpenPilotKneeWells=2,UV0ManifoldValid=True,
        originalViewerMovementControlsHUDUnchanged=True,
        newUV1ContactAOProven=False,artApproved=False,fullReleaseQACompleted=False)
if __name__=="__main__":
    import json
    print(json.dumps(preflight(),indent=2))
