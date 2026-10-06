TM.renderMap=()=>{
  const map=TM.S.data.map;
  const decks=map.deckNumbers;
  const locs=map.locations.filter(x=>x.deck===TM.S.deck);
  const ids=new Set(locs.map(x=>x.id));
  const edges=map.edges.filter(e=>ids.has(e.from)&&ids.has(e.to));
  const locBy=Object.fromEntries(locs.map(x=>[x.id,x]));
  const lines=edges.map(e=>{
    const a=locBy[e.from],b=locBy[e.to];
    return '<line class="edge '+(e.access==="restricted"?"restricted":"")+'" x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+'"/>';
  }).join("");
  const nodes=locs.map(x=>{
    const cur=x.id===TM.S.data.now.locationId;
    const cl=["node",cur?"current":"",x.access==="restricted"?"restricted":"",x.type==="quarters"?"quarters":""].join(" ");
    return '<g class="'+cl+'" data-id="'+TM.esc(x.id)+'"><circle cx="'+x.x+'" cy="'+x.y+'" r="'+(cur?3.2:2.5)+'"/><text x="'+x.x+'" y="'+(x.y+5)+'">'+TM.esc(TM.shortName(x.name))+'</text></g>';
  }).join("");
  TM.$("#view").innerHTML=
    '<article class="card map-card">'+
      '<div class="map-head"><div class="toolbar"><div class="decks">'+decks.map(d=>'<button class="'+(d===TM.S.deck?"active":"")+'" data-deck="'+d+'">'+d+'</button>').join("")+'</div><span class="pill">'+locs.length+' locations</span></div><h2>Deck '+TM.S.deck+'</h2><p class="mini">Original TrekMUD schematic · stable location IDs from campaign geography.</p></div>'+
      '<div class="map-wrap"><svg id="deck-map" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">'+lines+nodes+'</svg></div>'+
      '<div class="legend"><span><i class="dot current"></i>You are here</span><span><i class="dot"></i>Crew access</span><span><i class="dot restricted"></i>Restricted</span></div>'+
    '</article>';
  document.querySelectorAll("[data-deck]").forEach(b=>b.onclick=()=>{TM.S.deck=Number(b.dataset.deck);TM.renderMap()});
  document.querySelectorAll(".node").forEach(n=>n.onclick=()=>TM.showLocation(n.dataset.id));
};

TM.showLocation=id=>{
  const x=TM.S.data.map.locations.find(v=>v.id===id);if(!x)return;
  const connected=TM.S.data.map.edges.filter(e=>e.from===id||e.to===id).map(e=>{
    const other=e.from===id?e.to:e.from;
    const loc=TM.S.data.map.locations.find(v=>v.id===other);
    return loc?loc.name:other;
  });
  TM.showModal(
    '<div class="crew-rank">'+TM.esc(TM.deckLabel(x))+'</div>'+
    '<h2>'+TM.esc(x.name)+'</h2><p>'+TM.esc(x.id)+'</p>'+
    '<dl class="kv"><dt>Type</dt><dd>'+TM.esc(x.type)+'</dd><dt>Department</dt><dd>'+TM.esc(x.department)+'</dd><dt>Access</dt><dd>'+TM.esc(x.access)+'</dd><dt>Source</dt><dd>'+TM.esc(x.source)+'</dd><dt>Connections</dt><dd>'+TM.esc(connected.join(", ")||"None")+'</dd></dl>'
  );
};
