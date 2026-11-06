#!/usr/bin/env python3
"""Inspect physical browser renders and in-scene first-person movement.

Only marks a preview valid when actual WebGL images render, the original V3
geometry is intact and movement remains in its approved collision boundaries.
"""
from pathlib import Path
import sys,os,threading,functools,http.server,json,time
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=True,parents=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
results=[]
try:
 with sync_playwright() as p:
  executable=os.environ.get('CHROME') or '/usr/bin/google-chrome'
  browser=p.chromium.launch(executable_path=executable,headless=True,
   args=['--no-sandbox','--disable-dev-shm-usage','--enable-webgl',
         '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  # Compare at physically identical camera poses; mobile captured separately.
  for route,views,width,height in [
   ('3d-preview-v5',['aft','command','flight','science'],1280,800),
   ('3d-preview-v3',['aft','command','flight'],1280,800),
   ('3d-preview-v5',['aft'],390,844),
  ]:
   for view in views:
    page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
    page.goto(url+f'{route}/?studioCapture={view}',wait_until='domcontentloaded',timeout=45000)
    page.wait_for_function('document.body.dataset.rendererReady==="true" || document.body.dataset.rendererReady==="error"',timeout=120000)
    page.wait_for_timeout(1000)
    data=page.evaluate('''() => ({ready:document.body.dataset.rendererReady,
     triangles:document.body.dataset.geometryTriangles,
     missing:document.body.dataset.missingMaterials,
     position: window.__asteriaV5?.getPosition()||window.__asteriaWalkthrough?.getPosition()||null,
     frameCount:document.body.dataset.renderedFrames,
     splashHidden:document.getElementById('splash')?.classList.contains('off')})''')
    name=f'{route}-{view}-{width}.png';image=out/name;page.screenshot(path=str(image),timeout=60000)
    pixels=np.asarray(Image.open(image).convert('RGB'),dtype=np.float32)
    std=float(pixels.std(axis=(0,1)).mean())
    data.update({'route':route,'view':view,'imageStd':round(std,2),'file':name,'errors':errors})
    print(json.dumps(data),flush=True);results.append(data)
    assert data['ready']=='true',(data,errors)
    assert std>23,('screenshot too uniform',data)
    assert not errors,errors
    if route=='3d-preview-v5':
     assert int(data['triangles'])==106988 and data['missing']=='0',data
    page.close()
  # Real browser walking (not synthetic direct state injection).
  page=browser.new_page(viewport={'width':860,'height':560})
  page.goto(url+'3d-preview-v5/?studioCapture=aft',wait_until='domcontentloaded',timeout=30000)
  page.wait_for_function('document.body.dataset.rendererReady==="true"',timeout=120000)
  start=page.evaluate('window.__asteriaV5.getPosition()')
  page.keyboard.down('w');page.wait_for_timeout(2200);page.keyboard.up('w')
  after=page.evaluate('window.__asteriaV5.getPosition()')
  page.locator('[data-go="command"]').click()
  command=page.evaluate('window.__asteriaV5.getPosition()')
  print('MOVEMENT',json.dumps({'before':start,'after':after,'command':command}),flush=True)
  assert abs(after['x']-start['x'])+abs(after['z']-start['z'])>.06,('WASD did not advance',start,after)
  assert abs(command['x']+2.32)<.01 and abs(command['z']-2.15)<.01
  page.close();browser.close()
finally:server.shutdown()
(out/'results.json').write_text(json.dumps(results,indent=2))