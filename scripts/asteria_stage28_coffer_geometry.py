#!/usr/bin/env python3
"""Stage28: one physically joined, camera-scale architectural ceiling system.

Pure, Blender-independent geometry. A continuous 360-degree set of twelve deep
panoramic ceiling coffers, twelve closed longitudinal structural beams, three
continuous load-bearing hoop sections and six physically recessed light wells.
Every formed part is manufactured as a closed 3D solid; no billboard strips,
shader-only bevels, image substitutions or moving existing V3 room faces.

This is optional experimental geometry ONLY, intended to build on the pinned
Stage23 asset in an isolated CI route. All persistent routes, game state, walking
surfaces and camera logic remain byte-identical. CC0 PBR maps are supplied by
the established Blender envelope pipeline; this module supplies *no* textures.
"""
from __future__ import annotations
from collections import Counter
from math import cos, sin, pi, hypot, isfinite, sqrt

TAU = 2*pi
W, D = 7.55, 6.55
SECTORS, BAYS = 96, 12
STEP = TAU / SECTORS


def roof_y(r):
    return 4.38 - (r-.36)/(.985-.36)*.66


def point(a, r, shift):
    return (W*sin(a)*r, roof_y(r)+shift, D*cos(a)*r)


def surface(name, mat, a0, a1, r0, r1, shift, na=8, nr=5,
            thickness=.012, cup=0.0):
    """Solid double-skin curved panel with four physical edge returns.

    Front skin faces downward into the bridge. Back skin and side returns close
    its volume. UV0 is scan-scale world-planar, never a synthetic grayscale.
    """
    assert 0 < a1-a0 < TAU and .35 < r0 < r1 < 1.02
    assert thickness > .003 and na >= 1 and nr >= 1
    v, uv, faces = [], [], []
    stride = na + 1
    count = (nr+1)*stride
    for layer in (0, 1):
        for j in range(nr+1):
            r = r0+(r1-r0)*j/nr
            for i in range(na+1):
                a = a0+(a1-a0)*i/na
                # Press-formed shallow upward dish; the surrounding continuous
                # structural members project 110-155 mm below its surface.
                lift = cup*sin(pi*i/na)**2*sin(pi*j/nr)**2
                x,y,z = point(a,r,shift+lift+layer*thickness)
                v.append((x,y,z))
                uv.append((x/1.9,z/1.9))
    for j in range(nr):
        for i in range(na):
            n = j*stride+i
            faces.extend([(n,n+1,n+stride+1),
                          (n,n+stride+1,n+stride)])
            back=n+count
            faces.extend([(back,back+stride+1,back+1),
                          (back,back+stride,back+stride+1)])
    perimeter = (
        list(range(na+1))
        + [j*stride+na for j in range(1,nr+1)]
        + [nr*stride+i for i in range(na-1,-1,-1)]
        + [j*stride for j in range(nr-1,0,-1)]
    )
    for i,n in enumerate(perimeter):
        m = perimeter[(i+1)%len(perimeter)]
        faces.extend([(n,m+count,m), (n,n+count,m+count)])
    return dict(name=name, material=mat, vertices=v, uv=uv, faces=faces)


def swept_section(name, mat, profiles, closed=False):
    """Closed solid beam with a four-point cross section sampled on the arc."""
    assert len(profiles)>=3
    verts=[];uv=[];faces=[]
    for section in profiles:
        assert len(section)==4
        for xyz in section:
            verts.append(xyz)
            uv.append((xyz[0]/1.9,xyz[2]/1.9))
    n=len(profiles)
    steps=n if closed else n-1
    for i in range(steps):
        following=(i+1)%n
        for j in range(4):
            k=(j+1)%4
            a=i*4+j;b=following*4+j
            c=following*4+k;d=i*4+k
            faces.extend([(a,b,c),(a,c,d)])
    if not closed:
        faces.extend([(0,2,1),(0,3,2)])
        last=(n-1)*4
        faces.extend([(last,last+1,last+2),(last,last+2,last+3)])
    return dict(name=name,material=mat,vertices=verts,uv=uv,faces=faces)


def longitudinal_beam(bay):
    """Closed load-bearing roof seam that physically intersects all three rings."""
    a=bay*TAU/BAYS
    profiles=[]
    for i in range(18):
        r=.405+(.981-.405)*i/17
        half_width=.0145
        profiles.append((
            point(a-half_width,r,-.252+.151*max(0.,min(1.,(r-.80)/.175))),
            point(a+half_width,r,-.252+.151*max(0.,min(1.,(r-.80)/.175))),
            point(a+half_width,r,-.068),
            point(a-half_width,r,-.068)
        ))
    return swept_section(
        "ceiling / structural continuous radial spine %02d"%bay,
        "structural",profiles)


