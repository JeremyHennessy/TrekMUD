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
needle='window.__asteriaWalkthrough={roomId:'
assert html.count(needle)==1
html=html.replace(needle, "window.__captureV3={positions:P,normals:N,colors:C,materials:M,uv:UV,atlas:atlas.toDataURL('image/png')};"+needle)
for filename in ['hero-v3.js','furniture.js','set-details.js']:
 tag=f'<script src="{filename}"></script>'
 assert tag in html
 html=html.replace(tag,'<script>'+(V3/filename).read_text()+'</script>')
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