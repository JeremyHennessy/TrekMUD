const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const snapshot=JSON.parse(execFileSync('python',['-c',
  'import sys,json; from pathlib import Path; sys.path.insert(0,"scripts"); from build_player_console import player_safe_snapshot; print(json.dumps(player_safe_snapshot(Path.cwd())))'
],{cwd:root,encoding:'utf8'}));

function setup(){
  const nodes=new Map(),listeners={},intervals=[],timeouts=new Map();
  let timer=0,requests=0,draws=0;
  const node=id=>{
    if(!nodes.has(id))nodes.set(id,{id,open:false,textContent:'',innerHTML:'',
      addEventListener:(name,fn)=>{listeners[id+':'+name]=fn},
      focus:()=>{document.activeElement=node(id)},
      setSelectionRange:(start,end,direction)=>Object.assign(node(id),{selectionStart:start,selectionEnd:end,selectionDirection:direction})});
    return nodes.get(id);
  };
  const document={hidden:false,activeElement:null,querySelector:s=>node(s.slice(1)),
    querySelectorAll:()=>[],getElementById:node,
    addEventListener:(name,fn)=>{listeners[name]=fn}};
  const window={scrollX:0,scrollY:420,scrollTo:(x,y)=>{window.scrollX=x;window.scrollY=y},
    addEventListener:(name,fn)=>{listeners[name]=fn}};
  let response=async()=>({ok:true,json:async()=>structuredClone(snapshot)});
  const context={document,window,location:{hash:'#map'},AbortController,console,
    setInterval:(fn,ms)=>{intervals.push({fn,ms})},
    setTimeout:(fn)=>{timeouts.set(++timer,fn);return timer},clearTimeout:id=>timeouts.delete(id),
    fetch:async(url,options)=>{requests++;assert.equal(options.cache,'no-store');return response(options)}};
  Object.defineProperty(context,'TM',{get:()=>window.TM});
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(root,'ui/core.js'),'utf8'),context);
  vm.runInContext(fs.readFileSync(path.join(root,'ui/map.js'),'utf8'),context);
  const TM=context.TM;
  TM.render=()=>{draws++;nodes.delete('map-search')};
  return {TM,document,window,node,listeners,intervals,timeouts,
    get requests(){return requests},get draws(){return draws},
    respond:d=>{response=async()=>({ok:true,json:async()=>structuredClone(d)})},
    fetchWith:fn=>{response=fn}};
}
const next=()=>{
  const d=structuredClone(snapshot);
  d.source.campaignRevision++;
  d.source.checkpointId='test-next';
  d.now.shipTime='12:22';
  d.now.locationId='AST-D09-HUB-C';
  d.now.location=d.map.locations.find(x=>x.id===d.now.locationId);
  return d;
};

test('polling updates state and route while preserving navigation, filters, focus and scroll',async()=>{
  const h=setup();await h.TM.boot();
  assert.equal(h.intervals[0].ms,30000);
  Object.assign(h.TM.S,{mapKey:'7',deck:7,selectedLocation:'AST-D07-S12-0712C',
    mapSearch:'quarters',crewQuery:'science',crewDept:'SCIENCE',recordFilter:'science',routeTarget:'AST-D07-S12-0712C'});
  h.document.activeElement=h.node('map-search');
  h.document.activeElement.setSelectionRange(2,5,'forward');
  h.respond(next());await h.intervals[0].fn();
  for(const [key,value] of Object.entries({view:'map',mapKey:'7',deck:7,selectedLocation:'AST-D07-S12-0712C',mapSearch:'quarters',crewQuery:'science',crewDept:'SCIENCE',recordFilter:'science'}))assert.equal(h.TM.S[key],value);
  assert.equal(h.TM.S.routePath[0],'AST-D09-HUB-C');
  assert.equal(h.TM.S.routePath.at(-1),'AST-D07-S12-0712C');
  assert.equal(h.node('ship-time').textContent,'12:22');
  assert.equal(h.document.activeElement.id,'map-search');
  assert.equal(h.document.activeElement.selectionStart,2);
  assert.equal(h.document.activeElement.selectionEnd,5);
  assert.equal(h.window.scrollY,420);
});

test('unchanged campaign does not redraw even when build timestamp changes',async()=>{
  const h=setup();await h.TM.boot();const count=h.draws;
  h.respond({...snapshot,generatedAt:'different build'});await h.TM.refresh();
  assert.equal(h.draws,count);
});

test('offline, HTTP and malformed responses preserve last good snapshot; online retries',async()=>{
  const h=setup();await h.TM.boot();const previous=h.TM.S.data;
  for(const fn of [async()=>{throw Error('offline')},async()=>({ok:false}),async()=>({ok:true,json:async()=>{throw Error('invalid JSON')}}),async()=>({ok:true,json:async()=>({})})]){
    h.fetchWith(fn);await h.TM.refresh();assert.equal(h.TM.S.data,previous);
  }
  h.respond(next());await h.listeners.online();assert.equal(h.TM.S.data.source.checkpointId,'test-next');
});

test('hidden pages and open dialogs defer updates and resume when visible or closed',async()=>{
  const h=setup();await h.TM.boot();h.respond(next());const count=h.requests;
  h.document.hidden=true;await h.TM.refresh();assert.equal(h.requests,count);
  h.document.hidden=false;h.node('modal').open=true;await h.listeners.focus();assert.equal(h.requests,count);
  h.node('modal').open=false;await h.listeners['modal:close']();assert.equal(h.TM.S.data.source.checkpointId,'test-next');
  h.respond({...next(),now:{...next().now,shipTime:'12:23'}});await h.listeners.visibilitychange();
  assert.equal(h.node('ship-time').textContent,'12:23');
});

test('overlapping checks share one request and timeout releases the next retry',async()=>{
  const h=setup();await h.TM.boot();let release;
  h.fetchWith(()=>new Promise(resolve=>{release=resolve}));
  const first=h.TM.refresh(),count=h.requests;await h.TM.refresh();assert.equal(h.requests,count);
  release({ok:true,json:async()=>next()});await first;
  h.fetchWith(({signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('timeout')))));
  const pending=h.TM.refresh();[...h.timeouts.values()][0]();await pending;
  assert.equal(h.TM.refreshing,false);
  h.respond(snapshot);await h.TM.refresh();assert.equal(h.TM.S.data.source.checkpointId,snapshot.source.checkpointId);
});

test('failed initial load recovers automatically and failed rendering restores old state',async()=>{
  const h=setup();h.fetchWith(async()=>{throw Error('offline')});await h.TM.boot();
  assert.equal(h.TM.S.data,null);h.respond(snapshot);await h.listeners.online();
  assert.equal(h.TM.S.view,'map');assert.equal(h.TM.S.data.source.checkpointId,snapshot.source.checkpointId);
  const previous=h.TM.S.data,render=h.TM.render;
  h.TM.render=()=>{if(h.TM.S.data.source.checkpointId==='test-next')throw Error('render failure');render()};
  h.respond(next());await h.TM.refresh();assert.equal(h.TM.S.data,previous);
  assert.equal(h.node('ship-time').textContent,snapshot.now.shipTime);
});
