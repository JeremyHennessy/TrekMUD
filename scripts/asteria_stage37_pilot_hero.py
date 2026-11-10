#!/usr/bin/env python3
"""Stage37 reversible twin pilot seat geometry, not an approved asset.

46 organically rounded 3D components with continuous upholstered surfaces. All original frozen
V3 sources, screens, controls, moving/collision code are out of scope.
"""
from __future__ import annotations
from collections import Counter
from math import cos, sin, pi, sqrt, isfinite

def signed_volume(verts, faces):
    v=0.
    for i,j,k in faces:
        a,b,c=verts[i],verts[j],verts[k]
        v+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    return v

def cap_loft(name,mat,sections,around=48):
    """Closed sculpted upholstery, Catmull-Rom longitudinal profiles, rounded corners.

    Five interpolated rings per source interval prevent the obvious flat bands
    visible in the rejected Stage37 model. Preserve real 3D thickness.
    """
    assert len(sections)>=2 and around>=24 and around%4==0
    def spline(a,b,c,d,t):
        return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+
                    (-a+3*b-3*c+d)*t*t*t)
    smooth=[]
    for i in range(len(sections)-1):
        p0,p1=sections[max(i-1,0)],sections[i]
        p2,p3=sections[i+1],sections[min(i+2,len(sections)-1)]
        for step in range(5):
            t=step/5
            smooth.append([spline(p0[j],p1[j],p2[j],p3[j],t)
                           for j in range(5)])
    smooth.append(list(sections[-1]))
    vertices=[]
    for y,xc,half,zc,depth in smooth:
        assert .02<half<.72 and .012<depth<.5
        for k in range(around):
            a=2*pi*k/around
            co,si=cos(a),sin(a)
            vertices.append((xc+half*(1 if co>=0 else -1)*abs(co)**.56,
                             y,zc+depth*(1 if si>=0 else -1)*abs(si)**.56))
    faces=[]
    for ring in range(len(smooth)-1):
        for j in range(around):
            a=ring*around+j;b=ring*around+(j+1)%around
            c=(ring+1)*around+j;d=(ring+1)*around+(j+1)%around
            faces.extend(((a,b,c),(b,d,c)))
    end=(len(smooth)-1)*around
    for k in range(1,around-1):
        faces.extend(((0,k+1,k),(end,end+k,end+k+1)))
    return dict(name=name,material=mat,vertices=vertices,faces=faces)

def beam(name,mat,p,q,width=.04,depth=.048,sides=12):
    axis=[q[i]-p[i] for i in range(3)]
    length=sqrt(sum(x*x for x in axis))
    assert length>.025
    axis=[x/length for x in axis]
    ref=[0,0,1] if abs(axis[2])<.88 else [1,0,0]
    u=[axis[1]*ref[2]-axis[2]*ref[1],axis[2]*ref[0]-axis[0]*ref[2],axis[0]*ref[1]-axis[1]*ref[0]]
    m=sqrt(sum(x*x for x in u));u=[x/m for x in u]
    v=[axis[1]*u[2]-axis[2]*u[1],axis[2]*u[0]-axis[0]*u[2],axis[0]*u[1]-axis[1]*u[0]]
    vertices=[]
    for centre in (p,q):
        for k in range(sides):
            a=2*pi*k/sides
            vertices.append(tuple(centre[i]+width*cos(a)*u[i]+depth*sin(a)*v[i] for i in range(3)))
    faces=[]
    for k in range(sides):
        j=(k+1)%sides
        faces.extend(((k,j,sides+k),(j,sides+j,sides+k)))
    for k in range(1,sides-1):
        faces.extend(((0,k+1,k),(sides,sides+k,sides+k+1)))
    return dict(name=name,material=mat,vertices=vertices,faces=faces)

def metric_uv(points):
    a,b,c=points
    u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    axis=max(range(3),key=lambda j:abs(n[j]))
    i,j=((1,2),(0,2),(0,1))[axis]
    uv=[(p[i]/.7,p[j]/.7) for p in points]
    area=(uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[2][0]-uv[0][0])*(uv[1][1]-uv[0][1])
    assert abs(area)>1e-10
    return uv

