#!/usr/bin/env python3
"""Genuine Chromium WebGL Stage40 first-art visual gate (not release acceptance)."""
from pathlib import Path
import argparse,functools,http.server,hashlib,json,os,shutil,threading
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

SHOTS=(('desktop',1280,800),('mobile',390,844))
EXPECTED={"app.js","models/asteria-v3-restored-pbr.glb","models/manifest.json",
          "models/asteria-realistic-architectural-envelope-08.glb","models/envelope-manifest.json"}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main(root,out):
    before=root/'control';after=root/'candidate'
    a={p.relative_to(before).as_posix():digest(p) for p in before.rglob('*') if p.is_file()}
    b={p.relative_to(after).as_posix():digest(p) for p in after.rglob('*') if p.is_file()}
    assert set(a)==set(b)
    assert {x for x in a if a[x]!=b[x]}==EXPECTED
    assert a['models/asteria-hero-chair-candidate.glb']==b['models/asteria-hero-chair-candidate.glb']
    assert a['index.html']==b['index.html']
    source=(after/'models/manifest.json')
    meta=json.loads(source.read_text());assert meta['triangles']==48150
    assert meta['stage40_original_pilot_faces_removed']==32600
    env=json.loads((after/'models/envelope-manifest.json').read_text())
    assert env['newEnvelopeTriangles']==93288 and env['meshObjects']==241
    trial=env['stage40IntegratedCommandZoneTrial']
    assert trial['pilotInstances']==2 and trial['pilotTriangles']==62968
    assert trial['removedOldPortal29DrawNodes']==16
    assert trial['originalEnvelopeBinaryUnchanged'] and not trial['artisticallyApproved']
    out.mkdir(parents=True,exist_ok=True)
    serve=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
    thread=threading.Thread(target=serve.serve_forever,daemon=True);thread.start()
    baseurl='http://127.0.0.1:'+str(serve.server_port)
    report={'id':'ASTERIA_STAGE40_TRUE_CHROMIUM_MATCHED_ART_FIRST',
            'modelSHA256':b['models/asteria-realistic-architectural-envelope-08.glb'],
            'changedFiles':sorted(EXPECTED),'artApproved':False,'fullReleaseQAPassed':False,'views':{}}
    try:
        with sync_playwright() as pw:
            chromium=os.environ.get('CHROME') or shutil.which('google-chrome') or shutil.which('chromium')
            assert chromium,'Chromium browser is mandatory'
            browser=pw.chromium.launch(executable_path=chromium,headless=True,args=[
                '--no-sandbox','--disable-dev-shm-usage','--enable-webgl',
                '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
            for name,w,h in SHOTS:
                views={}
                for route in ('control','candidate'):
                    page=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1,has_touch=w<500)
                    errors=[];urls=[];http_errors=[]
                    page.on('pageerror',lambda err:errors.append(str(err)))
                    page.on('response',lambda resp:http_errors.append((resp.status,resp.url)) if resp.status>=400 else None)
                    page.on('request',lambda r:urls.append(r.url))
                    status=page.goto(f'{baseurl}/{route}/?studioCapture=command',wait_until='domcontentloaded',timeout=60000)
                    assert status and status.status==200
                    page.wait_for_function("document.body.dataset.rendererReady==='true'||document.body.dataset.rendererReady==='error'",timeout=120000)
                    page.wait_for_function("document.body.dataset.threeBayLoaded==='true'||document.body.dataset.rendererReady==='error'",timeout=120000)
                    page.wait_for_function("document.body.dataset.envelopeLoaded==='true'||document.body.dataset.rendererReady==='error'",timeout=180000)
                    page.wait_for_function("Number(document.body.dataset.renderedFrames||0)>=4",timeout=90000)
                    state=page.evaluate('''() => ({ready:document.body.dataset.rendererReady,error:document.getElementById('error')?.textContent||'',
                      room:window.__asteriaV5?.roomId,source:window.__asteriaV5?.sourceV3Sha,
                      writes:window.__asteriaV5?.changesCampaign,triangles:Number(document.body.dataset.geometryTriangles),
                      hero:Number(document.body.dataset.heroChairFaces),envelope:document.body.dataset.envelopeLoaded,
                      loaded:document.body.dataset.threeBayLoaded,frames:Number(document.body.dataset.renderedFrames)})''')
                    assert state['ready']=='true' and not state['error'],(route,state)
                    assert state['room']=='AST-D01-BRIDGE' and not state['writes']
                    assert state['source']=='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
                    assert state['triangles']==(48150 if route=='candidate' else 80846)
                    assert state['hero']==31484 and state['envelope']==state['loaded']=='true'
                    assert not errors and not http_errors,(route,errors,http_errors)
                    assert len({u for u in urls if u.endswith('.glb')})==5
                    path=out/f'command-{name}-{route}-{w}x{h}.png'
                    page.screenshot(path=str(path),timeout=60000)
                    views[route]=Image.open(path).convert('RGB')
                    page.close()
                before_arr=np.asarray(views['control'],dtype=np.int16)
                after_arr=np.asarray(views['candidate'],dtype=np.int16)
                changed=np.abs(before_arr-after_arr).max(axis=2)>10
                centered=changed[:,int(w*.2):int(w*.8)]
                quarters=[round(float(chunk.mean()*100),3) for chunk in np.array_split(changed,4,axis=0)]
                composite=Image.new('RGB',(w*2,h));composite.paste(views['control'],(0,0));composite.paste(views['candidate'],(w,0))
                composite.save(out/f'command-{name}-actual-before-after.jpg',quality=92)
                report['views'][name]={'viewport':[w,h], 'changedRGBOver10Percent':round(float(changed.mean()*100),4),
                       'center60PercentChanged':round(float(centered.mean()*100),4),'verticalQuarters':quarters,
                       'realBrowserWithoutErrors':True,'humanArtVerdict':'PENDING'}
            browser.close()
    finally:
        serve.shutdown()
    (out/'stage40-browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('STAGE40_GENUINE_BROWSER_ART_FIRST',json.dumps(report),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for key in ('root','out'):ap.add_argument('--'+key,required=True,type=Path)
    args=ap.parse_args();main(args.root,args.out)