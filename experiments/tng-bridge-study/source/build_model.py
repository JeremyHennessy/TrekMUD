"""Reference-guided original TNG-era bridge-style geometry.
Does NOT claim set-accurate survey or photogrammetric geometry.
Exports a textured glTF/GLB and a browser WebGL2 scene from identical meshes.
"""
import math, json, gzip, base64, random, io
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import trimesh
P=Path(__file__).parent
random.seed(83)

M={
 'carpet':('#534453',0.0),'carpetEdge':('#6c586b',0.0), 'walkway':('#5b6968',0.0), 'floorTrim':('#afa18c',0.04),
 'wall':('#a59c8e',0.0),'wallLight':('#d1c7b6',0.0),'wallInner':('#867e75',0.0),'wallInset':('#8b8479',0.0),
 'frame':('#625e58',0.0),'bronze':('#ae9272',0.12),'rail':('#c6ad87',0.08),'metal':('#383a3e',0.02),'metalLight':('#686765',0.0),
 'chair':('#b79a83',0.0),'chairDark':('#876d60',0.0),'chairSeam':('#d3b39b',0.0),'pedestal':('#494340',0.0),
 'console':('#9c9289',0.0),'consoleTop':('#454444',0.0),'consoleEdge':('#c6b8a6',0.0),'darkScreen':('#081018',0.12),
 'screen':('#14212a',0.4),'cyan':('#84e3e3',1.0),'gold':('#f0cb85',0.88),'lamp':('#fff3dc',1.4),
 'paleBlue':('#b1dfeb',0.7),'purple':('#b989a6',0.5), 'orange':('#e9aa74',0.65),'red':('#bb6671',0.45),
 'glass':('#232f39',0.15),'black':('#161a20',0.0), 'texturedLCARS':('#ffffff',0.9), 'texturedSide':('#ffffff',0.7),
 'starfield':('#ffffff',0.35), 'fabricBorder':('#706067',0.0),
}
TEX={'texturedLCARS':'lcars.png','texturedSide':'side_screen.png','starfield':'stars.png'}
# builders: p, normals, uv, indices
B=defaultdict(lambda:{'p':[],'n':[],'uv':[],'idx':[]})

def rgb(h): return [int(h[i:i+2],16)/255 for i in (1,3,5)]
def N(a):
 a=np.asarray(a,dtype=float);norm=np.linalg.norm(a)
 return a/max(1e-9,norm)
def TRI(mat,verts,norms=None,uvs=None):
 # custom mesh triangles provided list of 3 tuples per face
 b=B[mat]; l=len(b['p'])//3
 for i,p in enumerate(verts): b['p'].extend([float(v) for v in p]);b['uv'].extend(uvs[i] if uvs else [0,0])
 if norms is None:
  for i in range(0,len(verts),3):
   n=N(np.cross(np.array(verts[i+1])-verts[i],np.array(verts[i+2])-verts[i]))
   for _ in range(3):b['n'].extend(n.tolist())
 else:
  for n in norms:b['n'].extend([float(v) for v in n])
 b['idx'].extend(range(l,l+len(verts)))
def quad(a,b,c,d,mat,uv=True):
 # inward/outward orientation follows vertices; double-sided shader
 uv6=[[0,1],[1,1],[1,0],[0,1],[1,0],[0,0]] if uv else None
 TRI(mat,[a,b,c,a,c,d],uvs=uv6)
def rotateY(v,a):
 x,y,z=v;return [x*math.cos(a)+z*math.sin(a), y, -x*math.sin(a)+z*math.cos(a)]
def box(pos,size,mat,yaw=0):
 x,y,z=pos;sx,sy,sz=np.array(size)/2
 corners=[[-sx,-sy,-sz],[sx,-sy,-sz],[sx,sy,-sz],[-sx,sy,-sz],[-sx,-sy,sz],[sx,-sy,sz],[sx,sy,sz],[-sx,sy,sz]]
 corners=[[x+q[0],y+q[1],z+q[2]] for q in [rotateY(v,yaw) for v in corners]]
 for ids in [(0,1,2,3),(5,4,7,6),(4,0,3,7),(1,5,6,2),(3,2,6,7),(4,5,1,0)]:
  quad(*[corners[k] for k in ids],mat)
