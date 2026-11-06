'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const prefix='ui/3d-preview-v3/';
const page=read(prefix+'index.html');
const base=read('ui/3d-preview/index.html');
const v1=read('ui/3d/index.html');
const world=JSON.parse(read('world/asteria/topology.json'));

test('v3 preserves canonical room identity and existing navigation',()=>{
 assert.ok(world.locations.some(x=>x.id==='AST-D01-BRIDGE'&&x.deck===1&&x.access==='restricted'));
 assert.ok(page.includes("roomId:'AST-D01-BRIDGE'"));
 assert.ok(page.includes("visualPass:'hero-set-03'"));
 const suffix='function blocked(x,z)';
 const end='function resize()';
 const section=s=>s.slice(s.indexOf(suffix),s.indexOf(end,s.indexOf(suffix)));
 assert.ok(section(base).length>200);
 assert.equal(section(page),section(base),'movement/collision changed');
 assert.ok(v1.includes("roomId:'AST-D01-BRIDGE'"));
 assert.ok(!v1.includes('hero-v3.js'));
 assert.ok(!base.includes('hero-v3.js'));
});

test('all v3 JS parses and keeps outside assets and private state out',()=>{
 const inline=page.match(/<script>([\s\S]*?)<\/script>/);
 assert.ok(inline,'inline renderer missing');
 assert.doesNotThrow(()=>new vm.Script(inline[1]));
 for(const filename of ['hero-v3.js','furniture.js','set-details.js']){
  assert.ok(page.includes('<script src="'+filename+'"></script>'),filename+' not loaded');
  assert.doesNotThrow(()=>new vm.Script(read(prefix+filename)),filename+' does not parse');
 }
 assert.doesNotMatch(page,/<script[^>]+src="https?:|<img[^>]+src="https?:|<link[^>]+href="https?:/);
 for(const name of ['TrekMUD-GM','secretSeedHex','npc-private','future-events']){
  for(const filename of ['index.html','hero-v3.js'])assert.ok(!read(prefix+filename).includes(name));
 }
});

test('hero furniture emits finite smooth geometry without controlling game state',()=>{
 const sandbox={window:{}};
 vm.runInNewContext(read(prefix+'hero-v3.js'),sandbox);
 const hero=sandbox.window.AsteriaHero;
 assert.ok(Object.isFrozen(hero));
 let smoothCalls=0,faces=0;
 const finiteValue=v=>{if(typeof v==='number')assert.ok(Number.isFinite(v));if(Array.isArray(v))v.forEach(finiteValue);};
 const api={};
 for(const fn of ['box','cyl','ellipse','ring','tube','plane','surface']){
  api[fn]=(...args)=>{faces++;args.forEach(finiteValue);};
 }
 api.smoothSurface=(u,v,sample,color,material,flip)=>{
  assert.ok(Number.isInteger(u)&&u>=4);
  assert.ok(Number.isInteger(v)&&v>=4);
  for(const a of [0,.1,.35,.5,.75,1])for(const b of [0,.15,.6,1]){
   const p=sample(a,b);
   assert.equal(p.length,3);p.forEach(finiteValue);
  }
  smoothCalls++;
 };
 assert.equal(hero.chair({x:0,z:1.2,large:true},api).version,3);
 assert.equal(hero.chair({x:-1.15,z:-2.13},api).smooth,true);
 assert.equal(hero.flightIsland(api).segments,52);
 assert.equal(hero.commandPlatform(api).version,3);
 assert.equal(hero.commandPylons(api).count,2);
 assert.equal(hero.ceilingFixtures(api).fixtures,6);
 assert.ok(smoothCalls>=16);
 assert.ok(faces>=70);
 const script=read(prefix+'hero-v3.js');
 assert.doesNotMatch(script,/fetch\(|localStorage|XMLHttpRequest|location\.hash|campaign\/state/);
});
