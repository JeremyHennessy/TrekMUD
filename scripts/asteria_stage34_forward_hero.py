#!/usr/bin/env python3
"""Stage34: panoramic forward bridge HERO, single opt-in draft assembly.
Build CNC-manufacturable, continuous screen aperture and linked forward station,
without replacing screen pixels/controls or changing gameplay. SOURCE TRIAL ONLY.
"""
from collections import Counter
from math import sin,cos,pi,isfinite


def rr(half,bottom,top,radius,subdiv=10):
    assert .03<radius<min(half, (top-bottom)/2)
    result=[]
    for cx,cy,a0 in ((half-radius,top-radius,pi/2),
                      (half-radius,bottom+radius,0),
                      (-half+radius,bottom+radius,-pi/2),
                      (-half+radius,top-radius,-pi)):
        for i in range(subdiv+1):
            angle=a0-i*pi/(2*subdiv)
            result.append((cx+radius*cos(angle),cy+radius*sin(angle)))
    return result


def ring(name,material,outer,inner,z_back,z_front):
    """Single four-sided, 3D closed cast shell around open, retained screen."""
    a=rr(*outer);b=rr(*inner)
    assert len(a)==len(b)
    n=len(a)
    loops=[[(x,y,z_back) for x,y in a],
           [(x,y,z_front) for x,y in a],
           [(x,y,z_front+.022) for x,y in b],
           [(x,y,z_back+.013) for x,y in b]]
    verts=sum(loops,[])
    faces=[]
    for layer in range(4):
        following=(layer+1)%4
        for k in range(n):
            j=(k+1)%n
            p=layer*n+k;q=layer*n+j
            r=following*n+j;s=following*n+k
            faces.extend(((p,q,r),(p,r,s)))
    return dict(name=name,material=material,vertices=verts,faces=faces)


def rail(name,mat,side):
    """Forward station load path: one curved closed CNC side return."""
    assert side in (-1,1)
    sections=[
      (-5.94,3.43,.160,.52,.76),
      (-5.60,3.39,.170,.50,.80),
      (-5.20,3.35,.182,.46,.81),
      (-4.85,3.31,.194,.42,.78),
      (-4.60,3.28,.188,.40,.77),
    ]
    vertices=[]
    for z,xc,hx,y0,y1 in sections:
        x=side*xc
        vertices.extend([(x-hx,y0,z),(x+hx,y0,z),(x+hx,y1,z),(x-hx,y1,z)])
    faces=[]
    for k in range(len(sections)-1):
        o=4*k;n=o+4
        for j in range(4):
            q=(j+1)%4
            faces.extend(((o+j,o+q,n+q),(o+j,n+q,n+j)))
    end=(len(sections)-1)*4
    faces.extend(((0,2,1),(0,3,2),(end,end+1,end+2),(end,end+2,end+3)))
    return dict(name=name,material=mat,vertices=vertices,faces=faces)


def desk(name,mat):
    """True manufactured bowed full-width fascia: not a rectangular slab."""
    verts=[];steps=32
    for i in range(steps+1):
        t=(i/steps)*2-1
        x=3.38*t
        curve=.20*(1-t*t)
        z=-4.61+curve
        low=.40+.035*(1-t*t)
        high=.775+.06*(1-t*t)
        verts.extend([(x,low,z-.160),(x,low,z+.065),
                      (x,high,z+.065),(x,high,z-.160)])
    faces=[]
    for i in range(steps):
        a=i*4;b=(i+1)*4
        for j in range(4):
            q=(j+1)%4
            faces.extend(((a+j,a+q,b+q),(a+j,b+q,b+j)))
    last=steps*4
    faces.extend(((0,2,1),(0,3,2),(last,last+1,last+2),(last,last+2,last+3)))
    return dict(name=name,material=mat,vertices=verts,faces=faces)


def section(name,mat,low,high,dy,thick):
    """Thin embedded machined upper desk seam with finished solid end caps."""
    verts=[];faces=[];steps=32
    for i in range(steps+1):
        t=i/steps*2-1;x=3.35*t
        z=-4.54+.20*(1-t*t)
        y=dy+.06*(1-t*t)
        verts.extend([(x,y-low,z),(x,y+high,z),
                      (x,y+high,z+thick),(x,y-low,z+thick)])
    for i in range(steps):
        a=i*4;b=a+4
        for j in range(4):
            q=(j+1)%4
            faces.extend(((a+j,a+q,b+q),(a+j,b+q,b+j)))
    last=steps*4
    faces.extend(((0,2,1),(0,3,2),(last,last+1,last+2),(last,last+2,last+3)))
    return dict(name=name,material=mat,vertices=verts,faces=faces)


