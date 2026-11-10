#!/usr/bin/env python3
"""Isolated Asteria command-island Stage31: manufactured lofted consoles.

Blender-free geometry preflight; Blender writer passed as a callback. Not
approved for production. Protect screen images, walking, room and HUD.
"""
from __future__ import annotations
from collections import Counter
from math import cos,sin,pi,isfinite

def volume(v,f):
    t=0.
    for i,j,k in f:
        a,b,c=v[i],v[j],v[k]
        t+=a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0])
    return t/6.

def loft(P,rings,n=32):
    v=[]
    for y,w,front,rear in rings:
        assert y>.20 and w>.045 and front>.05 and rear>.05
        for j in range(n):
            a=2*pi*j/n;c=cos(a);s=sin(a)
            squircle=(abs(c)**4+abs(s)**4)**(-.25)
            v.append(P(w*c*squircle,y,(rear if s>=0 else front)*s*squircle))
    f=[]
    for r in range(len(rings)-1):
        for i in range(n):
            j=(i+1)%n;a=r*n+i;b=r*n+j
            c=(r+1)*n+i;d=(r+1)*n+j
            f.extend(((a,b,c),(b,d,c)))
    for i in range(1,n-1):
        f.append((0,i+1,i))
        end=(len(rings)-1)*n
        f.append((end,end+i,end+i+1))
    if volume(v,f)<0:f=[(a,c,b) for a,b,c in f]
    return v,f

def proof(v,f):
    assert volume(v,f)>1e-4 and all(isfinite(x) for p in v for x in p)
    undirected=Counter();directed=Counter()
    for face in f:
        assert len(set(face))==3
        for a,b in zip(face,face[1:]+face[:1]):
            undirected[tuple(sorted((a,b)))]+=1;directed[(a,b)]+=1
    assert all(n==2 for n in undirected.values())
    assert all(directed[(a,b)]==directed[(b,a)]==1 for a,b in undirected)
    return len(f)

def face_uv(v,f):
    result=[]
    for face in f:
        a,b,c=(v[i] for i in face)
        d=[b[k]-a[k] for k in range(3)];e=[c[k]-a[k] for k in range(3)]
        n=(d[1]*e[2]-d[2]*e[1],d[2]*e[0]-d[0]*e[2],d[0]*e[1]-d[1]*e[0])
        index=max(range(3),key=lambda k:abs(n[k]))
        i,j=((1,2),(0,2),(0,1))[index]
        uv=tuple((p[i]/1.9,p[j]/1.9) for p in (a,b,c))
        area=abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[2][0]-uv[0][0])*(uv[1][1]-uv[0][1]))
        assert area>1.e-10,("Collapsed Stage31 UV0",face)
        result.append(uv)
    return result

def generate(side):
    """Full-depth support openings; real thin top and closed load-bearing forks."""
    assert side in (-1,1)
    x0=side*1.27;z0=.58;a=side*.24;c=cos(a);s=sin(a)
    def P(x,y,z):return (x0+x*c-z*s,y,z0+x*s+z*c)
    parts=[]
    specs=(
       ("thin curved ivory instrument shell","powder_ivory",
        ((.904,.315,.302,.312),(.949,.385,.371,.393),
         (1.035,.402,.389,.400),(1.105,.367,.365,.377)),0,0,0),
       ("swept dark underside of instrument cradle","powder_graphite",
        ((.820,.280,.270,.289),(.865,.340,.325,.349),
         (.945,.382,.370,.385)),0,0,0),
       ("port load-bearing fork","powder_ivory",
        ((.285,.080,.082,.100),(.360,.089,.095,.109),
         (.565,.081,.110,.111),(.768,.085,.115,.120),
         (.892,.104,.126,.142)),-.292,.120,-.19),
       ("starboard load-bearing fork","powder_ivory",
        ((.285,.080,.082,.100),(.360,.089,.095,.109),
         (.565,.081,.110,.111),(.768,.085,.115,.120),
         (.892,.104,.126,.142)),.292,.120,-.19),
       ("deep recessed structural keel","powder_graphite",
        ((.288,.075,.065,.082),(.355,.091,.075,.095),
         (.570,.086,.073,.095),(.745,.095,.080,.113),
         (.875,.128,.102,.125)),0,-.270,.24),
    )
    for label,material,rings,dx,dz,slope in specs:
        def local(x,y,z,dx=dx,dz=dz,slope=slope):
            return P(x+dx,y,z+dz+slope*(y-.285))
        vertices,faces=loft(local,rings)
        assert proof(vertices,faces)>130
        uv=face_uv(vertices,faces)
        assert all(-2.2<x<2.2 and .25<y<1.14 and -.2<z<1.45 for x,y,z in vertices)
        parts.append(dict(name=f"STAGE31 / command {side} / {label}",
                          material=material,vertices=vertices,faces=faces,face_uv=uv))
    return parts

def build(side,model,mats):
    for part in generate(side):
        obj=model(part["name"],part["vertices"],part["faces"],mats[part["material"]])
        layer=obj.data.uv_layers.new(name="STAGE31_METRIC_PBR_UV0")
        assert len(obj.data.polygons)==len(part["face_uv"])
        for poly,uv in zip(obj.data.polygons,part["face_uv"]):
            for li,xy in zip(poly.loop_indices,uv):layer.data[li].uv=xy

def preflight():
    meshes=generate(-1)+generate(1)
    return dict(id="ASTERIA_STAGE31_COMMAND_ISLAND",meshCount=len(meshes),
                sourceTriangles=sum(len(m["faces"]) for m in meshes),
                actualOpenPhysicalSupportWell=True,
                watertight=True,UV0SourceNondegenerate=True,
                preserveOriginalScreens=True,artApproved=False)
if __name__=="__main__":
    import json
    print(json.dumps(preflight(),indent=2))