def rounded_box(center,size,r,mat,yaw=0,steps=4):
 cx,cy,cz=center; hx,hy,hz=np.array(size)/2
 if min(hx,hy,hz)<=r:r=max(.001,min(hx,hy,hz)*.8)
 faces=[(0,1),(0,-1),(1,1),(1,-1),(2,1),(2,-1)]
 vertices=[];normals=[];uvs=[];indices=[]
 for k,sign in faces:
  axes=[i for i in (0,1,2) if i!=k];ai,bi=axes
  for yi in range(steps+1):
   for xi in range(steps+1):
    vals=[0.,0.,0.];vals[k]=sign*[hx,hy,hz][k];vals[ai]=(-1+2*xi/steps)*[hx,hy,hz][ai];vals[bi]=(-1+2*yi/steps)*[hx,hy,hz][bi]
    q=[max(-max(0,t-r),min(max(0,t-r),v)) for t,v in zip([hx,hy,hz],vals)]
    delta=np.array(vals)-q;normal=N(delta);rounded=np.array(q)+normal*r
    loc=rotateY(rounded,yaw);n=rotateY(normal,yaw)
    vertices.append([cx+loc[0],cy+loc[1],cz+loc[2]]);normals.append(n);uvs.append([xi/steps,yi/steps])
  offset=len(vertices)-(steps+1)**2
  for yi in range(steps):
   for xi in range(steps):
    a=offset+yi*(steps+1)+xi;bb=a+1;c=a+(steps+1);d=c+1
    indices.extend([a,bb,d,a,d,c])
 b=B[mat];base=len(b['p'])//3
 for v in vertices:b['p'].extend(v)
 for n in normals:b['n'].extend(n)
 for uv in uvs:b['uv'].extend(uv)
 b['idx'].extend([base+i for i in indices])

def cylinder(p0,p1,r,mat,n=12,r2=None,cap=True):
 p0,p1=np.array(p0,float),np.array(p1,float);axis=N(p1-p0)
 if np.linalg.norm(p1-p0)<1e-6:return
 u=N(np.cross(axis,[0,0,1] if abs(axis[2])<.89 else [1,0,0]));v=N(np.cross(axis,u))
 if r2 is None:r2=r
 for i in range(n):
  t0=2*math.pi*i/n;t1=2*math.pi*(i+1)/n
  a=u*math.cos(t0)+v*math.sin(t0);b=u*math.cos(t1)+v*math.sin(t1)
  c0=(p0+r*a).tolist();c1=(p0+r*b).tolist();d0=(p1+r2*a).tolist();d1=(p1+r2*b).tolist()
  quad(c0,c1,d1,d0,mat)
  if cap:
   TRI(mat,[p0.tolist(),c1,c0]);TRI(mat,[p1.tolist(),d0,d1])
def ribbon(points,width,mat,vertical=False):
 for i in range(len(points)-1):
  a=np.array(points[i]);b=np.array(points[i+1]);t=N(b-a)
  v=N(np.cross([0,1,0] if not vertical else [0,0,1],t))*width/2
  quad((a-v).tolist(),(a+v).tolist(),(b+v).tolist(),(b-v).tolist(),mat)
def tube(points,r,mat,n=9):
 for a,b in zip(points[:-1],points[1:]):cylinder(a,b,r,mat,n=n,cap=False)
def elliptical_disc(rx,rz,y,mat,cx=0,cz=0,segments=100):
 for i in range(segments):
  t0=2*math.pi*i/segments;t1=2*math.pi*(i+1)/segments
  a=[cx+rx*math.sin(t0),y,cz+rz*math.cos(t0)];b=[cx+rx*math.sin(t1),y,cz+rz*math.cos(t1)]
  TRI(mat,[[cx,y,cz],a,b])
