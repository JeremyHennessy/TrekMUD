"""Stage46 independent physically grounded pilot seats: source-only art candidate.

All coordinates V3 Y-up metres; keeps original screen/controls, glass and footrests.
Original CC0 Asteria upholstery from SHA-verified hero GLB, not a new license claim.
"""
import math
from collections import Counter

HULL=9;DARK=7;EDGE=3;FABRIC=12;CONTROL=16;GREY=6

def part(name,vertices,faces,material):
    edges=Counter()
    for a,b,c in faces:
        assert len({a,b,c})==3
        for x,y in ((a,b),(b,c),(c,a)):edges[tuple(sorted((x,y)))]+=1
    assert edges and set(edges.values())=={2},(name,edges.most_common(1))
    volume=sum((vertices[a][0]*(vertices[b][1]*vertices[c][2]-vertices[b][2]*vertices[c][1])
      +vertices[a][1]*(vertices[b][2]*vertices[c][0]-vertices[b][0]*vertices[c][2])
      +vertices[a][2]*(vertices[b][0]*vertices[c][1]-vertices[b][1]*vertices[c][0]))/6
      for a,b,c in faces)
    assert abs(volume)>1e-7,(name,volume)
    if volume<0:faces=[(a,c,b) for a,b,c in faces]
    return dict(name=name,vertices=vertices,faces=faces,material=material)

def solid(name,sections,mat):
    v=[];f=[]
    for y,x,z,w,d in sections:
        v.extend(((x-w,y,z-d),(x+w,y,z-d),(x+w,y,z+d),(x-w,y,z+d)))
    for i in range(len(sections)-1):
        for j in range(4):
            a=i*4+j;b=i*4+(j+1)%4;c=a+4;d=b+4
            f.extend(((a,b,c),(b,d,c)))
    f.extend(((0,2,1),(0,3,2)))
    a=(len(sections)-1)*4
    f.extend(((a,a+1,a+2),(a,a+2,a+3)))
    return part(name,v,f,mat)

def skin(name,rows,cx,mat,depth=.09,bulge=.014,n=28):
    v=[];f=[]
    for s in (0,1):
        for y,w,z in rows:
            for j in range(n+1):
                t=j*2/n-1
                v.append((cx+w*t,y,z+bulge*(1-t*t)**2-s*depth))
    stride=n+1;count=len(rows);off=count*stride
    for i in range(count-1):
        for j in range(n):
            a=i*stride+j;b=a+1;c=a+stride;d=c+1
            f.extend(((a,c,b),(b,c,d)))
            a+=off;b+=off;c+=off;d+=off
            f.extend(((a,b,c),(b,d,c)))
        for j in (0,n):
            a=i*stride+j;b=(i+1)*stride+j
            if j==0:f.extend(((a,a+off,b),(b,a+off,b+off)))
            else:f.extend(((a,b,a+off),(b,b+off,a+off)))
    for j in range(n):
        a=j;b=a+1
        f.extend(((a,b,a+off),(b,b+off,a+off)))
        a=(count-1)*stride+j;b=a+1
        f.extend(((a,a+off,b),(b,a+off,b+off)))
    return part(name,v,f,mat)

def bolt(name,point,mat,r=.015):
    x,y,z=point;n=16;v=[];f=[]
    for h in (-.005,.005):
        for j in range(n):
            t=2*math.pi*j/n
            v.append((x+r*math.cos(t),y+h,z+r*math.sin(t)))
    for j in range(n):
        k=(j+1)%n;f.extend(((j,k,j+n),(k,k+n,j+n)))
    for j in range(1,n-1):f.extend(((0,j+1,j),(n,n+j,n+j+1)))
    return part(name,v,f,mat)

