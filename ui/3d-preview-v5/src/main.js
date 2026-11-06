/* Original USS Asteria, restored from exact approved-ish V3 set geometry.
 * Mesh source hash 74a154ae62bccb0c16d03c2ecf791a64ab19ce81.
 * Assets and controls are view-only. No MUD state, storage or hidden GM access.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const canvas=$('scene');
  const mobile=matchMedia('(max-width:760px)').matches;
  const params=new URLSearchParams(location.search);
  const W=7.55,D=6.55,eyeY=1.67;
  const fail=msg=>{$('loading').classList.add('off');$('error').style.display='grid';$('error').textContent=msg;document.body.dataset.rendererReady='error';};
  let renderer;
  try {
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance',alpha:false});
  } catch(err) {fail('The WebGL renderer cannot start: '+String(err.message||err));return;}
  renderer.setClearColor(0x11121d,1);
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=mobile?.94:1.01;
  renderer.shadowMap.enabled=!mobile&&params.get('shadows')!=='off';
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  const scene=new THREE.Scene();scene.background=new THREE.Color(0x0d0e17);
  // Restrained studio reflection, not the overbright V4 environment profile.
  try {
    const pmrem=new THREE.PMREMGenerator(renderer);
    const env=pmrem.fromScene(new RoomEnvironment(),.065);
    scene.environment=env.texture;scene.environmentIntensity=.21;
    pmrem.dispose();
  }catch(err){console.warn('Reflection environment unavailable; using material lighting.',err);}

  // Wide, soft key above the command island; cool light toward flight consoles.
  scene.add(new THREE.HemisphereLight(0xf3ebdf,0x38465b,.90));
  scene.add(new THREE.AmbientLight(0xbab6b2,.17));
  const key=new THREE.DirectionalLight(0xffe8d4,1.25);
  key.position.set(-4.6,7.5,1.8);key.target.position.set(0,.65,-.2);
  key.castShadow=renderer.shadowMap.enabled;
  key.shadow.mapSize.set(2048,2048);
  key.shadow.camera.left=-9;key.shadow.camera.right=9;
  key.shadow.camera.top=9;key.shadow.camera.bottom=-9;
  key.shadow.camera.near=.5;key.shadow.camera.far=25;
  key.shadow.bias=-.0005;key.shadow.normalBias=.055;
  key.shadow.radius=4;
  scene.add(key,key.target);
  const cool=new THREE.DirectionalLight(0x94b6d5,.45);
  cool.position.set(5.4,4.2,-4.8);scene.add(cool);
  for(const x of [-3.4,3.4])for(const z of [-3.4,1.35,4.05]){
    const lamp=new THREE.SpotLight(0xffdfc4,5.1,11,Math.PI/3,.94,2);
    lamp.position.set(x,4.07,z);
    lamp.target.position.set(x*.74,0,z*.82);
    scene.add(lamp,lamp.target);
  }
  const instrumentFill=new THREE.PointLight(0x8fb9d6,3.0,6.8,2);
  instrumentFill.position.set(0,2.2,-4.6);scene.add(instrumentFill);

  // Use V3's exact physical camera viewpoints and collision logic.
  const views={
    aft:{x:-1.23,z:4.80,yaw:.44,label:'AFT CORRIDOR ACCESS · DECK 01'},
    command:{x:-2.32,z:2.15,yaw:.22,label:'COMMAND PLATFORM'},
    flight:{x:0,z:-1.32,yaw:0,label:'FLIGHT CONTROL'},
    science:{x:-3.70,z:2.76,yaw:2.8,label:'SCIENCE GALLERY'},
    viewer:{x:0,z:-4.78,yaw:Math.PI,label:'FORWARD VIEWSCREEN'}
  };
  const camera=new THREE.PerspectiveCamera(65,1,.07,70);
  camera.rotation.order='YXZ';
  const pos={x:views.aft.x,z:views.aft.z,yaw:views.aft.yaw,pitch:-.14};
  let last=0, ready=false,frames=0,drag=null,stick=null,stickX=0,stickY=0, active='aft';
  const pressed=new Set();
  function blocked(x,z){
    if((x/W)**2+(z/D)**2>.845) return true;
    if(Math.abs(x)<2.95&&z>-3.90&&z<-2.72)return true;
    if(Math.abs(x)<.62&&z>.42&&z<1.80)return true;
    if(Math.abs(x)>3.58&&Math.abs(x)<5.12&&z>-3.01&&z<-.54)return true;
    if(Math.abs(x)>1.85&&Math.abs(x)<5.45&&z>3.69&&z<5.28)return true;
    return false;
  }
  function move(dx,dz){const nx=pos.x+dx,nz=pos.z+dz;if(!blocked(nx,pos.z))pos.x=nx;if(!blocked(pos.x,nz))pos.z=nz;}
  function resetAt(name){
    const p=views[name];if(!p)return;
    Object.assign(pos,{x:p.x,z:p.z,yaw:p.yaw,pitch:-.14});active=name;
    document.querySelectorAll('[data-go]').forEach(b=>b.classList.toggle('active',b.dataset.go===name));
    $('place').textContent=p.label;$('place').style.opacity='1';
    if(!params.has('studioCapture'))setTimeout(()=>{if($('place').textContent===p.label)$('place').style.opacity='0';},1700);
  }
  function resize(){const w=Math.max(1,canvas.clientWidth),h=Math.max(1,canvas.clientHeight),dpr=Math.min(window.devicePixelRatio||1,mobile?1.1:1.35);renderer.setPixelRatio(dpr);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
  function syncCamera(){
    camera.position.set(pos.x,eyeY,pos.z);
    // Three.js positive yaw faces left; original V3's positive yaw faces right.
    camera.rotation.set(pos.pitch,-pos.yaw,0,'YXZ');
  }
  const map=$('minimap'),mc=map.getContext('2d');
  function minimap(){const w=392,h=310,X=x=>w/2+x*21,Y=z=>h/2+z*19;
    mc.clearRect(0,0,w,h);mc.save();mc.strokeStyle='#9ba4b7';mc.lineWidth=3;mc.beginPath();mc.ellipse(X(0),Y(0),W*21,D*19,0,0,2*Math.PI);mc.stroke();
    mc.fillStyle='#756b83';mc.beginPath();mc.ellipse(X(0),Y(1.11),1.88*21,1.57*19,0,0,2*Math.PI);mc.fill();
    mc.fillStyle='#9ba3b0';mc.fillRect(X(-2.9),Y(-3.5),5.8*21,22);mc.fillRect(X(-4.9),Y(4.12),3*21,19);mc.fillRect(X(2.0),Y(4.12),3*21,19);
    mc.fillStyle='#d1b499';mc.fillRect(X(-1.0),Y(6.05),2*21,8);mc.fillRect(X(-3.15),Y(-6.16),6.3*21,5);
    mc.fillStyle='#dec9ba';mc.font='14px system-ui';mc.fillText('FWD',X(-.6),Y(-5.45));mc.fillStyle='#e8b793';mc.beginPath();mc.arc(X(pos.x),Y(pos.z),6.5,0,2*Math.PI);mc.fill();
    mc.strokeStyle='#e8b793';mc.lineWidth=3;mc.beginPath();mc.moveTo(X(pos.x),Y(pos.z));mc.lineTo(X(pos.x+Math.sin(pos.yaw)*.72),Y(pos.z-Math.cos(pos.yaw)*.72));mc.stroke();mc.restore();
  }
  // Small painted contact shadows anchor seating and workstations without altering meshes.
  function contactShadowTexture(){
    const c=document.createElement('canvas');c.width=c.height=256;const ctx=c.getContext('2d');
    const g=ctx.createRadialGradient(128,128,8,128,128,124);
    g.addColorStop(0,'rgba(20,18,31,.37)');g.addColorStop(.38,'rgba(20,18,31,.20)');g.addColorStop(1,'rgba(20,18,31,0)');
    ctx.fillStyle=g;ctx.fillRect(0,0,256,256);return new THREE.CanvasTexture(c);
  }
  const contact=contactShadowTexture();
  const spotMat=new THREE.MeshBasicMaterial({map:contact,transparent:true,opacity:.55,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,side:THREE.DoubleSide});
  for(const [x,y,z,rx,rz] of [[0,.304,1.2,1.15,.86],[-1.15,.042,-2.08,.70,.55],[1.15,.042,-2.08,.70,.55],[-3.45,.43,4.18,.72,.40],[3.45,.43,4.18,.72,.4]]){
    const m=new THREE.Mesh(new THREE.PlaneGeometry(rx*2,rz*2),spotMat);m.rotation.x=-Math.PI/2;m.position.set(x,y,z);m.renderOrder=7;scene.add(m);
  }
  function frame(ts){
    requestAnimationFrame(frame);
    const dt=Math.min(.05,(ts-last)/1000||.016);last=ts;
    const f=(pressed.has('w')||pressed.has('arrowup')?1:0)-(pressed.has('s')||pressed.has('arrowdown')?1:0)-stickY;
    const side=(pressed.has('d')||pressed.has('arrowright')?1:0)-(pressed.has('a')||pressed.has('arrowleft')?1:0)+stickX;
    const v=Math.hypot(f,side);
    if(v>.001){const speed=(pressed.has('shift')?4.6:2.35)*dt/v;move((Math.sin(pos.yaw)*f+Math.cos(pos.yaw)*side)*speed,(-Math.cos(pos.yaw)*f+Math.sin(pos.yaw)*side)*speed);}
    syncCamera();renderer.render(scene,camera);minimap();
    if(ready){frames++;document.body.dataset.renderedFrames=String(frames);if(frames===1){document.body.dataset.rendererReady='true';document.body.dataset.v5GeometryTriangles=String(106988);}}
  }
  canvas.addEventListener('pointerdown',e=>{if(!drag){drag={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);}});
  canvas.addEventListener('pointermove',e=>{if(!drag||drag.id!==e.pointerId)return;pos.yaw+=(e.clientX-drag.x)*.0043;pos.pitch=THREE.MathUtils.clamp(pos.pitch-(e.clientY-drag.y)*.0037,-1.29,1.29);drag.x=e.clientX;drag.y=e.clientY;});
  for(const ev of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(ev,e=>{if(drag?.id===e.pointerId)drag=null;});
  window.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright','shift','r','h'].includes(k))e.preventDefault();pressed.add(k);if(k==='r')resetAt('aft');if(k==='h')toggleUi();});
  window.addEventListener('keyup',e=>pressed.delete(e.key.toLowerCase()));window.addEventListener('blur',()=>pressed.clear());
  function toggleUi(){const hidden=document.body.classList.toggle('hideHud');for(const id of ['mast','topTitle','panel','waypoints','notice'])$(id).style.display=hidden?'none':'';$('hide').textContent=hidden?'SHOW HUD':'HIDE HUD';}
  $('hide').addEventListener('click',toggleUi);$('full').addEventListener('click',()=>{if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen?.();});
  document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>resetAt(b.dataset.go)));
  $('enter').addEventListener('click',()=>{$('splash').classList.add('off');});
  const pad=$('stick'),nub=$('thumb');
  function padMove(e){const r=pad.getBoundingClientRect(),dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2),q=Math.min(1,48/(Math.hypot(dx,dy)||1));stickX=THREE.MathUtils.clamp(dx*q/46,-1,1);stickY=THREE.MathUtils.clamp(dy*q/46,-1,1);nub.style.transform=`translate(${stickX*40}px,${stickY*40}px)`;}
  pad.addEventListener('pointerdown',e=>{stick=e.pointerId;pad.setPointerCapture(e.pointerId);padMove(e);});pad.addEventListener('pointermove',e=>{if(e.pointerId===stick)padMove(e);});for(const ev of ['pointerup','pointercancel','lostpointercapture'])pad.addEventListener(ev,e=>{if(e.pointerId===stick){stick=null;stickX=stickY=0;nub.style.transform='translate(0,0)';}});
  window.addEventListener('resize',resize);

  const loader=new GLTFLoader();
  loader.load('./models/asteria-v3-restored-pbr.glb',gltf=>{
    const room=gltf.scene;room.name='USS_ASTERIA_ROOM_01_V3_ARCHITECTURE';
    let nmeshes=0,triangles=0,missing=0;
    room.traverse(obj=>{
      if(!obj.isMesh)return;
      nmeshes++;const a=obj.geometry;
      triangles+=a.index?a.index.count/3:a.attributes.position.count/3;
      if(!obj.material)missing++;
      const mat=obj.material;
      obj.receiveShadow=true;
      // Only upholstered/cast forms cast directional shadows; architectural ribs do not.
      obj.castShadow=!mobile&&/upholstered_furniture/.test(obj.name);
      if(mat){mat.side=THREE.DoubleSide;
        if(mat.normalMap)mat.normalScale.set(.27,.27);
        if(/smoked_instrument/.test(obj.name)){
          mat.metalness=.22;mat.roughness=.29;mat.envMapIntensity=.35;
        }
        if(/diffused_practical/.test(obj.name)){
          mat.emissive=new THREE.Color(0xffd4ae);mat.emissiveIntensity=.30;
        }
      }
    });
    if(triangles!==106988||missing){fail('Scene asset geometry verification failed; V3 base has not been modified.');return;}
    scene.add(room);
    document.body.dataset.originalScenePreserved='true';
    document.body.dataset.materialGroups=String(nmeshes);
    document.body.dataset.geometryTriangles=String(triangles);
    document.body.dataset.sceneVersion='restored-v3-pbr-v5';
    document.body.dataset.missingMaterials=String(missing);
    window.__asteriaV5={roomId:'AST-D01-BRIDGE',sourceV3Sha:'74a154ae62bccb0c16d03c2ecf791a64ab19ce81',meshTriangles:triangles,getPosition:()=>({...pos}),resetAt,collision:blocked,ready:true,changesCampaign:false};
    ready=true;
    const choice=params.get('studioCapture');
    if(choice){resetAt(views[choice]?choice:'aft');$('splash').classList.add('off');}
    resize();$('loading').classList.add('off');requestAnimationFrame(frame);
  },undefined,err=>fail('The restored bridge scene failed to load: '+String(err.message||err)));
  resize();resetAt('aft');
})();