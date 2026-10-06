TM.mapPositionIndex=plan=>{
  const index={};
  for(const row of [...(plan.compartments||[]),...(plan.circulation||[])]){
    index[row.id]={x:row.x+(row.w||0)/2,y:row.y+(row.h||0)/2,row};
  }
  return index;
};

TM.planHullPath=plan=>{
  if(plan.kind==="pod")return "M 50 5 L 82 27 L 72 88 L 28 88 L 18 27 Z";
  const h=plan.hull,left=h.x,right=h.x+h.width;
  const shoulder=Math.min(14,h.width*.18),inner=Math.min(8,h.width*.1);
  return [
    "M 50 5",
    "C "+(right-shoulder)+" 8 "+right+" 21 "+right+" 39",
    "L "+(right-inner)+" 60",
    "C "+(right-inner*1.4)+" 79 "+(right-shoulder)+" 89 50 95",
    "C "+(left+shoulder)+" 89 "+(left+inner*1.4)+" 79 "+(left+inner)+" 60",
    "L "+left+" 39",
    "C "+left+" 21 "+(left+shoulder)+" 8 50 5 Z"
  ].join(" ");
};

TM.locationAccessible=id=>{
  const loc=TM.locationById(id);
  return !!loc && loc.access!=="restricted";
};

TM.routeEdgeKey=(a,b)=>a+"|"+b;
TM.routeEdgeSet=()=>{
  const out=new Set();
  const path=TM.S.routePath||[];
  for(let i=0;i<path.length-1;i++){
    out.add(TM.routeEdgeKey(path[i],path[i+1]));
    out.add(TM.routeEdgeKey(path[i+1],path[i]));
  }
  return out;
};

TM.computeRoute=targetId=>{
  const data=TM.S.data,start=data.now.locationId;
  const target=TM.locationById(targetId);
  if(!target)return {path:[],error:"Destination is not in the current ship directory."};
  if(target.access==="restricted")return {path:[],error:"Destination is restricted; no standard-access route is available."};
  if(start===targetId)return {path:[start],error:null};

  const byId=Object.fromEntries(data.map.locations.map(x=>[x.id,x]));
  const adj={};
  const add=(a,b)=>{(adj[a]||(adj[a]=[])).push(b)};
  for(const edge of data.map.edges){
    if(edge.access==="restricted")continue;
    const a=byId[edge.from],b=byId[edge.to];
    if(!a||!b||a.access==="restricted"||b.access==="restricted")continue;
    add(edge.from,edge.to);
    if(edge.bidirectional!==false)add(edge.to,edge.from);
  }

  const queue=[start],prev={[start]:null};
  for(let i=0;i<queue.length;i++){
    const cur=queue[i];
    for(const nxt of (adj[cur]||[])){
      if(Object.prototype.hasOwnProperty.call(prev,nxt))continue;
      prev[nxt]=cur;
      if(nxt===targetId){
        const path=[];let at=nxt;
        while(at!==null){path.push(at);at=prev[at]}
        return {path:path.reverse(),error:null};
      }
      queue.push(nxt);
    }
  }
  return {path:[],error:"No standard-access route could be found."};
};

TM.startRoute=targetId=>{
  const result=TM.computeRoute(targetId);
  TM.S.routeTarget=targetId;
  TM.S.routePath=result.path;
  TM.S.routeError=result.error;
  TM.S.mapKey=String(TM.S.data.map.currentKey||"9");
  TM.S.selectedLocation=TM.S.data.now.locationId;
};

TM.clearRoute=()=>{
  TM.S.routeTarget=null;TM.S.routePath=[];TM.S.routeError=null;
};

