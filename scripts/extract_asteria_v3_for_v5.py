#!/usr/bin/env python3
"""Recover the actual approved V3 mesh arrays and instrument atlas from a frozen source.

No geometry is recreated from memory: this executes the repository's exact V3
synchronous shape functions in a browser with a no-op WebGL renderer, preserving
all 106,988 original faces. Offline image/geometry capture only; campaign untouched.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import hashlib, subprocess, os, shutil, base64, numpy as np
ROOT=Path(__file__).resolve().parents[1]
V3=ROOT/'ui/3d-preview-v3'
OUT=Path(os.environ.get('ASTERIA_V5_SOURCE_DIR',str(ROOT/'_v5_mesh_capture')))
OUT.mkdir(parents=True,exist_ok=True)
expected='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
current=subprocess.check_output(['git','hash-object',str(V3/'index.html')],cwd=ROOT,text=True).strip()
if current!=expected:
 raise RuntimeError(f'Original V3 geometry changed: {current} (expected {expected}); explicit revalidation required')
html=(V3/'index.html').read_text()
# Optional geometry provenance; never alter the frozen V3 source on disk.
# Mark the exact authored captain's seat span (including its small under-seat
# accent ellipse), not an arbitrary spatial crop that could delete consoles.
capture_chair=os.environ.get("ASTERIA_V3_CAPTURE_CAPTAIN_CHAIR")=="1"
if capture_chair:
 pedestal='ellipse(0,.297,1.14,.48,.55,0x554e5e,1,44);'
 seat='chair(0,1.20,0,true);'
 assert html.count(pedestal)==1 and html.count(seat)==1
 html=html.replace(pedestal,"window.__v3ChairFirstFace=P.length/9;"+pedestal)
 html=html.replace(seat,seat+"window.__v3ChairLastFace=P.length/9;")
# Optional exact draw-call provenance for a NEW isolated command-platform
# architectural candidate. Do not crop a guessed 3D bounding box: that risks
# deleting other consoles, cast floor, movement surfaces and captain's chair.
capture_command=os.environ.get('ASTERIA_V3_CAPTURE_COMMAND_SECTION')=='1'
if capture_command:
 section_points=[
  ("platformStart",
   "if(window.AsteriaHero){window.AsteriaHero.commandPlatform({smoothSurface,box,cyl,ellipse,ring,tube});}",
   "window.__v3CommandPlatformFirst=P.length/9;"),
  ("platformEnd",
   "const shadowCasterStart=P.length/3;",
   "window.__v3CommandPlatformLast=P.length/9;"),
  ("pylonsStart",
   "if(window.AsteriaHero){window.AsteriaHero.commandPylons({smoothSurface,box,tube,surface});}",
   "window.__v3CommandPylonsFirst=P.length/9;"),
  ("pylonsEnd",
   "// Forward continuous flight island, original crescent design with separate seats.",
   "window.__v3CommandPylonsLast=P.length/9;"),
  ("joineryStart",
   "// Command plinth joinery: detailed brass edge lugs, inset upholstery seams and foot-level kick plates.",
   "window.__v3CommandTrimFirst=P.length/9;"),
  ("joineryEnd",
   "const setDressing=(typeof window.AsteriaSetDetails==='function')?",
   "window.__v3CommandTrimLast=P.length/9;"),
 ]
 for name,token,mark in section_points:
  assert html.count(token)==1,(name,html.count(token))
  html=html.replace(token,mark+token)
# Capture one exact existing acoustic wall-decor draw-call span and two original
# ceiling wedges, WITHOUT changing the frozen source bytes or replacing geometry
# based on guessed radius/bounding boxes. Ordinary source builds are unaffected.
capture_bay=os.environ.get('ASTERIA_V3_CAPTURE_INLAID_BAY')=='1'
capture_three=os.environ.get('ASTERIA_V3_CAPTURE_THREE_RIB_BAYS')=='1'
if capture_three:assert capture_bay,'Three-bay capture requires unchanged independent k24 source check'
if capture_bay:
 ceiling_begin="for(let k=0;k<96;k++){const a=k*2*Math.PI/96"
 ceiling_end="k%12===0?0xbcb4ad:0xd3c9bd,2);}"
 api_end="wallPos,W,D}):{pieces:0};"
 for label,token in [('ceiling begin',ceiling_begin),('ceiling end',ceiling_end),
                     ('set-details api',api_end)]:
  assert html.count(token)==1,(label,html.count(token))
 html=html.replace(ceiling_begin,
   "window.__v3BayCeilingRanges=[];"+ceiling_begin.replace(
    "const a=", "if(k===36||k===37)window.__v3BayRoofStart=P.length/9;const a="))
 html=html.replace(ceiling_end,ceiling_end.replace(");}",
   ");if(k===36||k===37)window.__v3BayCeilingRanges.push({name:'ceilingWedge'+k,start:window.__v3BayRoofStart,end:P.length/9});}"))
 html=html.replace(api_end,"wallPos,W,D,faceCount:()=>P.length/9}):{pieces:0};")
needle='window.__asteriaWalkthrough={roomId:'
assert html.count(needle)==1
html=html.replace(needle, "window.__captureV3={positions:P,normals:N,colors:C,materials:M,uv:UV,atlas:atlas.toDataURL('image/png')};"+needle)
for filename in ['hero-v3.js','furniture.js','set-details.js']:
 tag=f'<script src="{filename}"></script>'
 assert tag in html
 raw=(V3/filename).read_text()
 if capture_bay and filename=='set-details.js':
  begin="const wall=wallPos(a,.957);"
  end="  }\n  // Upright structural ribs"
  for label,token in [('bay decoration start',begin),('bay decoration end',end)]:
   assert raw.count(token)==1,(label,raw.count(token))
  extra_start=("if([22,23,24].includes(k)){window.__v3TripleStarts=window.__v3TripleStarts||{};window.__v3TripleStarts[k]=api.faceCount();}" if capture_three else "")
  raw=raw.replace(begin,"if(k===24)window.__v3BayDecorStart=api.faceCount();"+extra_start+begin)
  extra_end=("    if([22,23,24].includes(k)){window.__v3TripleEnds=window.__v3TripleEnds||{};window.__v3TripleEnds[k]=api.faceCount();}\n" if capture_three else "")
  raw=raw.replace(end,"    if(k===24)window.__v3BayDecorEnd=api.faceCount();\n"+extra_end+end)
 html=html.replace(tag,'<script>'+raw+'</script>')
stub="""<script>(()=>{
  const fake=new Proxy({}, {get:(_,k)=>{
    if(k==='getShaderParameter'||k==='getProgramParameter') return ()=>true;
    if(k==='getAttribLocation'||k==='getError')return ()=>0;
    if(k==='checkFramebufferStatus')return ()=>0;
    if(k.startsWith('create'))return ()=>({});
    if(k==='getShaderInfoLog'||k==='getProgramInfoLog')return ()=>'';
    return (...args)=>{};
  }});
  const prev=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'?fake:prev.call(this,type,...args)};
  window.requestAnimationFrame=()=>0;
})()</script>"""
html=html.replace('</head>',stub+'</head>',1)
executable=shutil.which('google-chrome') or shutil.which('chromium') or '/usr/bin/chromium'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':460,'height':340})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='domcontentloaded',timeout=90000)
 page.wait_for_function('window.__captureV3 !== undefined',timeout=90000)
 info=page.evaluate('''() => ({triangles:window.__asteriaWalkthrough.meshTriangles,
 counts:Object.fromEntries(Object.entries(window.__captureV3).filter(([k])=>k!=='atlas').map(([k,v])=>[k,v.length]))})''')
 assert info['triangles']==106988,info
 if capture_chair:
  span=page.evaluate('''() => ({
   start:window.__v3ChairFirstFace,end:window.__v3ChairLastFace
  })''')
  assert all(isinstance(span.get(k),(float,int)) for k in ('start','end')),span
  start,end=int(span['start']),int(span['end'])
  assert start==span['start'] and end==span['end'] and 0<start<end<106988,span
  removed=end-start
  assert 1000<removed<25000, f"Unexpected V3 command seat span: {span}"
  provenance={
   'roomId':'AST-D01-BRIDGE',
   'sourceV3Blob':expected,
   'totalFaces':106988,
   'firstFaceIncluded':start,'lastFaceExcluded':end,
   'captainSeatFaces':removed,
   'sourceCalls':[pedestal,seat],
   'note':'The exact contiguous V3 draw-call range, not a spatial bounding-box crop'
  }
  (OUT/'captain-chair-source-span.json').write_text(
    __import__('json').dumps(provenance,indent=2)+'\n')
  print('V3 captain chair draw-call span',provenance,flush=True)
 if capture_command:
  span=page.evaluate("""() => ({
    platform:[window.__v3CommandPlatformFirst,window.__v3CommandPlatformLast],
    pylons:[window.__v3CommandPylonsFirst,window.__v3CommandPylonsLast],
    trim:[window.__v3CommandTrimFirst,window.__v3CommandTrimLast]
  })""")
  ranges=[]
  for name,positions in span.items():
   a,b=positions
   assert all(isinstance(v,(float,int)) for v in (a,b)),(name,positions)
   assert a==int(a) and b==int(b) and 0<a<b<106988,(name,positions)
   ranges.append({'name':name,'start':int(a),'end':int(b),
                  'faces':int(b-a)})
  ranges.sort(key=lambda row:row['start'])
  assert len(ranges)==3
  for before,after in zip(ranges,ranges[1:]):
   assert before['end']<after['start'],(before,after)
  if capture_chair:
   assert ranges[0]['end']<=start or ranges[0]['start']>=end
   for item in ranges:
    assert item['end']<=start or item['start']>=end, \
        'Command/podium face spans cannot overlap captain chair'
  report={
   'roomId':'AST-D01-BRIDGE',
   'sourceV3Blob':expected,
   'totalFaces':106988,
   'ranges':ranges,
   'commandFaces':sum(x['faces'] for x in ranges),
   'captureMethod':'Exact sequential V3 drawing call boundaries, not spatial cropping',
   'note':'Reference only; world and game collision geometry are not modified.'
  }
  assert 3000<report['commandFaces']<35000,report
  (OUT/'command-section-source-spans.json').write_text(
    __import__('json').dumps(report,indent=2)+'\n')
  print('V3 command platform draw-call face spans',report,flush=True)
 if capture_bay:
  segments=page.evaluate("""() => ({
   decor:[window.__v3BayDecorStart,window.__v3BayDecorEnd],
   ceiling:window.__v3BayCeilingRanges
  })""")
  assert isinstance(segments['decor'],list) and len(segments['decor'])==2,segments
  assert isinstance(segments['ceiling'],list) and len(segments['ceiling'])==2,segments
  ranges=[]
  for name, pair in [('wallBayDecor24',segments['decor'])]+[
      (item['name'],[item['start'],item['end']]) for item in segments['ceiling']]:
   first,last=pair
   assert first==int(first) and last==int(last) and 0<first<last<106988,(name,pair)
   ranges.append({'name':name,'start':int(first),'end':int(last),
                  'faces':int(last-first)})
  ranges.sort(key=lambda item:item['start'])
  for previous,nxt in zip(ranges,ranges[1:]):
   assert previous['end']<=nxt['start'],(previous,nxt)
  assert {v['name'] for v in ranges}=={'wallBayDecor24','ceilingWedge36','ceilingWedge37'}
  assert 4<sum(v['faces'] for v in ranges)<1000
  report={
   'roomId':'AST-D01-BRIDGE','sourceV3Blob':expected,'totalFaces':106988,
   'selectedWallDecorK':24,'selectedCeilingWedges':[36,37],
   'wallAngleRadians':(24.5)*2*__import__('math').pi/64,
   'ceilingAngleSpanRadians':[36*2*__import__('math').pi/96,
                              38*2*__import__('math').pi/96],
   'ranges':ranges,'removedFaces':sum(v['faces'] for v in ranges),
   'method':'exact frozen V3 generator drawing call boundaries, instrumented in memory',
   'structuralWallSubstrateRetained':True,
   'neighborRibsAndConsolesRetained':True,'noSourceEdits':True
  }
  (OUT/'inlaid-bay-source-spans.json').write_text(
     __import__('json').dumps(report,indent=2)+'\n')
  print('MEASURED_INLAID_V3_BAY',report,flush=True)
  if capture_three:
   expanded=page.evaluate("""() => ({
    firsts:window.__v3TripleStarts,
    ends:window.__v3TripleEnds
   })""")
   assert isinstance(expanded['firsts'],dict) and isinstance(expanded['ends'],dict),expanded
   rows=[]
   for k in (22,23,24):
    first=expanded['firsts'].get(str(k))
    last=expanded['ends'].get(str(k))
    assert isinstance(first,(float,int)) and isinstance(last,(float,int)),(k,expanded)
    assert 0<first==int(first)<last==int(last)<106988,(k,first,last)
    assert last-first==58,(k,first,last,'Unexpected original V3 bay size, do not guess')
    rows.append({'name':f'wallBayDecor{k}','bay':k,'start':int(first),
                 'end':int(last),'faces':int(last-first)})
   assert rows[0]['end']==rows[1]['start'] and rows[1]['end']==rows[2]['start'],rows
   single=next(x for x in report['ranges'] if x['name']=='wallBayDecor24')
   assert rows[2]['start']==single['start'] and rows[2]['end']==single['end'],rows
   if capture_chair:
    assert all(entry['end']<=start or entry['start']>=end for entry in rows)
   if capture_command:
    assert all(b['end']<=c['start'] or b['start']>=c['end']
               for b in rows for c in ranges)
   triple={'roomId':'AST-D01-BRIDGE','sourceV3Blob':expected,
    'totalFaces':106988,'selectedWallDecorK':[22,23,24],
    'ranges':rows,'removedFaces':sum(x['faces'] for x in rows),
    'capturedBy':'exact adjacent frozen V3 set-details.js draw-call boundaries, in-memory only',
    'singleBayCrossCheck':'k24 source spans exactly agree with established Stage03',
    'ceilingWedgesRetained':True,'otherGeometryUntouched':True,
    'sourceFilesModified':False}
   assert triple['removedFaces']==174
   (OUT/'three-rib-bays-source-spans.json').write_text(
      __import__('json').dumps(triple,indent=2)+'\n')
   print('MEASURED_THREE_ORIGINAL_WALL_BAYS',triple,flush=True)
 assert not errors,errors
 for key in ['positions','normals','colors','materials','uv']:
  pieces=[];size=160000
  count=info['counts'][key]
  for start in range(0,count,size):
   encoded=page.evaluate('''({key,start,count}) => {
     const v=new Float32Array(window.__captureV3[key].slice(start,start+count));
     const u=new Uint8Array(v.buffer);
     let out='';for(let i=0;i<u.length;i+=8192)out+=String.fromCharCode(...u.subarray(i,i+8192));
     return btoa(out);
   }''',{'key':key,'start':start,'count':min(size,count-start)})
   pieces.append(np.frombuffer(base64.b64decode(encoded),dtype='<f4'))
  np.save(OUT/(key+'.npy'),np.concatenate(pieces))
 atlas=page.evaluate('window.__captureV3.atlas')
 (OUT/'atlas.png').write_bytes(base64.b64decode(atlas.split(',',1)[1]))
 print('Captured original V3',info,'atlas bytes',len((OUT/'atlas.png').read_bytes()),flush=True)
 browser.close()