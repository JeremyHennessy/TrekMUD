window.TM={};
TM.S={data:null,view:"now",deck:9,selectedLocation:null,crewQuery:"",crewDept:"ALL"};
TM.titleMap={now:"Right Now",map:"Ship Map",character:"Character",crew:"Crew",threads:"Threads",timeline:"Timeline"};
TM.$=s=>document.querySelector(s);
TM.esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
TM.empty=(msg="Nothing established here yet.")=>'<div class="empty">'+TM.esc(msg)+'</div>';
TM.card=(title,body,cls="")=>'<article class="card '+cls+'"><h3>'+TM.esc(title)+'</h3>'+body+'</article>';
TM.unresolvedCount=o=>Object.values(o||{}).filter(v=>v==null).length;
TM.deckLabel=x=>x?.deck!=null?"Deck "+x.deck+(x.section?" · Section "+x.section:""):(x?.section||"Ship location");
TM.shortName=s=>String(s||"").replace("Central ","").replace("Junior Officer ","").replace(" — Deck "+TM.S.deck,"").slice(0,22);
TM.showModal=html=>{TM.$("#modal-content").innerHTML=html;TM.$("#modal").showModal()};
TM.bind=()=>{
  document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>{
    TM.S.view=b.dataset.view;
    document.querySelectorAll("#nav button").forEach(x=>x.classList.toggle("active",x===b));
    TM.render();
  });
  TM.$("#modal-close").onclick=()=>TM.$("#modal").close();
};
TM.render=()=>{
  document.title="TrekMUD · "+TM.titleMap[TM.S.view];
  TM.$("#title").textContent=TM.titleMap[TM.S.view];
  const fn={now:TM.renderNow,map:TM.renderMap,character:TM.renderCharacter,crew:TM.renderCrew,threads:TM.renderThreads,timeline:TM.renderTimeline}[TM.S.view]||TM.renderNow;
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
    TM.bind();
    TM.render();
  }catch(e){
    TM.$("#view").innerHTML='<article class="card"><h2>Console unavailable</h2><p class="mini">'+TM.esc(e.message)+'</p></article>';
  }
};
document.addEventListener("DOMContentLoaded",TM.boot);

TM.deptClass=d=>"dept-"+String(d||"shipwide").toLowerCase().replace(/[^a-z0-9]+/g,"-");
TM.rankShort=r=>String(r||"").replace("Lieutenant Commander","Lt. Cmdr.").replace("Lieutenant junior grade","Lt. j.g.").replace("Lieutenant","Lt.").replace("Commander","Cmdr.").replace("Captain","Capt.");
TM.shipMark=()=>'<svg class="ship-mark" viewBox="0 0 240 110" aria-hidden="true"><path class="ship-main" d="M120 7C74 7 35 23 25 45l18 11-9 28 36 8 20-19h60l20 19 36-8-9-28 18-11C205 23 166 7 120 7Z"/><path class="ship-cut" d="M75 48h90l-16 18H91Z"/><path class="ship-nacelle" d="M40 62l-24 27 38 8 22-25Zm160 0 24 27-38 8-22-25Z"/></svg>';