def ellipse_ring(rxo,rzo,rxi,rzi,y,mat,segments=110,center=(0,0)):
 cx,cz=center
 for i in range(segments):
  t0=2*math.pi*i/segments;t1=2*math.pi*(i+1)/segments
  a=[cx+rxo*math.sin(t0),y,cz+rzo*math.cos(t0)];b=[cx+rxo*math.sin(t1),y,cz+rzo*math.cos(t1)]
  c=[cx+rxi*math.sin(t1),y,cz+rzi*math.cos(t1)];d=[cx+rxi*math.sin(t0),y,cz+rzi*math.cos(t0)]
  quad(a,b,c,d,mat)
def arc_points(rx,rz,y,a,b,n=40,cx=0,cz=0):return [[cx+rx*math.sin(a+(b-a)*i/n),y,cz+rz*math.cos(a+(b-a)*i/n)] for i in range(n+1)]
def wall_arc(rx,rz,theta0,theta1,y0,y1,mat,n=1):
 for i in range(n):
  t0=theta0+(theta1-theta0)*i/n;t1=theta0+(theta1-theta0)*(i+1)/n
  a=[rx*math.sin(t0),y0,-rz*math.cos(t0)];b=[rx*math.sin(t1),y0,-rz*math.cos(t1)]
  c=[rx*math.sin(t1),y1,-rz*math.cos(t1)];d=[rx*math.sin(t0),y1,-rz*math.cos(t0)]
  quad(a,b,c,d,mat)
def panel_at(theta,y,w,h,mat,rx=7.52,rz=6.32,offset=.06):
 x=rx*math.sin(theta);z=-rz*math.cos(theta)
 tangent=np.array([math.cos(theta),0,math.sin(theta)]); inward=np.array([-math.sin(theta),0,math.cos(theta)])
 c=np.array([x,y,z])+offset*inward
 a=c-tangent*w/2+np.array([0,-h/2,0]);b=c+tangent*w/2+np.array([0,-h/2,0])
 d=c-tangent*w/2+np.array([0,h/2,0]);cc=c+tangent*w/2+np.array([0,h/2,0])
 quad(a.tolist(),b.tolist(),cc.tolist(),d.tolist(),mat)
def bevel_console(x,y,z,w=2,h=.48,d=.65,yaw=0):
 rounded_box((x,y,z),(w,h,d),.08,'console',yaw)
 box((x,y+h*.45,z-d*.10),(w*.96,.055,d*.87),'consoleTop',yaw)
 box((x,y+h*.49,z-d*.12),(w*.83,.012,d*.72),'texturedLCARS',yaw)
 # front kick panel
 box((x,y-h*.42,z+d*.41),(w*.89,.045,.045),'bronze',yaw)

# SCENE FLOOR / ROOM
elliptical_disc(7.76,6.58,-.34,'floorTrim')
elliptical_disc(7.60,6.40,-.27,'walkway')
# raised border and central pit, distinctive mauve plum inset
elliptical_disc(4.68,4.40,-.22,'carpetEdge',cz=-.5)
elliptical_disc(4.40,4.12,-.20,'carpet',cz=-.5)
ellipse_ring(4.68,4.4,4.45,4.17,-.175,'bronze',center=(0,-.5))
ellipse_ring(7.65,6.44,7.42,6.22,-.22,'floorTrim')
# graceful stage at rear tactical area
box((0,-.10,3.77),(7.6,.24,2.6),'carpetEdge')
box((0,-.08,3.67),(7.2,.22,2.25),'carpet')
for ymat,yy in [('bronze',.00),('floorTrim',.02)]:box((0,yy,2.52),(7.4,.06,.06),ymat)

# WALL STRUCTURE, oval shell lower and upper band
for i in range(100):
 t0=2*math.pi*i/100;t1=2*math.pi*(i+1)/100
 wall_arc(7.55,6.35,t0,t1,-.33,.42,'wallInner')
 wall_arc(7.55,6.35,t0,t1,.42,3.13,'wall' if i%5 else 'wallLight')
 wall_arc(7.55,6.35,t0,t1,3.13,3.64,'wallInner')
