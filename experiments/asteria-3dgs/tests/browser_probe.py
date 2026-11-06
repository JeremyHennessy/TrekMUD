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
   for view in ('aft','command'):
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
  browser.close()
finally:
 server.shutdown()
(out/'probe.json').write_text(json.dumps(results,indent=2)+'\n')