TM.routeSummarySteps=()=>{
  const path=TM.S.routePath||[],steps=[];
  for(let i=0;i<path.length;i++){
    const loc=TM.locationById(path[i]);if(!loc)continue;
    if(/-TL-C$/.test(loc.id)){
      let j=i;
      while(j+1<path.length && /-TL-C$/.test(path[j+1]))j++;
      const last=TM.locationById(path[j]);
      if(j>i){
        steps.push({kind:"lift",title:"Turbolift",detail:TM.deckLabel(loc)+" → "+TM.deckLabel(last)});
        i=j;continue;
      }
    }
    steps.push({kind:"room",title:loc.name,detail:TM.deckLabel(loc)});
  }
  return steps;
};

TM.routePanel=()=>{
  if(!TM.S.routeTarget)return "";
  const target=TM.locationById(TM.S.routeTarget);
  if(TM.S.routeError){
    return '<div class="route-panel error"><div><span>ROUTE UNAVAILABLE</span><b>'+TM.esc(target?.name||"Destination")+'</b><small>'+TM.esc(TM.S.routeError)+'</small></div><button data-route-clear>Clear</button></div>';
  }
  const steps=TM.routeSummarySteps();
  return '<div class="route-panel"><div class="route-head"><div><span>STANDARD ROUTE</span><b>'+TM.esc(target?.name||"Destination")+'</b><small>'+Math.max(0,(TM.S.routePath||[]).length-1)+' connections · restricted passages excluded</small></div><div><button data-route-show>Show destination</button><button data-route-clear>Clear</button></div></div><div class="route-steps">'+steps.map((x,i)=>'<div class="route-step '+x.kind+'"><em>'+String(i+1).padStart(2,"0")+'</em><div><b>'+TM.esc(x.title)+'</b><small>'+TM.esc(x.detail)+'</small></div></div>').join("")+'</div></div>';
};

TM.mapSearchResults=()=>{
  const q=String(TM.S.mapSearch||"").trim().toLowerCase();
  if(!q)return [];
  return TM.S.data.map.locations.filter(x=>
    [x.name,x.type,x.department,x.id,TM.deckLabel(x)].join(" ").toLowerCase().includes(q)
  ).slice(0,10);
};

TM.mapRoomClass=row=>{
  const bits=["compartment",TM.deptClass(row.department)];
  if(row.access==="restricted")bits.push("restricted");
  if(row.id===TM.S.data.now.locationId)bits.push("current");
  if(row.id===TM.S.selectedLocation)bits.push("selected");
  if((TM.S.routePath||[]).includes(row.id))bits.push("route-node");
  return bits.join(" ");
};

TM.renderShipProfile=()=>{
  const map=TM.S.data.map,profile=map.profile||[],pods=map.podProfile||[];
  return '<div class="ship-overview">'+
    '<div class="overview-title"><span>USS ASTERIA</span><b>NEBULA CLASS</b></div>'+
    '<div class="ship-stack">'+profile.map(row=>
      '<button class="deck-band '+(String(row.key)===String(TM.S.mapKey)?"active":"")+' '+(row.current?"current":"")+'" data-map-key="'+TM.esc(row.key)+'" title="Deck '+row.deck+' · '+TM.esc(row.label)+'">'+
        '<span class="deck-no">'+String(row.deck).padStart(2,"0")+'</span>'+
        '<span class="deck-hull" style="width:'+row.width+'%"><i></i></span>'+
        '<span class="deck-label">'+TM.esc(row.label)+'</span>'+
      '</button>'
    ).join("")+'</div>'+
    '<div class="pod-stack">'+pods.map(row=>
      '<button class="pod-band '+(String(row.key)===String(TM.S.mapKey)?"active":"")+' '+(row.current?"current":"")+'" data-map-key="'+TM.esc(row.key)+'">'+
        '<span class="pod-code">'+TM.esc(row.key)+'</span><span class="pod-label">'+TM.esc(row.label)+'</span>'+
      '</button>'
    ).join("")+'</div>'+
    '<div class="overview-footer"><span class="legend-key"><i class="current"></i>current</span><span>28 decks · 4 pod levels</span></div>'+
  '</div>';
};