for level,rr,mat in [(0.35,7.48,'bronze'),(2.90,7.50,'bronze'),(3.25,7.52,'bronze')]:
 tube(arc_points(rr,6.28,level,0,2*math.pi,120),.032,mat)
# ceiling and inset light trays
elliptical_disc(7.48,6.29,3.66,'wallLight')
ellipse_ring(7.42,6.22,6.65,5.48,3.62,'wallInner')
ellipse_ring(6.55,5.4,5.98,4.96,3.61,'frame')
elliptical_disc(5.96,4.92,3.62,'wallLight')
ellipse_ring(4.24,3.30,3.84,2.97,3.58,'bronze')
elliptical_disc(3.74,2.87,3.57,'wall')
# real warm luminous ceiling grid panels, inset quadrilateral with trim
for col in range(-4,5):
 for row in range(-2,3):
  x=col*1.09;z=row*1.2-.10
  if (x/5.9)**2+(z/4.7)**2>0.92:continue
  rounded_box((x,3.558,z),(0.86,.04,.94),.08,'lamp',steps=2)
  box((x,3.532,z),(.94,.025,1.01),'frame')
# upper accent inner rings
for rx,rz,y,mat in [(5.99,4.9,3.53,'bronze'),(6.77,5.59,3.53,'rail')]:tube(arc_points(rx,rz,y,0,2*math.pi,100),.048,mat)

# WALL MODULES, SIDE PANELS
for theta in np.linspace(-2.0,-.55,11).tolist()+np.linspace(.55,2.0,11).tolist():
 # long cream wall cabinet modules as on clip's starboard side
 panel_at(theta,1.75,.73,2.42,'wallLight',offset=.069)
 panel_at(theta,1.72,.65,2.28,'wallInset',offset=.088)
 for yi in [.69,1.37,2.02,2.68]:
  panel_at(theta,yi,.62,.04,'frame',offset=.107)
 for yi in [.78,1.47,2.14]:
  panel_at(theta,yi,.55,.52,'wall',offset=.11)
  # black access latches left/right
  for delta in (-.19,.22):
   a=theta+delta/7.5
   panel_at(a,yi+.12,.065,.035,'black',offset=.13)
  if int(theta*100)%3==0:panel_at(theta,yi-.17,.31,.035,'frame',offset=.132)
# secondary horizontal side light strip
for amin,amax in [(-2.05,-.5),(.5,2.05)]:
 tube(arc_points(7.44,6.26,2.94,amin,amax,34),.055,'paleBlue')
 tube(arc_points(7.44,6.26,2.86,amin,amax,34),.018,'bronze')

# Front wall's large dark viewscreen and decorative trim. Flat projection visually prominent
box((0,1.83,-6.19),(7.5,2.55,.29),'frame')
rounded_box((0,1.87,-6.014),(7.17,2.29,.08),.07,'darkScreen',steps=4)
box((0,1.87,-5.962),(6.95,2.08,.018),'starfield')
for x in [-3.84,3.84]:rounded_box((x,1.90,-5.96),(.16,2.7,.18),.08,'bronze',steps=3)
rounded_box((0,3.14,-5.98),(7.82,.16,.30),.06,'bronze')
rounded_box((0,.46,-5.98),(7.8,.13,.24),.05,'bronze')
# forward navigation station, two broad curved consoles facing viewscreen
for x in [-2.15,2.15]:
 bevel_console(x,.29,-4.0,2.85,.44,.88)
 for dx in [-1.03,-.67,-.3,.3,.65,1.0]:
  box((x+dx,.55,-4.08),(.055,.012,.51),'bronze')
 # screen front narrow modules
 for dx in [-.9,-.4,.4,.9]:box((x+dx,.48,-4.46),(.15,.055,.018),'cyan')
# main console tapered middle section and pilot seats
bevel_console(0,.24,-4.2,1.14,.47,.66)