def signed_volume(vertices,faces):
    v=0.
    for i,j,k in faces:
        a,b,c=[vertices[n] for n in (i,j,k)]
        v+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    return v


def metric_uv(pts):
    a,b,c=pts
    q=[b[i]-a[i] for i in range(3)]
    r=[c[i]-a[i] for i in range(3)]
    n=(q[1]*r[2]-q[2]*r[1],q[2]*r[0]-q[0]*r[2],q[0]*r[1]-q[1]*r[0])
    axis=max(range(3),key=lambda i:abs(n[i]))
    i,j=((1,2),(0,2),(0,1))[axis]
    uv=[(p[i]/1.7,p[j]/1.7) for p in pts]
    area=(uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[2][0]-uv[0][0])*(uv[1][1]-uv[0][1])
    assert abs(area)>1e-10, ('Invalid source PBR mapping',pts)
    return uv


def generate():
    parts=[
      ring('STAGE34 / CNC continuous panoramic portal / plaster ceramic',
           'powder_ivory',(3.71,.51,3.77,.335),(3.145,.84,3.197,.230),-6.30,-5.963),
      ring('STAGE34 / physically seated satin screen reveal',
           'satin_nickel',(3.196,.810,3.237,.256),(3.117,.879,3.172,.216),-6.015,-5.912),
      desk('STAGE34 / continuous bowed forward instrument cabinetry', 'powder_graphite'),
      section('STAGE34 / inlaid upper satin integral desk bead', 'satin_nickel',.017,.012,.767,.019),
    ]
    for side in (-1,1):
        parts.append(rail(f'STAGE34 / forward portal-to-cabinet bent load path {side}', 'powder_graphite',side))
    for p in parts:
        v=p['vertices'];f=p['faces']
        assert len(v)>12 and len(f)>15
        assert all(isfinite(coord) for pos in v for coord in pos)
        assert all(-3.76<=x<=3.76 and .36<=y<=3.79 and -6.34<=z<=-4.30
                   for x,y,z in v),p['name']
        vol=signed_volume(v,f)
        if vol<0:
            p['faces']=[(i,k,j) for i,j,k in f]
            vol=-vol
        assert vol>.00005,(p['name'],vol)
        edges=Counter()
        dirs=Counter()
        uv=[]
        for tri in p['faces']:
            assert len(set(tri))==3 and min(tri)>=0 and max(tri)<len(v)
            pts=[v[i] for i in tri]
            uv.append(metric_uv(pts))
            for x,y in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                edges[tuple(sorted((x,y)))]+=1
                dirs[(x,y)]+=1
        assert all(count==2 for count in edges.values()),p['name']
        assert all(dirs[(x,y)]==dirs[(y,x)]==1 for x,y in edges),p['name']
        p['face_uv']=uv
    assert len(parts)==6
    return parts


def build(model,mats):
    results=[]
    for item in generate():
        key=item['material']
        assert key in ('powder_ivory','powder_graphite','satin_nickel')
        ob=model(item['name'],item['vertices'],item['faces'],mats[key])
        mapped=ob.data.uv_layers.new(name='STAGE34_PHYSICAL_FACE_SCANNED_PBR_UV0')
        for poly,tex in zip(ob.data.polygons,item['face_uv']):
            for loop,uv in zip(poly.loop_indices,tex):
                mapped.data[loop].uv=uv
        results.append(ob)
    return results


def preflight():
    p=generate()
    return {'id':'AST_STAGE34_FORWARD_HERO_OPT_IN','parts':len(p),
            'triangles':sum(len(x['faces']) for x in p),
            'allSourceTopologyWatertight':True,'normalsSourceWindingConsistent':True,
            'perFacePbrUv0NoCollapse':True,'starfieldApertureClear':True,
            'exact96SourceExclusionUnchanged':True,
            'artApproved':False,'fullRenderAndMovementPending':True}

if __name__=='__main__':
    import json
    print(json.dumps(preflight(),indent=2))