TM.renderDeckSvg=plan=>{
  const positions=TM.mapPositionIndex(plan),routeEdges=TM.routeEdgeSet();
  const corridors=(plan.edges||[]).map(edge=>{
    const a=positions[edge.from],b=positions[edge.to];if(!a||!b)return "";
    const mx=(a.x+b.x)/2;
    const onRoute=routeEdges.has(TM.routeEdgeKey(edge.from,edge.to));
    return '<path class="deck-connection '+(edge.access==="restricted"?"restricted ":"")+(onRoute?"route":"")+'" d="M '+a.x+' '+a.y+' L '+mx+' '+a.y+' L '+mx+' '+b.y+' L '+b.x+' '+b.y+'"/>';
  }).join("");

  const rooms=(plan.compartments||[]).map(room=>{
    const current=room.id===TM.S.data.now.locationId;
    return '<g class="'+TM.mapRoomClass(room)+'" data-room="'+TM.esc(room.id)+'">'+
      '<rect x="'+room.x+'" y="'+room.y+'" width="'+room.w+'" height="'+room.h+'" rx="2"/>'+
      '<text class="room-label" x="'+(room.x+room.w/2)+'" y="'+(room.y+room.h/2-.4)+'">'+TM.esc(TM.shortName(room.name))+'</text>'+
      '<text class="room-type" x="'+(room.x+room.w/2)+'" y="'+(room.y+room.h/2+3.1)+'">'+TM.esc(String(room.type||"").toUpperCase())+'</text>'+
      (current?'<g class="you-marker" transform="translate('+(room.x+room.w-2)+','+(room.y+2)+')"><circle r="3.2"/><text y="1">YOU</text></g>':"")+
    '</g>';
  }).join("");

  const circulation=(plan.circulation||[]).map(row=>{
    const current=row.id===TM.S.data.now.locationId,onRoute=(TM.S.routePath||[]).includes(row.id);
    return '<g class="circulation '+row.kind+' '+(current?"current ":"")+(onRoute?"route-node":"")+'" data-room="'+TM.esc(row.id)+'">'+
      '<rect x="'+row.x+'" y="'+row.y+'" width="'+row.w+'" height="'+row.h+'" rx="2"/>'+
      '<text x="'+(row.x+row.w/2)+'" y="'+(row.y+row.h/2+1)+'">'+TM.esc(row.kind==="turbolift"?"TL":row.kind==="hub"?"HUB":"COR")+'</text>'+
    '</g>';
  }).join("");

  const orientation=plan.kind==="pod"
    ? '<text class="orientation forward" x="50" y="3">DORSAL SENSOR POD</text>'
    : '<text class="orientation forward" x="50" y="3">FORWARD</text><text class="orientation port" x="3" y="50" transform="rotate(-90 3 50)">PORT</text><text class="orientation starboard" x="97" y="50" transform="rotate(90 97 50)">STARBOARD</text>';

  return '<svg class="deck-schematic" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">'+
    '<defs><filter id="glow"><feGaussianBlur stdDeviation="1.2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'+
    '<path class="deck-hull-outline" d="'+TM.planHullPath(plan)+'"/>'+
    '<path class="deck-spine" d="M '+(plan.hull.x+7)+' 50 H '+(plan.hull.x+plan.hull.width-7)+'"/>'+
    orientation+corridors+circulation+rooms+
  '</svg>';
};