def make(side):
    assert side in (-1,1)
    x0,z0=side*1.15,-2.13
    def world(p):
        x,y,z=p
        return (x0+x*cos(side*.035)-z*sin(side*.035),y,z0+x*sin(side*.035)+z*cos(side*.035))
    parts=[]
    def add(part):
        part['name']=f'STAGE37 / pilot {side:+d} / '+part['name']
        part['vertices']=[world(p) for p in part['vertices']]
        parts.append(part)
    # Back-facing sculpted silhouette; fully attached rear cushion cassette.
    add(cap_loft('continuous formed rear spine','graphite',[
        (.665,0,.27,.205,.102),(.760,0,.405,.285,.125),
        (1.02,0,.435,.340,.130),(1.30,0,.402,.431,.120),
        (1.52,0,.332,.505,.099),(1.66,0,.255,.529,.076),(1.675,0,.218,.530,.061)]))
    add(cap_loft('rear-facing inset plum upholstery','velour',[
        (.770,0,.245,.419,.022),(.855,0,.310,.429,.035),
        (1.050,0,.342,.473,.035),(1.300,0,.302,.553,.031),
        (1.508,0,.235,.595,.027),(1.570,0,.184,.593,.018)]))
    add(cap_loft('lumbar cushion nested into rear','velour_alt',[
        (.794,0,.165,.451,.018),(.830,0,.277,.468,.043),
        (.975,0,.282,.474,.043),(1.025,0,.227,.473,.019)]))
    add(cap_loft('contoured upper head support','velour_alt',[
        (1.472,0,.177,.604,.025),(1.515,0,.220,.614,.042),
        (1.615,0,.225,.627,.040),(1.656,0,.150,.610,.019)]))
    add(cap_loft('underslung graphite seat pan','graphite',[
        (.570,0,.320,-.035,.285),(.615,0,.430,-.040,.365),
        (.676,0,.441,-.052,.375),(.704,0,.405,-.062,.338)]))
    add(cap_loft('sculpted plum seat saddle','velour',[
        (.679,0,.367,-.059,.320),(.717,0,.405,-.059,.346),
        (.758,0,.398,-.054,.340),(.768,0,.320,-.045,.280)]))
    add(cap_loft('floor-mounted graphite drive shoe','graphite',[
        (.060,0,.330,-.040,.240),(.085,0,.365,-.038,.275),
        (.148,0,.352,-.036,.253),(.178,0,.270,-.030,.193)]))
    add(cap_loft('integrated rotary cable bearing','nickel',[
        (.163,0,.122,-.018,.127),(.212,0,.143,-.017,.145),
        (.300,0,.102,-.020,.110),(.350,0,.083,-.019,.089)]))
    add(beam('seat load-bearing central column','graphite',(.0,.300,-.02),(.0,.648,-.040),.091,.083,16))
    for sg in (-1,1):
        add(beam(f'splayed Y-frame saddle bearer {sg:+d}','nickel',
                 (sg*.055,.324,-.010),(sg*.314,.624,-.046),.049,.054))
        add(beam(f'rear shell shoulder brace {sg:+d}','graphite',
                 (sg*.298,.666,.225),(sg*.332,1.286,.415),.055,.068))
        add(beam(f'cantilever arm-electronics riser {sg:+d}','graphite',
                 (sg*.332,.618,-.100),(sg*.520,.916,-.040),.061,.071))
        add(cap_loft(f'integrated sculpted arm pad {sg:+d}','velour_alt',[
            (.912,sg*.515,.105,-.051,.230),(.941,sg*.526,.135,-.051,.258),
            (.990,sg*.530,.140,-.051,.255),(1.000,sg*.528,.095,-.051,.210)],24))
        add(cap_loft(f'recessed tactile console panel {sg:+d}','gasket',[
            (.997,sg*.531,.074,-.075,.145),(1.017,sg*.531,.091,-.075,.164),
            (1.027,sg*.531,.081,-.075,.152)],24))
        add(beam(f'satin shoulder-to-arm joint {sg:+d}','nickel',
                 (sg*.394,.834,.194),(sg*.518,.930,.084),.028,.031))
        add(beam(f'shoe underside structural anchor {sg:+d}','graphite',
                 (sg*.235,.090,-.135),(sg*.292,.184,-.162),.080,.065))
    return parts

def generate():
    parts=make(-1)+make(1)
    kinds={'graphite','velour','velour_alt','nickel','gasket'}
    for part in parts:
        verts=part['vertices'];faces=part['faces']
        assert part['material'] in kinds and len(verts)>=24 and len(faces)>40
        assert all(isfinite(x) for p in verts for x in p)
        assert all(-2.1<=x<=2.1 and .04<=y<=1.72 and -2.85<=z<=-1.36
                   for x,y,z in verts),part['name']
        vol=signed_volume(verts,faces)
        if vol<0:part['faces']=[(a,c,b) for a,b,c in faces]
        assert abs(vol)>.0000004,(part['name'],vol)
        edges=Counter();direct=Counter();uv=[]
        for tri in part['faces']:
            assert len(set(tri))==3
            uv.append(metric_uv([verts[i] for i in tri]))
            for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
                edges[tuple(sorted((a,b)))]+=1;direct[(a,b)]+=1
        assert all(n==2 for n in edges.values()),part['name']
        assert all(direct[(a,b)]==direct[(b,a)]==1 for a,b in edges),part['name']
        part['face_uv']=uv
    assert len(parts)==46
    assert 14000<sum(len(p['faces']) for p in parts)<52000
    return parts

def preflight():
    p=generate()
    return {'id':'AST_STAGE37_TWO_PILOT_SEATS_ART_FIRST',
        'parts':len(p),'triangles':sum(len(x['faces']) for x in p),
        'sourceOldPilotFacesExpected':32600,'closedManifold':True,
        'perFacePhysicalUV0':True,'scannedPbrLicenseVerified':False,
        'realCyclesContactUV1Verified':False,'artApproved':False,
        'productionChanged':False}

if __name__=='__main__':
    import json
    print(json.dumps(preflight(),indent=2))
