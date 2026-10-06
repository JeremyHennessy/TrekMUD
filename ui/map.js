TM.mapPositionIndex=plan=>{
  const index={};
  for(const row of [...(plan.compartments||[]),...(plan.circulation||[])]){
    index[row.id]={
      x:row.x+(row.w||0)/2,
      y:row.y+(row.h||0)/2,
      row
    };
  }
  return index;
};

TM.hullPath=h=>{
  const left=h.x,right=h.x+h.width;
  const shoulder=Math.min(14,h.width*.18);
  const inner=Math.min(8,h.width*.1);
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

TM.mapRoomClass=row=>{
  const bits=["compartment",TM.deptClass(row.department)];
  if(row.access==="restricted")bits.push("restricted");
  if(row.id===TM.S.data.now.locationId)bits.push("current");
  if(row.id===TM.S.selectedLocation)bits.push("selected");
  return bits.join(" ");
};

TM.renderShipProfile=()=>{
  const profile=TM.S.data.map.profile||[];
  return '<div class="ship-overview">'+
    '<div class="overview-title"><span>USS MERIDIAN</span><b>DECK CUTAWAY</b></div>'+
    '<div class="ship-stack">'+profile.map(row=>
      '<button class="deck-band '+(row.deck===TM.S.deck?"active":"")+' '+(row.current?"current":"")+'" data-deck="'+row.deck+'" title="Deck '+row.deck+' · '+TM.esc(row.label)+'">'+
        '<span class="deck-no">'+String(row.deck).padStart(2,"0")+'</span>'+
        '<span class="deck-hull" style="width:'+row.width+'%"><i></i></span>'+
        '<span class="deck-label">'+TM.esc(row.label)+'</span>'+
      '</button>'
    ).join("")+'</div>'+
    '<div class="overview-footer"><span class="legend-key"><i class="current"></i>current deck</span><span>19 decks</span></div>'+
  '</div>';
};

TM.renderDeckSvg=plan=>{
  const positions=TM.mapPositionIndex(plan);
  const corridors=(plan.edges||[]).map(edge=>{
    const a=positions[edge.from],b=positions[edge.to];
    if(!a||!b)return "";
    const mx=(a.x+b.x)/2;
    return '<path class="deck-connection '+(edge.access==="restricted"?"restricted":"")+'" d="M '+a.x+' '+a.y+' L '+mx+' '+a.y+' L '+mx+' '+b.y+' L '+b.x+' '+b.y+'"/>';
  }).join("");

  const rooms=(plan.compartments||[]).map(room=>{
    const current=room.id===TM.S.data.now.locationId;
    const label=TM.shortName(room.name);
    return '<g class="'+TM.mapRoomClass(room)+'" data-room="'+TM.esc(room.id)+'">'+
      '<rect x="'+room.x+'" y="'+room.y+'" width="'+room.w+'" height="'+room.h+'" rx="2"/>'+
      '<text class="room-label" x="'+(room.x+room.w/2)+'" y="'+(room.y+room.h/2-.4)+'">'+TM.esc(label)+'</text>'+
      '<text class="room-type" x="'+(room.x+room.w/2)+'" y="'+(room.y+room.h/2+3.1)+'">'+TM.esc(String(room.type||"").toUpperCase())+'</text>'+
      (current?'<g class="you-marker" transform="translate('+(room.x+room.w-2)+','+(room.y+2)+')"><circle r="3.2"/><text y="1">YOU</text></g>':"")+
    '</g>';
  }).join("");

  const circulation=(plan.circulation||[]).map(row=>{
    const current=row.id===TM.S.data.now.locationId;
    return '<g class="circulation '+row.kind+' '+(current?"current":"")+'" data-room="'+TM.esc(row.id)+'">'+
      '<rect x="'+row.x+'" y="'+row.y+'" width="'+row.w+'" height="'+row.h+'" rx="2"/>'+
      '<text x="'+(row.x+row.w/2)+'" y="'+(row.y+row.h/2+1)+'">'+TM.esc(row.kind==="turbolift"?"TL":row.kind==="hub"?"HUB":"COR")+'</text>'+
    '</g>';
  }).join("");

  return '<svg class="deck-schematic" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">'+
    '<defs><filter id="glow"><feGaussianBlur stdDeviation="1.2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'+
    '<path class="deck-hull-outline" d="'+TM.hullPath(plan.hull)+'"/>'+
    '<path class="deck-spine" d="M '+(plan.hull.x+7)+' 50 H '+(plan.hull.x+plan.hull.width-7)+'"/>'+
    '<text class="orientation forward" x="50" y="3">FORWARD</text>'+
    '<text class="orientation port" x="3" y="50" transform="rotate(-90 3 50)">PORT</text>'+
    '<text class="orientation starboard" x="97" y="50" transform="rotate(90 97 50)">STARBOARD</text>'+
    corridors+circulation+rooms+
  '</svg>';
};

TM.roomInspector=id=>{
  const data=TM.S.data;
  const x=data.map.locations.find(v=>v.id===id);
  if(!x)return '<div class="room-inspector empty-inspector"><span>SELECT A COMPARTMENT</span><p>Choose any room on the deck plan to inspect it.</p></div>';

  const connected=data.map.edges.filter(e=>e.from===id||e.to===id).map(e=>{
    const other=e.from===id?e.to:e.from;
    const loc=data.map.locations.find(v=>v.id===other);
    return {name:loc?.name||other,access:e.access,type:e.type};
  });

  const current=id===data.now.locationId;
  return '<div class="room-inspector '+(current?"current":"")+'">'+
    '<div class="inspector-kicker">'+TM.esc(TM.deckLabel(x))+'</div>'+
    '<h3>'+TM.esc(x.name)+'</h3>'+
    (current?'<div class="current-location-badge">YOU ARE HERE</div>':"")+
    '<dl class="inspector-grid">'+
      '<dt>TYPE</dt><dd>'+TM.esc(x.type)+'</dd>'+
      '<dt>DEPT</dt><dd>'+TM.esc(x.department)+'</dd>'+
      '<dt>ACCESS</dt><dd>'+TM.esc(x.access)+'</dd>'+
      '<dt>ID</dt><dd class="mono">'+TM.esc(x.id)+'</dd>'+
    '</dl>'+
    '<div class="connection-list"><span>CONNECTED TO</span>'+
      (connected.length?connected.map(c=>'<div><b>'+TM.esc(c.name)+'</b><small>'+TM.esc(c.type)+' · '+TM.esc(c.access)+'</small></div>').join(""):'<p>None listed</p>')+
    '</div>'+
  '</div>';
};

TM.renderMap=()=>{
  const map=TM.S.data.map;
  const plan=map.deckPlans[String(TM.S.deck)];
  if(!plan){
    TM.$("#view").innerHTML='<article class="card">'+TM.empty("No schematic for this deck.")+'</article>';
    return;
  }
  if(!TM.S.selectedLocation || !map.locations.some(x=>x.id===TM.S.selectedLocation&&x.deck===TM.S.deck)){
    TM.S.selectedLocation=TM.S.deck===map.currentDeck?TM.S.data.now.locationId:(plan.compartments[0]?.id||plan.circulation[0]?.id||null);
  }

  TM.$("#view").innerHTML=
    '<div class="map-v2">'+
      '<aside class="map-profile-panel">'+TM.renderShipProfile()+'</aside>'+
      '<section class="deck-plan-panel">'+
        '<div class="deck-plan-head">'+
          '<div><span class="section-code">DECK '+String(plan.deck).padStart(2,"0")+'</span><h2>'+TM.esc(plan.label)+'</h2><p>'+TM.esc(plan.compartmentCount)+' compartments · '+TM.esc(plan.roomCount)+' mapped locations</p></div>'+
          '<div class="map-actions"><button class="map-nav" data-deck-prev>←</button><button class="map-nav" data-deck-next>→</button></div>'+
        '</div>'+
        '<div class="deck-svg-frame">'+TM.renderDeckSvg(plan)+'</div>'+
        '<div class="map-legend-v2"><span><i class="swatch current"></i>Jeremy</span><span><i class="swatch science"></i>Science</span><span><i class="swatch operations"></i>Operations</span><span><i class="swatch engineering"></i>Engineering</span><span><i class="swatch restricted"></i>Restricted</span></div>'+
      '</section>'+
      '<aside class="map-inspector-panel">'+TM.roomInspector(TM.S.selectedLocation)+'</aside>'+
    '</div>';

  document.querySelectorAll("[data-deck]").forEach(b=>b.onclick=()=>{
    TM.S.deck=Number(b.dataset.deck);TM.S.selectedLocation=null;TM.renderMap();
  });
  document.querySelectorAll("[data-room]").forEach(n=>n.onclick=()=>{
    TM.S.selectedLocation=n.dataset.room;TM.renderMap();
  });
  const prev=TM.$("[data-deck-prev]"),next=TM.$("[data-deck-next]");
  if(prev)prev.onclick=()=>{TM.S.deck=Math.max(1,TM.S.deck-1);TM.S.selectedLocation=null;TM.renderMap()};
  if(next)next.onclick=()=>{TM.S.deck=Math.min(19,TM.S.deck+1);TM.S.selectedLocation=null;TM.renderMap()};
};
