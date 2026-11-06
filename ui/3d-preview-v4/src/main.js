/* USS Asteria — original TrekMUD ship interior, V4 independent preview.
 * No MUD campaign calls, storage, private GM data or state writes.
 * Three.js 0.187.0, glTF 2.0 PBR mesh assets. MIT Three.js runtime separately licensed.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const canvas = $('scene');
  const fail = message => { $('error').hidden = false; $('error').textContent = message; document.body.dataset.v4Ready = 'error'; };
  const webgl2 = (() => { try { return !!document.createElement('canvas').getContext('webgl2'); } catch { return false; } })();
  if (!webgl2) { fail('This cinematic preview needs a WebGL 2-capable browser. The earlier /3d/ versions are still available.'); return; }
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'});
  } catch (e) { fail(`Unable to start the 3D renderer: ${e.message}`); return; }
  const mobile = matchMedia('(max-width:720px)').matches;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = mobile ? 1.24 : 1.13;
  renderer.shadowMap.enabled = !mobile;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.setClearColor(0x101522,1);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x090f18);
  // PBR reflection environment: restrained studio softbox approximation.
  const pmrem=new THREE.PMREMGenerator(renderer);
  const env=pmrem.fromScene(new RoomEnvironment(),.065);
  scene.environment=env.texture;
  scene.environmentIntensity=.31;
  pmrem.dispose();
  const camera = new THREE.PerspectiveCamera(64,1,.065,160);
  camera.rotation.order = 'YXZ';
  const W=7.55,D=6.55, eyeY=1.69;
  const views={
    aft:{x:-1.38,z:4.91,yaw:.40,pitch:-.095,label:'AFT CORRIDOR ACCESS'},
    command:{x:-2.48,z:2.60,yaw:.20,pitch:-.11,label:'COMMAND PLATFORM'},
    flight:{x:0,z:-1.56,yaw:0,pitch:-.025,label:'FLIGHT CONTROL'},
    science:{x:-4.75,z:2.10,yaw:2.63,pitch:-.045,label:'SCIENCE ANALYSIS'},
    viewer:{x:0,z:-4.84,yaw:0,pitch:.06,label:'FORWARD VIEWSCREEN'}
  };
  let pos={x:views.aft.x,z:views.aft.z,yaw:views.aft.yaw,pitch:views.aft.pitch};
  const pressed=new Set(); let active='aft', last=0,drag=null, joystick=null, joyX=0,joyY=0,ready=false,frameN=0;
  const originalState = { roomId:'AST-D01-BRIDGE', deck:1, neighbors:['AST-D01-HUB-C'], writesCampaign:false };

  function track(el){ el.castShadow=true;el.receiveShadow=true;return el; }
  const hemi = new THREE.HemisphereLight(0xd8e7f4,0x3e3d45,1.20);scene.add(hemi);
  scene.add(new THREE.AmbientLight(0x9eafc0,.21));
  const key = new THREE.DirectionalLight(0xffe1c4,1.86);
  key.position.set(-3.8,7.2,1.2);key.target.position.set(0,.8,0);key.castShadow=!mobile;
  key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-9;key.shadow.camera.right=9;key.shadow.camera.top=8;key.shadow.camera.bottom=-8;key.shadow.camera.near=1;key.shadow.camera.far=23;
  key.shadow.bias=-.0004;key.shadow.normalBias=.035;
  scene.add(key,key.target);
  const fill=new THREE.DirectionalLight(0xa8cbeb,.81);fill.position.set(5.2,3.8,-3.5);scene.add(fill);
  for(const x of [-4.74,4.74]) for(const z of [-4.65,.78,3.45]){
    const light = new THREE.PointLight(0xffdec0,mobile?7:9,5.7,2);
    light.position.set(x,3.75,z);scene.add(light);
  }
  const frontGlow=new THREE.PointLight(0x91b9de,5.3,9.5,2);
  frontGlow.position.set(0,2.30,-5.68);scene.add(frontGlow);
  const rearGlow=new THREE.PointLight(0xffd3a0,5,6,2);
  rearGlow.position.set(0,3.65,5.90);scene.add(rearGlow);

  // Original, layered exterior of a fictional dock, visible only through the ship's forward viewer.
  function random(seed){let k=seed>>>0;return()=>{k=(1664525*k+1013904223)>>>0;return k/4294967296;};}
  const rnd=random(37542);
  function makeSpace(){
    const texCanvas=document.createElement('canvas');texCanvas.width=2048;texCanvas.height=1024;
    const ctx=texCanvas.getContext('2d');
    const grad=ctx.createRadialGradient(1300,560,25,1120,520,1200);
    grad.addColorStop(0,'#131d34');grad.addColorStop(.42,'#091124');grad.addColorStop(1,'#03050e');
    ctx.fillStyle=grad;ctx.fillRect(0,0,2048,1024);
    for(let i=0;i<1500;i++){
      const x=rnd()*2048,y=rnd()*1024,r=(rnd()**6)*1.9+.22;
      const alpha=.18+rnd()*.74;
      ctx.fillStyle=`rgba(${177+Math.floor(rnd()*65)},${199+Math.floor(rnd()*48)},255,${alpha})`;
      ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();
    }
    const texture=new THREE.CanvasTexture(texCanvas);texture.colorSpace=THREE.SRGBColorSpace;
    const bg=new THREE.Mesh(new THREE.PlaneGeometry(110,55),new THREE.MeshBasicMaterial({map:texture,depthWrite:false}));
    bg.position.set(0,2,-90);scene.add(bg);
    const station=new THREE.Group();station.position.set(1.2,1.4,-28);station.rotation.z=.19;scene.add(station);
    const hull=new THREE.MeshStandardMaterial({color:0x75899a,metalness:.73,roughness:.31});
    const dark=new THREE.MeshStandardMaterial({color:0x25384f,metalness:.58,roughness:.46});
    const shine=new THREE.MeshBasicMaterial({color:0xb2d7ef});
    let m=new THREE.Mesh(new THREE.TorusGeometry(3.35,.17,12,128),hull);m.rotation.y=.30;station.add(m);
    m=new THREE.Mesh(new THREE.TorusGeometry(2.73,.08,10,120),dark);m.rotation.y=.30;station.add(m);
    const hub=new THREE.Mesh(new THREE.CylinderGeometry(.78,.90,.63,40),hull);hub.rotation.x=PI/2;station.add(hub);
    const bridgeDock=new THREE.Mesh(new THREE.CylinderGeometry(.44,.65,1.25,40),dark);bridgeDock.rotation.x=PI/2;bridgeDock.position.z=.54;station.add(bridgeDock);
    for(let i=0;i<8;i++){
      const a=2*Math.PI*i/8;
      const beam=new THREE.Mesh(new THREE.BoxGeometry(.14,3.35,.14),hull);
      beam.position.set(Math.sin(a)*1.66,Math.cos(a)*1.66,0);beam.rotation.z=-a;
      station.add(beam);
      const lamp=new THREE.Mesh(new THREE.SphereGeometry(.073,8,8),shine);
      lamp.position.set(3.35*Math.sin(a),3.35*Math.cos(a),.04);station.add(lamp);
    }
    for(let i=0;i<30;i++){
      const a=i*Math.PI*2/30;
      let l=new THREE.Mesh(new THREE.SphereGeometry(.045,7,7),new THREE.MeshBasicMaterial({color:i%3?0xa1cee4:0xf7ca90}));
      l.position.set(3.36*Math.sin(a),3.36*Math.cos(a),.08);station.add(l);
    }
    // Dim distant blue giant to lend real scale to the viewport.
    const planetMat=new THREE.MeshStandardMaterial({color:0x426b92,metalness:0,roughness:1,emissive:0x20375a,emissiveIntensity:.27});
    const planet=new THREE.Mesh(new THREE.SphereGeometry(10,52,26),planetMat);
    planet.position.set(-33,-6,-84);scene.add(planet);
    const rim=new THREE.DirectionalLight(0xb1d7ff,2.5);rim.position.set(-40,16,-40);scene.add(rim);
  }
  const PI=Math.PI;makeSpace();

  const screenMaterials=[];
  function displayTexture(title,index,kind='sensors'){
    const c=document.createElement('canvas');c.width=768;c.height=512;const g=c.getContext('2d');
    const accent=['#a7cbd6','#d9b59c','#adabc9','#aac1b9','#d3b8c7','#e1c3a5'][index%6];
    g.fillStyle='#050d17';g.fillRect(0,0,768,512);
    g.fillStyle='#0d1d2c';g.fillRect(14,14,740,484);
    g.fillStyle=accent;g.fillRect(36,35,16,438);g.fillRect(65,33,264,12);
    g.font='bold 25px ui-monospace,monospace';g.fillText(title,73,103);
    g.font='16px ui-monospace,monospace';g.fillStyle='#93a7b7';g.fillText('USS ASTERIA / NCC-63542',73,136);
    g.strokeStyle='#47637b';g.lineWidth=2;g.strokeRect(75,173,615,241);
    const rr=random(15+index*717);
    if(kind==='sensors'){
      g.strokeStyle=accent;g.lineWidth=2;
      for(let i=0;i<8;i++){
        g.globalAlpha=.50+.4*rr();g.beginPath();
        for(let n=0;n<20;n++){
          const x=95+n*30, y=322-85*Math.sin(n/5+i*.3)*(.25+rr()*.11) +(rr()-.5)*25;
          if(!n)g.moveTo(x,y);else g.lineTo(x,y);
        }g.stroke();
      }g.globalAlpha=1;
    }else{
      for(let i=0;i<11;i++){
        const y=193+i*19;g.fillStyle=i%2?accent:'#56778b';
        g.fillRect(100,y,120+rr()*380,7);
      }
    }
    for(let i=0;i<12;i++){
      g.fillStyle=i%3===0?accent:'#536f85';g.fillRect(72+i*52,448,30,15);
    }
    const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;
    tex.anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),4);
    return tex;
  }
  function addFlightScreens(){
    const labels=['HELM CONTROL','NAVIGATION','ARRAY STATUS','MISSION OPERATIONS','TACTICAL STATUS','SHIP SYSTEMS'];
    for(let i=0;i<6;i++){
      const x=-2.28+(4.56/5)*i;
      const z=-3.72+.25*(x/2.76)**2;
      const mat=new THREE.MeshStandardMaterial({map:displayTexture(labels[i],i),emissive:0xffffff,emissiveMap:displayTexture(labels[i],i),emissiveIntensity:.64,metalness:0,roughness:.28,side:THREE.DoubleSide});
      const plane=new THREE.Mesh(new THREE.PlaneGeometry(.70,.79),mat);
      plane.position.set(x,1.058,z-.256);
      plane.rotation.x=-1.265;
      scene.add(plane);screenMaterials.push(plane);
    }
  }
  function addAftScreens(){
    const labels=['LONG RANGE SENSOR','SCIENCE DATA','COMMS & RELAY','DORSAL POD','STELLAR ANALYSIS','ENGINEERING LINK'];
    for(const sign of [-1,1])for(let k=0;k<3;k++){
      const x=sign*(2+k*1.22);
      const tex=displayTexture(labels[k+(sign===1?3:0)],k+6,'systems');
      const mat=new THREE.MeshStandardMaterial({map:tex,emissive:0x8aaabd,emissiveMap:tex,emissiveIntensity:.55,metalness:.0,roughness:.33,side:THREE.DoubleSide});
      const plane=new THREE.Mesh(new THREE.PlaneGeometry(.85,1.20),mat);
      plane.position.set(x,2.20,5.815);plane.rotation.y=PI;scene.add(plane);screenMaterials.push(plane);
    }
  }
  function addSideTables(){
    for(const s of [-1,1]) for(let j=0;j<4;j++){
      const x=s*(2.46+j*.90),z=4.10+.20*Math.sin(j*Math.PI/3);
      const tex=displayTexture('SCIENCE / ANALYSIS',j+12,'systems');
      const mat=new THREE.MeshStandardMaterial({map:tex,emissive:0xa6cde3,emissiveMap:tex,emissiveIntensity:.50,metalness:0,roughness:.32,side:THREE.DoubleSide});
      const plane=new THREE.Mesh(new THREE.PlaneGeometry(.62,.60),mat);
      plane.rotation.x=-PI/2;plane.rotation.z=s*.10;
      plane.position.set(x,1.181,z-.22);
      scene.add(plane);screenMaterials.push(plane);
    }
  }
  addFlightScreens();addAftScreens();addSideTables();

  function block(x,z){
    if((x/W)**2+(z/D)**2>.82) return true;
    if(Math.abs(x)<2.98 && z< -3.03 && z>-4.48) return true;
    if(Math.hypot(x,z-1.22)<.67)return true;
    if(Math.abs(x)>1.03&&Math.abs(x)<1.75 && z>.05&&z<1.30)return true;
    if(Math.abs(x)>2.15&&Math.abs(x)<5.70 && z>3.56&&z<4.92)return true;
    return false;
  }
  function resetAt(view){
    const v=views[view];if(!v)return;
    Object.assign(pos,{x:v.x,z:v.z,yaw:v.yaw,pitch:v.pitch});active=view;
    $('zoneLabel').textContent=v.label;
    document.querySelectorAll('[data-place]').forEach(el=>el.classList.toggle('active',el.dataset.place===view));
    syncCamera();drawMinimap();
  }
  function syncCamera(){camera.position.set(pos.x,eyeY,pos.z);camera.rotation.set(pos.pitch,pos.yaw,0,'YXZ');}
  function move(forward,side,dt){
    const speed=(pressed.has('shift')?4.4:2.38)*dt;
    const x=(Math.sin(pos.yaw)*forward+Math.cos(pos.yaw)*side)*speed;
    const z=(-Math.cos(pos.yaw)*forward+Math.sin(pos.yaw)*side)*speed;
    if(!block(pos.x+x,pos.z))pos.x+=x;
    if(!block(pos.x,pos.z+z))pos.z+=z;
  }
  function frame(time){
    requestAnimationFrame(frame);
    const dt=Math.min(.04,(time-last)/1000 || .016);last=time;
    const f=(pressed.has('w')||pressed.has('arrowup')?1:0)-(pressed.has('s')||pressed.has('arrowdown')?1:0)-joyY;
    const side=(pressed.has('d')||pressed.has('arrowright')?1:0)-(pressed.has('a')||pressed.has('arrowleft')?1:0)+joyX;
    const norm=Math.hypot(f,side);
    if(norm>.001)move(f/norm,side/norm,dt);
    syncCamera();document.body.dataset.frameAttempt=String(frameN+1);
    try { renderer.render(scene,camera); } catch(e) { fail("WebGL scene render failed: "+e.message); return; }
    drawMinimap();
    if(ready){frameN++; document.body.dataset.renderedFrames=String(frameN);
      if(frameN===1){document.body.dataset.v4Ready='true';document.body.dataset.renderTriangles=String(renderer.info.render.triangles);}
    }
  }
  function resize(){
    const w=Math.max(1,canvas.clientWidth),h=Math.max(1,canvas.clientHeight);
    const dpr=Math.min(window.devicePixelRatio||1,mobile?1.2:1.55);
    renderer.setPixelRatio(dpr);renderer.setSize(w,h,false);
    camera.aspect=w/h;camera.updateProjectionMatrix();
  }
  const m=$('map').getContext('2d');
  function drawMinimap(){
    const w=300,h=220,X=x=>150+x*13.2,Y=z=>112+z*13.2;
    m.clearRect(0,0,w,h);
    m.strokeStyle='#829ca3';m.lineWidth=2.5;m.beginPath();m.ellipse(150,112,W*13.2,D*13.2,0,0,2*PI);m.stroke();
    m.fillStyle='#a59daa';m.beginPath();m.ellipse(150,Y(.96),2.24*13.2,1.86*13.2,0,0,2*PI);m.fill();
    m.fillStyle='#a5b4c2';m.fillRect(X(-2.96),Y(-3.72),5.92*13.2,12);
    m.fillStyle='#d9b393';m.fillRect(X(-1.14),Y(6.1),2.28*13.2,7);
    m.fillStyle='#8dcab5';m.beginPath();m.arc(X(pos.x),Y(pos.z),5.2,0,2*PI);m.fill();
    m.strokeStyle='#8dcab5';m.lineWidth=2;m.beginPath();m.moveTo(X(pos.x),Y(pos.z));m.lineTo(X(pos.x+Math.sin(pos.yaw)),Y(pos.z-Math.cos(pos.yaw)));m.stroke();
    m.font='10px system-ui';m.fillStyle='#d8d8dd';m.fillText('FWD',140,25);
  }
  canvas.addEventListener('pointerdown',e=>{drag={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{
    if(!drag||drag.id!==e.pointerId)return;
    pos.yaw-=(e.clientX-drag.x)*.0044;
    pos.pitch=THREE.MathUtils.clamp(pos.pitch-(e.clientY-drag.y)*.0033,-1.05,1.05);
    drag.x=e.clientX;drag.y=e.clientY;
  });
  for(const type of ['pointerup','pointercancel','lostpointercapture']) canvas.addEventListener(type,e=>{if(drag?.id===e.pointerId)drag=null;});
  window.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright','shift','r'].includes(k))e.preventDefault();pressed.add(k);if(k==='r')resetAt('aft');});
  window.addEventListener('keyup',e=>pressed.delete(e.key.toLowerCase()));
  window.addEventListener('blur',()=>pressed.clear());
  window.addEventListener('resize',resize);
  document.querySelectorAll('[data-place]').forEach(btn=>btn.addEventListener('click',()=>resetAt(btn.dataset.place)));
  $('enter').addEventListener('click',()=>{$('curtain').classList.add('off');});
  const pad=$('mobilePad'),thumb=$('mobileThumb');
  function setPad(e){const r=pad.getBoundingClientRect(),dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2),norm=Math.max(1,Math.hypot(dx,dy)/38);joyX=dx/norm/38;joyY=dy/norm/38;thumb.style.transform=`translate(${joyX*33}px,${joyY*33}px)`;}
  pad.addEventListener('pointerdown',e=>{joystick=e.pointerId;pad.setPointerCapture(e.pointerId);setPad(e);});
  pad.addEventListener('pointermove',e=>{if(e.pointerId===joystick)setPad(e);});
  for(const type of ['pointerup','pointercancel','lostpointercapture'])pad.addEventListener(type,e=>{if(e.pointerId===joystick){joystick=null;joyX=joyY=0;thumb.style.transform='translate(0,0)';}});

  const load=new GLTFLoader();
  load.load('./models/asteria-bridge-shell.glb', gltf=>{
    const group=gltf.scene;group.name='ASTERIA_BRIDGE_V4';
    let triangles=0,models=0,missing=0;
    group.traverse(o=>{
      if(o.isMesh){o.castShadow=!mobile;o.receiveShadow=true;models++;
        const geo=o.geometry;if(geo?.index)triangles+=geo.index.count/3;else if(geo?.attributes?.position)triangles+=geo.attributes.position.count/3;
        if(!o.material)missing++;
        if(o.material && !o.material.normalMap && !o.name.includes('Screen')){ /* texture maps vary by asset type */ }
      }
    });
    scene.add(group);
    window.__asteriaV4={...originalState,render:'three-r187-glb-pbr',getPosition:()=>({...pos}),resetAt,block,materials:group.children.filter(x=>x.isMesh).length,triangleCount:triangles,meshCount:models};
    document.body.dataset.scene='loaded';document.body.dataset.glbMeshes=String(models);document.body.dataset.glbTriangles=String(Math.floor(triangles));document.body.dataset.webglVersion='2';
    document.body.dataset.missingMaterial=String(missing);
    $('stateLabel').textContent='Deck 01 · Scene ready';
    ready=true;
    const choice=new URLSearchParams(location.search).get('capture');
    if(choice){resetAt(views[choice]?choice:'aft');$('curtain').classList.add('off');}
    resize();requestAnimationFrame(frame);
  }, undefined, err=>{fail('The V4 3D asset could not be loaded: '+(err.message||String(err)));});
  resize();resetAt('aft');
})();