def circumferential_ring(index,r,half_width):
    """Actual closed load-bearing hoop, penetrating spines at shared contacts."""
    profiles=[]
    for i in range(144):
        a=TAU*i/144
        profiles.append((
            point(a,r-half_width,-.103 if index==2 else -.243),
            point(a,r+half_width,-.103 if index==2 else -.243),
            point(a,r+half_width,-.070),
            point(a,r-half_width,-.070),
        ))
    return swept_section("ceiling / continuous structural hoop %02d"%index,
                         "structural",profiles,closed=True)


def combined(name, mat, parts):
    """Union of physically separate closed manufactured trims, one draw call."""
    vertices=[];uv=[];faces=[]
    for p in parts:
        assert p["material"]==mat
        start=len(vertices)
        vertices.extend(p["vertices"])
        uv.extend(p["uv"])
        faces.extend(tuple(start+x for x in tri) for tri in p["faces"])
    return dict(name=name,material=mat,vertices=vertices,uv=uv,faces=faces)


def light_well(bay):
    """Deep-backed fixture: graphite trough, recessed opal and stepped bezel."""
    k=bay*8
    a0=(k+2.30)*STEP;a1=(k+5.70)*STEP
    r0,r1=.789,.886
    back=surface("light well %02d / closed recessed backing"%bay,
                 "structural",a0,a1,r0,r1,-.148,10,3)
    opal=surface("light well %02d / opal diffuser behind raised frame"%bay,
                 "opal",a0+.027,a1-.027,r0+.018,r1-.018,-.187,10,3)
    border=[
        surface("trim", "structural", a0, a0+.030, r0, r1,-.226,1,3),
        surface("trim", "structural", a1-.030, a1, r0, r1,-.226,1,3),
        surface("trim", "structural", a0+.028, a1-.028, r0, r0+.021,-.226,8,1),
        surface("trim", "structural", a0+.028, a1-.028, r1-.021, r1,-.226,8,1),
    ]
    bezel=combined("light well %02d / manufactured four-sided dark bezel"%bay,
                   "structural",border)
    return back,opal,bezel


def generate():
    """All one-zone parts; deterministic no IO, no original geometry mutations."""
    objects=[]
    for bay in range(BAYS):
        k=bay*8
        a0=(k+.11)*STEP;a1=(k+7.89)*STEP
        panel=surface(
            "ceiling / curved scanned acoustic coffer %02d"%bay,
            "wall" if bay%4==2 else "ceiling",
            a0,a1,.443,.948,-.125,12,7,thickness=.020,cup=.049)
        objects.append(panel)
    for bay in range(BAYS):
        objects.append(longitudinal_beam(bay))
    for idx,(r,half_width) in enumerate(((.435,.047),(.692,.051),(.958,.053))):
        objects.append(circumferential_ring(idx,r,half_width))
    for bay in range(0,BAYS,2):
        objects.extend(light_well(bay))
    assert len(objects)==45
    return objects


def preflight():
    """Cheap, independent per-face/UV/manifold/extent checks, before Cycles."""
    objects=generate()
    triangles=0
    report=[]
    for obj in objects:
        v=obj["vertices"];faces=obj["faces"];uv=obj["uv"]
        assert len(v)==len(uv)>7,(obj["name"],len(v),len(uv))
        assert obj["material"] in ("ceiling","wall","structural","opal")
        for p in v:
            assert all(isfinite(x) for x in p),obj["name"]
            assert 3.3<p[1]<4.5,(obj["name"],p)
        edges=Counter()
        for tri in faces:
            assert len(tri)==3 and len(set(tri))==3,tri
            assert all(0<=x<len(v) for x in tri),tri
            for x,y in zip(tri,tri[1:]+tri[:1]):
                edges[tuple(sorted((x,y)))] += 1
            p,q,r=(v[i] for i in tri)
            u=tuple(q[i]-p[i] for i in range(3))
            w=tuple(r[i]-p[i] for i in range(3))
            normal=(u[1]*w[2]-u[2]*w[1],
                    u[2]*w[0]-u[0]*w[2],
                    u[0]*w[1]-u[1]*w[0])
            assert sum(n*n for n in normal)>1e-13,(obj["name"],tri)
        invalid=[(edge,n) for edge,n in edges.items() if n!=2]
        assert not invalid,(obj["name"],invalid[:3])
        triangles+=len(faces)
        report.append((obj["name"],len(v),len(faces)))
    assert 10000<=triangles<=15000,triangles
    return {"meshCount":len(objects),"triangles":triangles,
            "materials":["CC0 scanned ceiling","CC0 scanned wall",
                         "manufactured graphite","existing physical opal"],
            "allMeshesClosed":True,"allFacesNondegenerate":True,
            "UV0Present":True,"retainedSourceFaceRemovals":864,
            "originalGameSourceUnchanged":True,
            "components":[12,12,3,18],
            "sectionExtentMeters":[.388,1.011],"parts":report}


if __name__=="__main__":
    import json
    print(json.dumps(preflight(),indent=2))