TM.roomInspector=id=>{
  const data=TM.S.data,x=TM.locationById(id);
  if(!x)return '<div class="room-inspector empty-inspector"><span>SELECT A COMPARTMENT</span><p>Choose any mapped compartment to inspect it.</p></div>';
  const connected=data.map.edges.filter(e=>e.from===id||e.to===id).map(e=>{
    const other=e.from===id?e.to:e.from,loc=TM.locationById(other);
    return {name:loc?.name||other,access:e.access,type:e.type};
  });
  const current=id===data.now.locationId;
  const accessLabel=x.access==="restricted"?"RESTRICTED DIRECTORY":x.access==="assigned"?"ASSIGNED ACCESS":"CREW DIRECTORY";
  const routeButton=current?"":'<button class="console-action '+(x.access==="restricted"?"disabled":"")+'" '+(x.access==="restricted"?"disabled":"data-route-selected")+'>'+(x.access==="restricted"?"Restricted destination":"Route from current location")+'</button>';
  return '<div class="room-inspector '+(current?"current":"")+'">'+
    '<div class="inspector-kicker">'+TM.esc(TM.deckLabel(x))+'</div>'+
    '<h3>'+TM.esc(x.name)+'</h3>'+
    (current?'<div class="current-location-badge">YOU ARE HERE</div>':"")+
    '<div class="directory-status">'+TM.esc(accessLabel)+'</div>'+
    '<dl class="inspector-grid">'+
      '<dt>TYPE</dt><dd>'+TM.esc(x.type)+'</dd>'+
      '<dt>DEPT</dt><dd>'+TM.esc(x.department)+'</dd>'+
      '<dt>ACCESS</dt><dd>'+TM.esc(x.access)+'</dd>'+
      '<dt>REF</dt><dd class="mono">'+TM.esc(x.id)+'</dd>'+
    '</dl>'+routeButton+
    '<div class="connection-list"><span>CONNECTED TO</span>'+
      (connected.length?connected.map(c=>'<div><b>'+TM.esc(c.name)+'</b><small>'+TM.esc(c.type)+' · '+TM.esc(c.access)+'</small></div>').join(""):'<p>None listed</p>')+
    '</div>'+
  '</div>';
};

TM.mapTools=()=>{
  const results=TM.mapSearchResults();
  const quick=[
    ["AST-D07-S12-0712C","Quarters"],
    ["AST-D04-SCI-OFFICE","Science"],
    ["AST-D06-SICKBAY","Sickbay"],
    ["AST-D12-MESS","Mess"]
  ];
  return '<div class="map-tools">'+
    '<div class="map-search-wrap"><input id="map-search" autocomplete="off" placeholder="Find room, department, deck…" value="'+TM.esc(TM.S.mapSearch)+'">'+
      (TM.S.mapSearch?'<div class="map-search-results">'+(results.length?results.map(x=>
        '<div class="map-search-row"><button data-view-room="'+TM.esc(x.id)+'"><span>'+TM.esc(x.name)+'</span><small>'+TM.esc(TM.deckLabel(x))+' · '+TM.esc(x.department)+'</small></button><button class="route-mini" '+(x.access==="restricted"?"disabled":"data-route-search=\""+TM.esc(x.id)+"\"")+'>Route</button></div>'
      ).join(""):'<div class="map-search-empty">No matching ship locations.</div>')+'</div>':"")+
    '</div>'+
    '<div class="quick-route">'+quick.map(([id,label])=>'<button data-route-quick="'+id+'">'+label+'</button>').join("")+'</div>'+
  '</div>';
};