# Command pit geometry, rail geometry with graceful bronze curve centered about chairs
# Yaw ends and sweep from left to right behind command chairs
rail=[[-4.1+8.2*i/52,1.03+0.38*(1-((i-26)/26)**2),1.10+1.13*(1-((i-26)/26)**2)] for i in range(53)]
tube(rail,.075,'rail',n=11)
rail_top=[[p[0],p[1]+.14,p[2]+.12] for p in rail]
tube(rail_top,.034,'bronze')
for i in range(0,53,5):
 a=rail[i];cylinder([a[0],-.15,a[2]],a,.048,'bronze')
# thin curved dark band under top rail
for i in range(52):
 a=rail[i];b=rail[i+1];quad(a,b,[b[0],b[1]-.12,b[2]+.01],[a[0],a[1]-.12,a[2]+.01],'consoleEdge')

# chair factory: upholstered office style with fitted backs and flared arm rests
def chair(x,z,scale=1,angle=0,seat_y=.05):
 def xf(a,b,c):
  a*=scale;b*=scale;c*=scale
  v=rotateY([a,b,c],angle);return [x+v[0],seat_y+v[1],z+v[2]]
 def rb(local,size,rad,mat):
  rounded_box(xf(*local),[v*scale for v in size],rad*scale,mat,yaw=angle,steps=5)
 # taper pedestal + heavy round base
 cylinder(xf(0,-.14,0),xf(0,.32,0),.105*scale,'pedestal',12)
 cylinder(xf(0,-.17,0),xf(0,-.12,0),.40*scale,'metalLight',16)
 rb((0,.43,.05),(1.00,.22,.96),.10,'chair')
 rb((0,.50,-.06),(.84,.09,.68),.04,'chairSeam')
 # backrest leaning backward z+ rear
 rb((0,.97,.42),(1.03,1.12,.22),.11,'chair')
 rb((0,1.03,.31),(.88,.81,.10),.05,'chairDark')
 rb((0,1.07,.245),(.76,.69,.038),.018,'chair')
 rb((0,1.52,.52),(.9,.19,.26),.075,'chairSeam')
 # side upholstered shoulder wings
 for sign in [-1,1]:
  rb((sign*.46,1.10,.36),(.19,.84,.20),.07,'chairSeam')
  rb((sign*.63,.64,-.07),(.19,.25,.80),.075,'chair')
  rb((sign*.65,.77,-.19),(.14,.035,.30),.018,'consoleTop')
  rb((sign*.65,.795,-.15),(.095,.012,.19),.003,'texturedSide')
 # slim center stitching lines
 for sign in [-1,1]:
  p=[xf(sign*.34,.64,.23),xf(sign*.34,1.37,.27)]
  tube(p,.009*scale,'chairSeam',n=7)
chair(-1.8,-2.85,.90,0,seat_y=-.18);chair(1.8,-2.85,.90,0,seat_y=-.18)
chair(0,-.20,1.13,0,seat_y=-.13)
chair(-2.67,.12,.96,-.12,seat_y=-.13);chair(2.67,.12,.96,.12,seat_y=-.13)

# center captain's pedestal / low stage outline
elliptical_disc(1.08,.84,-.18,'bronze',cz=-.18)
elliptical_disc(.95,.74,-.165,'carpet',cz=-.18)

# wide tactical station at back (semicircle desk, multiple screens)
for i in range(31):
 t=-1.23+2.46*(i+.5)/31
 x=4.45*math.sin(t);z=3.83+1.22*(1-math.cos(t))
 pos=(x,1.10,z)
 yaw=-t*.46
 rounded_box(pos,(.32,.31,.86),.035,'console',yaw,steps=2)
 box((x,1.274,z-.07),(.315,.04,.72),'consoleTop',yaw)
 if i%3!=0:
  box((x,1.298,z-.07),(.29,.015,.65),'texturedLCARS',yaw)
 else:
  box((x,1.298,z-.07),(.27,.015,.62),'texturedSide',yaw)
 # front blank kick panels
 box((x,.74,z-.28),(.32,.63,.09),'wallInner',yaw)
# tactical dark rear monitor band
for i in range(39):
 t=-.95+1.9*(i+.5)/39
 x=5.2*math.sin(t);z=5.86-0.35*math.cos(t)
 yaw=-t*.7
 rounded_box((x,2.33,z),(.36,.55,.12),.015,'black',yaw,steps=2)
 box((x,2.36,z-.074),(.29,.42,.021),'texturedSide',yaw)
