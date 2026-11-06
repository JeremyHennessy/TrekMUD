#!/usr/bin/env python3
"""A/B screenshot validation for independent synthetic Spark/GLB Asteria trial."""
from pathlib import Path
import json, os, time, threading, functools, http.server, sys
from PIL import Image, ImageStat
import numpy as np
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=True,parents=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
results=[]
try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(executable_path=os.getenv('CHROME','/usr/bin/google-chrome'),headless=True,
    args=['--no-sandbox','--disable-dev-shm-usage','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for mode in ('mesh','splat'):
   for view in ('aft','command','chairClose'):
    p=browser.new_page(viewport={'width':1024,'height':640},device_scale_factor=1)
    errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.goto(url+f'?capture={view}&chair={mode}',wait_until='domcontentloaded',timeout=30000)
    p.wait_for_function('document.body.dataset.v4Ready==="true" || document.body.dataset.v4Ready==="error"',timeout=120000)
    if mode=='splat':p.wait_for_function('document.body.dataset.splatReady==="true" || document.body.dataset.splatReady==="error"',timeout=120000)
    p.wait_for_timeout(1000)
    path=out/f'{view}-{mode}.png';p.screenshot(path=str(path))
    d=p.evaluate('''() => ({v4:document.body.dataset.v4Ready,splat:document.body.dataset.splatReady,
      chair:document.body.dataset.hybridMode,glbMeshes:document.body.dataset.glbMeshes,frames:document.body.dataset.renderedFrames,
      camera:window.__asteriaV4?.getPosition()||null, error:document.querySelector('#error')?.textContent||null})''')
    im=Image.open(path).convert('RGB');gray=np.asarray(im,dtype=np.uint8)
    std=float(gray.std(axis=(0,1)).mean());d.update({'mode':mode,'view':view,'errors':errors,'imageStd':round(std,2),'path':path.name})
    results.append(d);print(json.dumps(d),flush=True)
    assert d['v4']=='true' and d['glbMeshes'] is not None,(mode,view,d)
    if mode=='splat': assert d['splat']=='true',(mode,view,d)
    assert not errors,(mode,view,errors)
    assert std>22,(mode,view,'blank screenshot')
    p.close()
  # Separate depth/occlusion diagnostic. If a splat doesn't appear here, the problem
  # is the splat encoding/renderer rather than the existing Asteria meshes.
  p=browser.new_page(viewport={'width':1024,'height':640},device_scale_factor=1)
  errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  p.goto(url+'?capture=chairClose&chair=splat&splatOnly=1',wait_until='domcontentloaded',timeout=30000)
  p.wait_for_function('document.body.dataset.splatReady==="true" || document.body.dataset.splatReady==="error"',timeout=120000)
  p.wait_for_timeout(1100)
  iso_path=out/'isolated-chair-splat.png';p.screenshot(path=str(iso_path))
  info=p.evaluate('''() => ({splat:document.body.dataset.splatReady,splatCount:document.body.dataset.splatCount,
    debug:window.__asteriaSplatDebug, error:document.querySelector('#error')?.textContent||null})''')
  info.update({'mode':'isolated','errors':errors,'path':iso_path.name})
  arr=np.asarray(Image.open(iso_path).convert('RGB'),dtype=np.uint8)
  info['imageStd']=float(arr.std(axis=(0,1)).mean())
  results.append(info);print(json.dumps(info),flush=True)
  assert info['splat']=='true' and int(info.get('splatCount') or 0)>10000 and not errors
  # Do not assert presence of non-background pixels until checking whether the
  # client has a valid depth/alpha render; the captured image is the visual evidence.
  p.close()
  # Positive control: an independently generated turquoise 13x13 Gaussian patch.
  # This is not part of the ship; it discriminates renderer failure from bad .splat bytes.
  p=browser.new_page(viewport={'width':1024,'height':640},device_scale_factor=1)
  control_errors=[];p.on('pageerror',lambda e:control_errors.append(str(e)))
  p.goto(url+'?capture=chairClose&chair=splat&splatOnly=1&controlSplat=1',
         wait_until='domcontentloaded',timeout=30000)
  p.wait_for_function('document.body.dataset.controlReady==="true" || document.body.dataset.controlReady==="error"',timeout=120000)
  p.wait_for_timeout(2200)
  control_path=out/'isolated-procedural-control.png';p.screenshot(path=str(control_path))
  cinfo=p.evaluate("""() => ({controlReady:document.body.dataset.controlReady,
    controlCount:document.body.dataset.controlCount,splatCount:document.body.dataset.splatCount,
    frames:document.body.dataset.renderedFrames,
    error:document.querySelector('#error')?.textContent||null})""")
  pixels=np.asarray(Image.open(control_path).convert('RGB')).astype(np.int32)
  roi=pixels[145:450,280:750]
  cyan=(roi[:,:,1]>145)&(roi[:,:,1]>roi[:,:,0]*1.5)&(roi[:,:,2]>roi[:,:,0]*1.4)
  cinfo.update({'mode':'procedural-control','path':control_path.name,
    'cyanPixels':int(cyan.sum()),'errors':control_errors})
  results.append(cinfo);print(json.dumps(cinfo),flush=True)
  assert not control_errors
  assert cinfo['controlReady']=='true' and int(cinfo.get('controlCount') or 0)>100
  # A renderer success requires actual visible cyan pixels, not just loading.
  assert cinfo['cyanPixels']>100,'Known-good Gaussian patch is invisible: renderer path not validated'
  p.close()
  browser.close()
finally:
 server.shutdown()
(out/'probe.json').write_text(json.dumps(results,indent=2)+'\n')