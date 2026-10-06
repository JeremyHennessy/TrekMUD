window.TM={};
TM.S={data:null,view:"now",deck:9,mapKey:null,selectedLocation:null,mapSearch:"",routeTarget:null,routePath:[],crewQuery:"",crewDept:"ALL",recordFilter:"all"};
TM.titleMap={now:"Right Now",ship:"Ship",map:"Ship Map",character:"Character",crew:"Crew",threads:"Threads",records:"Records",timeline:"Timeline"};
TM.$=s=>document.querySelector(s);
TM.esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
TM.empty=(msg="Nothing established here yet.")=>'<div class="empty">'+TM.esc(msg)+'</div>';
TM.card=(title,body,cls="")=>'<article class="card '+cls+'"><h3>'+TM.esc(title)+'</h3>'+body+'</article>';
TM.unresolvedCount=o=>Object.values(o||{}).filter(v=>v==null).length;
TM.deckLabel=x=>x?.deck!=null?"Deck "+x.deck+(x.section?" · Section "+x.section:""):(x?.section||"Ship location");
TM.shortName=s=>String(s||"").replace("Central ","").replace("Junior Officer ","").replace(" — Deck "+TM.S.deck,"").slice(0,22);
TM.showModal=html=>{TM.$("#modal-content").innerHTML=html;TM.$("#modal").showModal()};
TM.setView=view=>{
  if(!TM.titleMap[view])view="now";
  TM.S.view=view;
  document.querySelectorAll("#nav button").forEach(x=>x.classList.toggle("active",x.dataset.view===view));
  TM.render();
};
TM.bind=()=>{
  document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>{
    const view=b.dataset.view;
    if(location.hash!=="#"+view)location.hash=view;
    else TM.setView(view);
  });
  TM.$("#modal-close").onclick=()=>TM.$("#modal").close();
  window.addEventListener("hashchange",()=>TM.setView(location.hash.replace(/^#/,"")||"now"));
};
TM.render=()=>{
  document.title="TrekMUD · "+TM.titleMap[TM.S.view];
  TM.$("#title").textContent=TM.titleMap[TM.S.view];
  const fn={now:TM.renderNow,ship:TM.renderShip,map:TM.renderMap,character:TM.renderCharacter,crew:TM.renderCrew,threads:TM.renderThreads,records:TM.renderRecords,timeline:TM.renderTimeline}[TM.S.view]||TM.renderNow;
  fn();
};
TM.boot=async()=>{
  try{
    const r=await fetch("data/player-console.json",{cache:"no-store"});
    if(!r.ok)throw new Error("Player-safe state snapshot unavailable.");
    TM.S.data=await r.json();
    const d=TM.S.data;
    TM.$("#ship-time").textContent=d.now.shipTime;
    TM.$("#stardate").textContent="STARDATE "+d.now.stardate;
    TM.$("#eyebrow").textContent=d.ship.name.toUpperCase()+" · "+d.ship.registry;
    TM.$("#rail-meta").innerHTML="Checkpoint <b>"+TM.esc(d.source.checkpointId)+"</b><br>Revision "+TM.esc(d.source.campaignRevision)+"<br>Rules "+TM.esc(d.source.rulesVersion);
    TM.S.deck=d.now.location?.deck||9;
    TM.S.mapKey=d.map?.currentKey||String(TM.S.deck);
    TM.bind();
    TM.setView(location.hash.replace(/^#/,"")||"now");
  }catch(e){
    TM.$("#view").innerHTML='<article class="card"><h2>Console unavailable</h2><p class="mini">'+TM.esc(e.message)+'</p></article>';
  }
};
document.addEventListener("DOMContentLoaded",TM.boot);

TM.deptClass=d=>"dept-"+String(d||"shipwide").toLowerCase().replace(/[^a-z0-9]+/g,"-");
TM.rankShort=r=>String(r||"").replace("Lieutenant Commander","Lt. Cmdr.").replace("Lieutenant junior grade","Lt. j.g.").replace("Lieutenant","Lt.").replace("Commander","Cmdr.").replace("Captain","Capt.");
TM.shipMark=()=>'<svg class="ship-mark" viewBox="0 0 260 120" aria-hidden="true"><ellipse class="ship-main" cx="108" cy="48" rx="82" ry="34"/><path class="ship-cut" d="M88 65h40l30 17-28 10H92L64 82Z"/><path class="ship-nacelle" d="M49 68 14 103l58 3 25-29Zm118 9 25 29 54-3-32-35Z"/><path class="ship-pod" d="M104 14h34l20 16-37 14-38-14Z"/><path class="ship-pylon" d="M108 32h22v28h-22Z"/></svg>';

TM.locationById=id=>TM.S.data?.map?.locations?.find(x=>x.id===id)||null;
TM.locationKey=x=>x?.deck!=null?String(x.deck):String(x?.section||"");
TM.initials=name=>String(name||"").split(/\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,2).toUpperCase();