# station countertop lip and rail
ridge=[[4.46*math.sin(t),1.34,3.78+1.22*(1-math.cos(t))-0.32] for t in np.linspace(-1.24,1.24,70)]
tube(ridge,.04,'bronze')
# starboard and port Science consoles side walls
for sign in [-1,1]:
 xx=sign*5.45
 bevel_console(xx,.64,-1.55,2.0,.75,.93,yaw=sign*math.pi/2)
 chair(sign*4.72,-1.57,.78,-sign*math.pi/2,seat_y=-.12)
 # far side wall large inset screen bank
 for iz in range(3):
  box((sign*7.12,1.65,-3.06+iz*.88),(.12,.98,.73),'frame')
  box((sign*7.00,1.66,-3.06+iz*.88),(.022,.85,.60),'texturedLCARS')

# rear exit doors: recessed transoms and recognizable paired turbolift panels
for x in [-5.04,5.04]:
 z=4.83
 rounded_box((x,1.71,z),(2.12,2.92,.24),.10,'wallInner')
 rounded_box((x,1.67,z-.145),(1.84,2.61,.10),.06,'bronze')
 rounded_box((x-.43,1.66,z-.202),(.80,2.45,.055),.035,'wallLight')
 rounded_box((x+.43,1.66,z-.202),(.80,2.45,.055),.035,'wallLight')
 box((x,1.66,z-.245),(.028,2.44,.02),'frame')
 for dx in [-.77,.77]:
  box((x+dx,1.37,z-.245),(.033,.72,.026),'frame')
 box((x-.93,2.0,z-.243),(.07,.31,.025),'cyan')
 box((x+.93,2.0,z-.243),(.07,.31,.025),'orange')
 # deep top door panel / number
 box((x,3.17,z), (2.16,.15,.2),'wallLight')

# side exit panel doors
for sign in [-1,1]:
 box((sign*6.77,1.64,2.1),(.17,2.67,1.38),'wallInner')
 box((sign*6.65,1.66,2.1),(.07,2.46,1.04),'wallLight')
 box((sign*6.59,1.65,2.1),(.032,2.46,.045),'frame')

# straight interface rails, lights, panel lines, small details
for x in np.linspace(-6.2,6.2,15):
 if abs(x)<3.9:continue
 box((x,2.83,-5.36),(.20,.035,.25),'lamp')
# decorative sconces around rear wall
for angle in np.linspace(2.15,4.15,10):
 if 2.5<angle<3.8:continue
 panel_at(angle,2.55,.13,.62,'frame')
 panel_at(angle,2.55,.075,.44,'gold',offset=.13)
# thin set-wall red-orange vertical indicators near doors
for x in [-3.86,3.86]:
 box((x,1.87,5.45),(.105,1.43,.045),'black')
 for k in range(9):box((x,1.30+k*.12,5.41),(.055,.054,.02),'orange' if k%2 else 'red')

# create textures with actual tiny labeled graphic elements
try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',18)
except:font=ImageFont.load_default()
try:small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',11)
except:small=font

def save_lcars(name,variant=False):
 img=Image.new('RGB',(1024,512),'#070c13');d=ImageDraw.Draw(img)
 cols=['#db9c66','#bc7c92','#e4c68b','#7ca6bb','#aaa1ce','#c9a26f'];
 d.rounded_rectangle((22,20,1002,82),radius=20,fill=cols[0])
 d.rectangle((120,20,330,82),fill='#080b13');d.rectangle((570,20,748,82),fill='#080b13')
 d.text((145,38),'OPERATIONS  /  CONFIGURATION' if not variant else 'SCIENCE  /  SENSOR ARRAY',font=small,fill='#e7d8c5')
 for j in range(8):
  y=110+j*47
  if j%3==0:d.rounded_rectangle((23,y,206,y+30),radius=8,fill=cols[j%6])
  else:d.rectangle((23,y,206,y+30),fill=cols[(j+2)%6])
  d.text((31,y+7),f'{j+1:02d} / {104+j*13}.4',fill='#11151d',font=small)
  d.rectangle((240,y,997,y+2),fill=cols[(j+1)%6])
  for k in range(19):
   x=260+k*37
   if random.random()<.76:d.rounded_rectangle((x,y+12,x+random.randint(6,23),y+23),radius=2,fill=random.choice(cols))
 for t in range(4):
  d.arc((310+t*12,185+t*12,620-t*12,495-t*12),start=200,end=330,fill=cols[t%6],width=3)
 img.save(P/name,quality=95)