TM.renderMap=()=>{
  const map=TM.S.data.map,key=String(TM.S.mapKey||map.currentKey||"9");
  const plan=map.deckPlans[key]||map.podPlans[key];
  if(!plan){TM.$("#view").innerHTML='<article class="card">'+TM.empty("No schematic for this section.")+'</article>';return;}
  if(!TM.S.selectedLocation || !map.locations.some(x=>x.id===TM.S.selectedLocation&&(String(x.deck)===key||String(x.section)===key))){
    TM.S.selectedLocation=key===String(map.currentKey)?TM.S.data.now.locationId:(plan.compartments[0]?.id||plan.circulation[0]?.id||null);
  }
  const code=plan.kind==="pod"?plan.key:"DECK "+String(plan.key).padStart(2,"0");
  const subtitle=plan.kind==="pod"?"Dorsal mission pod":"Primary hull";

  TM.$("#view").innerHTML=
    TM.mapTools()+TM.routePanel()+
    '<div class="map-v2">'+
      '<aside class="map-profile-panel">'+TM.renderShipProfile()+'</aside>'+
      '<section class="deck-plan-panel">'+
        '<div class="deck-plan-head"><div><span class="section-code">'+TM.esc(code)+' · '+TM.esc(subtitle)+'</span><h2>'+TM.esc(plan.label)+'</h2><p>'+TM.esc(plan.compartmentCount)+' compartments · '+TM.esc(plan.roomCount)+' mapped locations</p></div>'+
          (plan.kind==="deck"?'<div class="map-actions"><button class="map-nav" data-deck-prev>←</button><button class="map-nav" data-deck-next>→</button></div>':"")+
        '</div>'+
        '<div class="deck-svg-frame">'+TM.renderDeckSvg(plan)+'</div>'+
        '<div class="map-legend-v2"><span><i class="swatch current"></i>Jeremy</span><span><i class="swatch route"></i>Route</span><span><i class="swatch science"></i>Science</span><span><i class="swatch operations"></i>Operations</span><span><i class="swatch engineering"></i>Engineering</span><span><i class="swatch restricted"></i>Restricted</span></div>'+
      '</section>'+
      '<aside class="map-inspector-panel">'+TM.roomInspector(TM.S.selectedLocation)+'</aside>'+
    '</div>';

  document.querySelectorAll("[data-map-key]").forEach(b=>b.onclick=()=>{TM.S.mapKey=b.dataset.mapKey;const n=Number(TM.S.mapKey);if(Number.isInteger(n)&&n>0)TM.S.deck=n;TM.S.selectedLocation=null;TM.renderMap()});
  document.querySelectorAll("[data-room]").forEach(n=>n.onclick=()=>{TM.S.selectedLocation=n.dataset.room;TM.renderMap()});
  document.querySelectorAll("[data-view-room]").forEach(b=>b.onclick=()=>{const x=TM.locationById(b.dataset.viewRoom);TM.S.mapKey=TM.locationKey(x);TM.S.selectedLocation=x.id;TM.S.mapSearch="";TM.renderMap()});
  document.querySelectorAll("[data-route-search]").forEach(b=>b.onclick=()=>{TM.startRoute(b.dataset.routeSearch);TM.S.mapSearch="";TM.renderMap()});
  document.querySelectorAll("[data-route-quick]").forEach(b=>b.onclick=()=>{TM.startRoute(b.dataset.routeQuick);TM.renderMap()});
  const rs=TM.$("[data-route-selected]");if(rs)rs.onclick=()=>{TM.startRoute(TM.S.selectedLocation);TM.renderMap()};
  const rc=TM.$("[data-route-clear]");if(rc)rc.onclick=()=>{TM.clearRoute();TM.renderMap()};
  const show=TM.$("[data-route-show]");if(show)show.onclick=()=>{const x=TM.locationById(TM.S.routeTarget);if(x){TM.S.mapKey=TM.locationKey(x);TM.S.selectedLocation=x.id;TM.renderMap()}};
  const search=TM.$("#map-search");if(search)search.oninput=e=>{TM.S.mapSearch=e.target.value;TM.renderMap()};
  const prev=TM.$("[data-deck-prev]"),next=TM.$("[data-deck-next]");
  if(prev)prev.onclick=()=>{TM.S.deck=Math.max(1,Number(plan.key)-1);TM.S.mapKey=String(TM.S.deck);TM.S.selectedLocation=null;TM.renderMap()};
  if(next)next.onclick=()=>{TM.S.deck=Math.min(28,Number(plan.key)+1);TM.S.mapKey=String(TM.S.deck);TM.S.selectedLocation=null;TM.renderMap()};
};