def seat(side):
    x0=side*1.16;z0=-2.17
    nm="STAGE46 / "+("port" if side<0 else "starboard")+" / crashworthy flight seat"
    out=[]
    put=out.append
    put(solid(nm+" / deck bolted fixed shoe",[(.055,x0,z0+.10,.300,.260),(.124,x0,z0+.10,.282,.242)],HULL))
    put(solid(nm+" / spreadfoot integrated yoke",[(.108,x0,z0+.104,.20,.16),(.22,x0,z0+.09,.23,.16),(.48,x0,z0+.08,.17,.14),(.68,x0,z0+.16,.20,.14)],EDGE))
    put(solid(nm+" / cast central column",[(.30,x0,z0+.07,.148,.17),(.52,x0,z0+.08,.157,.145),(.79,x0,z0+.18,.165,.145),(.92,x0,z0+.23,.153,.138)],HULL))
    for s in (-1,1):
        put(solid(nm+f" / integrated loadbearing side web {s}",[(.12,x0+s*.205,z0+.08,.048,.15),(.29,x0+s*.175,z0+.08,.063,.18),(.54,x0+s*.202,z0+.17,.079,.15),(.69,x0+s*.190,z0+.18,.065,.125)],HULL))
        for z in (-.045,.205):put(bolt(nm+f" / deck fastener {s} {z}",(x0+s*.218,.121,z0+z),EDGE))
    backrows=[(.70,.262,.135),(.86,.285,.164),(1.03,.305,.205),(1.31,.300,.257),(1.48,.275,.284),(1.62,.245,.295),(1.70,.195,.302)]
    put(skin(nm+" / integrated shaped back chassis",[(y,w,z0+z) for y,w,z in backrows],x0,HULL,depth=.115,n=36))
    for s in (-1,1):
        put(solid(nm+f" / continuous forged side crash armor {s}",[(.61,x0+s*.246,z0+.138,.056,.129),(.79,x0+s*.28,z0+.157,.067,.122),(1.14,x0+s*.309,z0+.231,.062,.128),(1.46,x0+s*.273,z0+.296,.055,.126),(1.66,x0+s*.19,z0+.312,.051,.111)],EDGE))
        put(solid(nm+f" / attached control housing {s}",[(.65,x0+s*.302,z0-.175,.080,.17),(.78,x0+s*.335,z0-.165,.094,.20),(.87,x0+s*.314,z0-.145,.089,.194)],HULL))
    put(solid(nm+" / inset ventilation cassette",[(.93,x0,z0+.269,.170,.038),(1.05,x0,z0+.288,.177,.039),(1.39,x0,z0+.309,.172,.036),(1.50,x0,z0+.325,.150,.031)],DARK))
    for i,y in enumerate((1.05,1.175,1.30,1.425)):
        put(solid(nm+f" / recessed equipment outlet fin {i}",[(y-.014,x0,z0+.337,.166,.017),(y+.014,x0,z0+.338,.166,.017)],EDGE))
    put(solid(nm+" / armored seat belt anchor",[(.70,x0,z0+.18,.242,.10),(.86,x0,z0+.19,.251,.107),(.93,x0,z0+.222,.233,.102)],GREY))
    for s in (-1,1):
        for y in (.81,1.47):
            put(bolt(nm+f" / service fastener {s} {y}",(x0+s*.184,y,z0+(.352 if y>1 else .308)),CONTROL))
    # Upholstered pads are in FRONT of the machined shell, original source material 12.
    for i,(lo,hi,w) in enumerate(((.83,1.02,.258),(1.04,1.26,.263),(1.28,1.48,.252),(1.51,1.67,.194))):
        put(skin(nm+f" / replaceable sewn microfibre cushion {i}",[
            (lo,w*.87,z0-.010+(lo-.8)*.13),((lo+hi)/2,w,z0-.007+((lo+hi)/2-.8)*.13),
            (hi,w*.87,z0+.017+(hi-.8)*.13)],x0,FABRIC,depth=.073,n=30))
    put(solid(nm+" / rigid seat pan",[(.56,x0,z0-.37,.31,.19),(.675,x0,z0-.27,.31,.20),(.73,x0,z0-.17,.27,.16)],HULL))
    put(skin(nm+" / deep foam seat squab",[(.704,.273,z0-.49),(.727,.307,z0-.29),(.748,.268,z0-.09)],x0,FABRIC,depth=.071,n=28))
    for s in (-1,1):
        put(solid(nm+f" / joined arm control casting {s}",[(.67,x0+s*.297,z0+.04,.079,.11),(.77,x0+s*.351,z0-.12,.090,.16),(.82,x0+s*.367,z0-.28,.088,.18),(.85,x0+s*.36,z0-.445,.082,.115)],HULL))
        put(solid(nm+f" / satin wrist tactile insert {s}",[(.856,x0+s*.36,z0-.38,.064,.083),(.858,x0+s*.36,z0-.20,.064,.098)],EDGE))
    return out

def make_pair():
    parts=seat(-1)+seat(1)
    assert len(parts)>=55
    return parts