def save_stars():
 img=Image.new('RGB',(1200,520),'#05090f');pixels=img.load();d=ImageDraw.Draw(img)
 rr=random.Random(197)
 for i in range(700):
  x=rr.randrange(1200);y=rr.randrange(520);w=rr.choices([1,2,3],[.79,.19,.02])[0]
  c=rr.choice([(196,202,220),(242,224,207),(171,205,225),(255,255,255)])
  d.ellipse((x,y,x+w,y+w),fill=c)
 for j in range(40):
  x=rr.randrange(1200);y=rr.randrange(520)
  d.point((x,y),fill=(75,98,145))
 img.save(P/'stars.png')
save_lcars('lcars.png');save_lcars('side_screen.png',True);save_stars()

# export model and GLB -- shared geometry, separate glTF scene
meshes=[];scene=trimesh.Scene()
for key,b in B.items():
 p=np.array(b['p'],dtype=np.float32).reshape(-1,3)
 n=np.array(b['n'],dtype=np.float32).reshape(-1,3)
 uv=np.array(b['uv'],dtype=np.float32).reshape(-1,2)
 idx=np.array(b['idx'],dtype=np.uint32).reshape(-1,3)
 if not len(p):continue
 base,em=M[key]
 meshes.append({'name':key,'pos':p.astype(float).round(5).flatten().tolist(), 'normal':n.astype(float).round(5).flatten().tolist(),'uv':uv.astype(float).round(5).flatten().tolist(),'indices':idx.flatten().tolist()})
 mesh=trimesh.Trimesh(vertices=p,faces=idx,process=False)
 matkw={'name':key,'doubleSided':True,'baseColorFactor':list(rgb(base))+[1], 'metallicFactor':.08 if key in ('bronze','rail','metal','metalLight') else 0, 'roughnessFactor':.7 if key not in ('glass','metal') else .4,'emissiveFactor':[min(1,c*em) for c in rgb(base)]}
 if key in TEX:
  matkw['baseColorTexture']=Image.open(P/TEX[key]).convert('RGB');mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=trimesh.visual.material.PBRMaterial(**matkw))
 else: mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=trimesh.visual.material.PBRMaterial(**matkw))
 scene.add_geometry(mesh,node_name=key)
 print(f'{key:17s} {len(p):>7} vertices  {len(idx):>7} triangles')
with (P/'bridge_reference_model.glb').open('wb') as fp:fp.write(scene.export(file_type='glb'))
# use gzip-json for standalone HTML
payload={'materials':{k:{'color':rgb(v[0]),'emissive':v[1],'texture':TEX.get(k)} for k,v in M.items()},'meshes':meshes,'scene':{'title':'Bridge study - reference-guided geometry','copyright':'Original footage remains separately attributed; geometry is manually constructed and approximate'}}
raw=json.dumps(payload,separators=(',',':')).encode();compressed=gzip.compress(raw,compresslevel=7)
(P/'model_payload.b64').write_text(base64.b64encode(compressed).decode())
(P/'model_report.json').write_text(json.dumps({'meshes':len(meshes),'vertices':sum(len(m['pos'])//3 for m in meshes),'triangles':sum(len(m['indices'])//3 for m in meshes),'glb_bytes':(P/'bridge_reference_model.glb').stat().st_size,'raw_json_bytes':len(raw),'compressed_bytes':len(compressed),'reference':'Original Starship Mine 125-130s frames; proportions estimated not surveyed'},indent=2))
print('DONE:',(P/'model_report.json').read_text())
