#!/usr/bin/env python3
"""Stage41: isolated, reversible Asteria command-workstation sculpt (NO DEPLOY).

Runs existing frozen Blender command generator unchanged, replacing ONLY its two
bulky lower instrument-pedestal assemblies with source-authored continuous
loadbearing workstation geometry. All glass/screens/controls/rails/platform
are regenerated through the untouched original routine.

No photorealism claim, no new source removal and no production writes.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import asteria_command_blender as original

PI = math.pi
REPLACED_NAMES = (
    'moulded eight-corner closed cast pedestal',
    'recessed toe support',
    'rear service door',
    'light-seam recess',
)
replaced = []
new = []


def bounds_face(obj, vertices, faces):
    assert len(vertices) > 6 and len(faces) > 5, obj
    for f in faces:
        assert all(0 <= i < len(vertices) for i in f) and len(set(f)) == 3, (obj, f)
    for x,y,z in vertices:
        assert -2.08 <= x <= 2.08 and .264 <= y <= 1.12 and -.45 <= z <= 1.1, (obj,(x,y,z))


def solid(name, verts, faces, material):
    bounds_face(name,verts,faces)
    # Existing model() maps original Three.js X/Y-up/Z to Blender X/-Z/Z-up.
    uvs=[((x+2.1)/4.2,(z+.65)/3.45) for x,_,z in verts]
    obj=original.model(name,verts,faces,material,uvs)
    new.append(obj)
    return obj


def loft_patch(name, P, ytop, back, front, material):
    """Single continuous shallow underside casting, not a side-by-side box.

    Corner stations hand-shaped to intersect the original closed upper rim
    and bend around the human kneehole. Top and underside are physical skins.
    """
    ribs=[(-.395,.302,1.055,.116),(-.335,.355,1.060,.137),
          (-.150,.368,1.064,.115),(.075,.373,1.064,.122),
          (.260,.353,1.055,.137),(.393,.296,1.035,.119)]
    # More stations (b) and lateral arcs (a) give a machined radius, not a slab.
    verts=[];UV=[];faces=[]
    cols=18
    for skin in (0,1):
        for b,w,h,t in ribs:
            for i in range(cols+1):
                u=i/cols*2-1
                a=u*w
                fillet=(abs(u)**8)*.015
                y=h + (.003*(1-u*u)) - (t if skin else 0) + (fillet if skin else -fillet)
                verts.append(P(a,y,b))
                UV.append(((u+1)*.5,(b+.395)/.79))
    row=cols+1;rows=len(ribs);offset=rows*row
    for j in range(rows-1):
        for i in range(cols):
            p=j*row+i;q=p+1;r=p+row;s=r+1
            faces.extend(((p,r,q),(q,r,s)))
            p+=offset;q+=offset;r+=offset;s+=offset
            faces.extend(((p,q,r),(q,s,r)))
    # Closed sides and ends
    for j in range(rows-1):
        for i in (0,cols):
            p=j*row+i;q=(j+1)*row+i
            if i==0:faces.extend(((p,p+offset,q),(q,p+offset,q+offset)))
            else:faces.extend(((p,q,p+offset),(q,q+offset,p+offset)))
    for i in range(cols):
        p=i;q=i+1
        faces.extend(((p,q,p+offset),(q,q+offset,p+offset)))
        p=(rows-1)*row+i;q=p+1
        faces.extend(((p,p+offset,q),(q,p+offset,q+offset)))
    return solid(name,verts,faces,material)


def smooth_beam(name, P, points, a, r_side, r_depth, material):
    """Solid elliptical forged side brace with curved centerline and full caps.

    Its continuous S-bend runs underside -> equipment shoulder -> structural
    landing shoe at the existing command plinth top. It is not free-standing.
    """
    refined=[]
    for i in range(len(points)-1):
        p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(len(points)-1,i+2)]
        for k in range(7):
            t=k/7
            def cat(j):
                v0,v1,v2,v3=[p[j] for p in (p0,p1,p2,p3)]
                return .5*((2*v1)+(-v0+v2)*t+(2*v0-5*v1+4*v2-v3)*t*t+(-v0+3*v1-3*v2+v3)*t*t*t)
            refined.append((cat(0),cat(1)))
    refined.append(points[-1])
    verts=[];faces=[];N=12
    for i,(b,y) in enumerate(refined):
        prev=refined[max(0,i-1)];nxt=refined[min(len(refined)-1,i+1)]
        db=nxt[0]-prev[0];dy=nxt[1]-prev[1];ll=math.hypot(db,dy) or 1
        nb,ny=-dy/ll,db/ll
        for j in range(N):
            ang=2*PI*j/N
            aa=a+r_side*math.cos(ang)
            bb=b+r_depth*math.sin(ang)*nb
            yy=y+r_depth*math.sin(ang)*ny
            verts.append(P(aa,yy,bb))
    for i in range(len(refined)-1):
        for j in range(N):
            p=i*N+j;q=i*N+(j+1)%N;r=(i+1)*N+j;s=(i+1)*N+(j+1)%N
            faces.extend(((p,q,r),(q,s,r)))
    for j in range(1,N-1):
        faces.append((0,j+1,j))
        end=(len(refined)-1)*N
        faces.append((end,end+j,end+j+1))
    return solid(name,verts,faces,material)


def capsule(name,P,a,y,b,size,mat):
    """Rounded floor mounting shoe physically sharing load with side frame."""
    w,d,h=size
    radial=16
    verts=[];faces=[]
    for skin in (-1,1):
        yy=y+skin*h/2
        for j in range(radial):
            t=2*PI*j/radial
            verts.append(P(a+w*.5*math.cos(t),yy,b+d*.5*math.sin(t)))
    for j in range(radial):
        k=(j+1)%radial
        faces.extend(((j,k,j+radial),(k,k+radial,j+radial)))
    for j in range(1,radial-1):
        faces.append((0,j+1,j))
        faces.append((radial,radial+j,radial+j+1))
    return solid(name,verts,faces,mat)


def detail_pipe(name,P,coords,r,material):
    obj=original.pipe(name,[P(*q) for q in coords],r,material,segments=3)
    new.append(obj)
    return obj


def make_workstation(side,mats):
    x0=side*1.27;z0=.58;rot=side*.24
    co,si=math.cos(rot),math.sin(rot)
    def P(a,y,b):return (x0+a*co-b*si,y,z0+a*si+b*co)
    tag=f'Command / {side} / STAGE41'
    # The curved graphite structural header actually lands within the
    # original metal rim, leaving the V3 glass untouched at y=1.165.
    loft_patch(tag+' / swept upper instrument cradle',P,1.05,-.395,.393,mats['powder_graphite'])
    # Rear equipment spine: half-depth compact unit behind visibly open knees.
    for y,b,size,mat,name in [
        (.842,-.300,(.50,.133,.214),'powder_ivory','ceramic service core'),
        (.725,-.376,(.435,.029,.185),'console_gasket','recessed gasketed hatch'),
        (.930,-.292,(.60,.027,.033),'satin_nickel','load-spreading rear sill'),
    ]:
        X,Y,Z=P(0,y,b)
        obj=original.box(tag+' / '+name,(X,Y,Z),size,mats[mat],.017,rot)
        new.append(obj)
    # Rigid physically connected cantilever ribs: both upper joins extend
    # into the closed header and both feet intersect the plinth at y=.281.
    path=[(-.264,1.016),(-.247,.916),(-.257,.777),(-.215,.624),(-.090,.505),
          (.085,.420),(.205,.345),(.235,.301)]
    for ix,a in enumerate((-.266,.266)):
        smooth_beam(tag+f' / deep formed cantilever {ix}',P,path,a,.056,.062,mats['powder_ivory'])
        smooth_beam(tag+f' / nickel underside rib {ix}',P,[(-.325,1.017),(-.278,.902),
                    (-.282,.774),(-.215,.624),(-.090,.516)],a,.014,.014,mats['satin_nickel'])
        capsule(tag+f' / floor anchor casting {ix}',P,a,.293,.213,(.181,.240,.056),mats['powder_graphite'])
        for s in (-1,1):
            x,y,z=P(a+s*.056,.328,.245)
            ob=original.bolt(tag+f' / retained anchor fastener {ix}:{s}',x,y,z,mats['satin_nickel'],.011)
            new.append(ob)
    # Visible compact equipment box beneath glass, inset rather than an
    # uninterrupted slab. Its frame is carried by the existing side braces.
    X,Y,Z=P(0,.755,-.318)
    obj=original.box(tag+' / vented aft electronics bridge',(X,Y,Z),(.44,.147,.138),
                     mats['powder_graphite'],.020,rot)
    new.append(obj)
    for i in range(5):
        a=-.170+i*.085
        detail_pipe(tag+f' / ventilated ceramic shadow vent {i}',P,
                    [(a,.743,-.399),(a,.773,-.399)],.0055,mats['satin_nickel'])
    detail_pipe(tag+' / under-ledge continuous satin tangent',P,
      [(a,.954,-.338) for a in [-.296,-.20,-.10,0,.10,.20,.296]],.012,mats['satin_nickel'])


real_make=original.make_pylon

def stage41_make_pylon(side,mats,correct_screen_uv=False,stage33=False):
    assert not stage33, 'Stage33 art and Stage41 may not stack'
    before=set(original.COMMAND.objects)
    real_make(side,mats,correct_screen_uv,stage33=False)
    made=[o for o in original.COMMAND.objects if o not in before]
    expected={f'Command / {side} / {s}' for s in REPLACED_NAMES}
    found={o.name for o in made if o.name in expected}
    assert found==expected, (found,expected)
    for ob in made:
        if ob.name in expected:
            replaced.append((ob.name,ob.type))
            bpy.data.objects.remove(ob,do_unlink=True)
    make_workstation(side,mats)


def main():
    original.make_pylon=stage41_make_pylon
    original.main()
    assert len(replaced)==8 and len(new)>=35,(len(replaced),len(new))
    # This text report is trial-only: no false GLB AO or art claim.
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    d=dict(zip(argv[::2],argv[1::2]))
    out=Path(d['--out'])
    q={'stage':'ASTERIA_STAGE41_ISOLATED_WORKSTATIONS',
       'removedSourceNodes':sorted(a for a,t in replaced),
       'replacementObjectCount':len(new),
       'retainsExactOriginalScreensAndControls':True,
       'noNewScannedMaterials':True,
       'fullContactAO':False,'artApproved':False,'productionModified':False}
    (out/'stage41-trial-report.json').write_text(json.dumps(q,indent=2)+'\n')
    print('ASTERIA_STAGE41_EXACT_OPT_IN',json.dumps(q))


if __name__=='__main__':main()
