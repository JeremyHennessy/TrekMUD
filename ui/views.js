TM.renderNow=()=>{
  const d=TM.S.data,c=d.character,n=d.now,loc=n.location||{};
  const events=d.calendar.events.slice(0,3).map(e=>'<div class="item"><strong><span class="time">'+TM.esc(e.shipTime)+'</span>'+TM.esc(e.title)+'</strong><small>'+TM.esc(e.status)+'</small></div>').join("")||TM.empty();
  const threads=d.threads.map(t=>'<div class="item"><strong>'+TM.esc(t.title)+'</strong><small>'+TM.esc(t.summary)+'</small></div>').join("")||TM.empty();
  const knowledge=d.knowledge.map(k=>'<div class="item"><strong>'+TM.esc(k.subject)+'</strong><small>'+TM.esc(k.fact)+'</small></div>').join("")||TM.empty();
  const inventory=d.inventory.map(i=>'<div class="item"><strong>'+TM.esc(i.name)+'</strong><small>'+TM.esc(i.category)+'</small></div>').join("")||TM.empty();
  TM.$("#view").innerHTML=
    '<div class="hero">'+
      '<article class="card hero-main"><div class="hero-rank">'+TM.esc(c.rank)+' · '+TM.esc(c.department)+'</div><div class="hero-name">'+TM.esc(c.name)+'</div><div class="hero-role">'+TM.esc(c.billet)+'</div><div class="hero-location">'+TM.esc(loc.name||n.locationId)+'<small>'+TM.deckLabel(loc)+' · '+TM.esc(d.ship.name)+' at '+TM.esc(n.shipLocation)+'</small></div></article>'+
      '<article class="card"><h3>Ship status</h3><div class="status-line"><span class="label">Alert</span><span class="pill good">'+TM.esc(n.alertCondition)+'</span></div><div class="status-line"><span class="label">Checkpoint</span><span class="value">'+TM.esc(d.source.checkpointId)+'</span></div><div class="status-line"><span class="label">RNG</span><span class="value">'+TM.esc(d.rng.status)+' · '+TM.esc(d.rng.counter)+'</span></div><div class="status-line"><span class="label">Health</span><span class="value">'+TM.esc(c.health.injuryState)+' · fatigue '+TM.esc(c.health.fatigue)+'</span></div></article>'+
    '</div>'+
    '<div class="grid four">'+
      TM.card("Next obligations",'<div class="list">'+events+'</div>')+
      TM.card("Active threads",'<div class="list">'+threads+'</div>')+
      TM.card("Known crew",'<div class="metric">'+TM.esc(d.crew.materializedCount)+'</div><p class="mini">'+TM.esc(d.crew.backgroundCount)+' additional crew remain background until they matter in play.</p>')+
      TM.card("Organic character",'<div class="metric">'+TM.unresolvedCount(c.attributes)+'</div><p class="mini">attributes unresolved · '+TM.esc(c.discoveryState.academyRank1SlotsRemaining)+' Academy training slots remain</p>',"discovery")+
    '</div>'+
    '<div class="grid two" style="margin-top:18px">'+
      TM.card("What Jeremy knows",'<div class="list">'+knowledge+'</div>')+
      TM.card("Personal issue",'<div class="list">'+inventory+'</div>')+
    '</div>';
};

TM.renderCharacter=()=>{
  const c=TM.S.data.character;
  const attrs=Object.entries(c.attributes).map(([k,v])=>'<div class="attr '+(v==null?"unresolved":"")+'"><span>'+TM.esc(k)+'</span><b>'+(v==null?"◇":TM.esc(v))+'</b></div>').join("");
  const pool=(c.discoveryState.attributePoolRemaining||[]).map(v=>'<span>'+TM.esc(v)+'</span>').join("");
  const skills=Object.entries(c.skills).map(([k,v])=>'<tr><td>'+TM.esc(k)+'</td><td class="'+(v==null?"undiscovered":"")+'">'+(v==null?"Undiscovered":TM.esc(v))+'</td></tr>').join("");
  const facts=[...(c.discoveryState.backgroundFacts||[]),...(c.discoveryState.personalInterests||[]),...(c.discoveryState.traits||[])];
  const details=facts.length?facts.map(x=>'<div class="item">'+TM.esc(x)+'</div>').join(""):TM.empty("Character details will appear here as play establishes them.");
  const quals=TM.S.data.qualifications.map(q=>'<div class="item"><strong>'+TM.esc(q.name)+'</strong><small>'+TM.esc(q.status)+'</small></div>').join("");
  TM.$("#view").innerHTML=
    '<div class="grid two">'+
      '<article class="card"><h3>Identity</h3><div class="hero-name" style="font-size:2.4rem">'+TM.esc(c.name)+'</div><p class="mini">'+TM.esc(c.species)+' · age '+TM.esc(c.age)+' · '+TM.esc(c.pronouns)+'</p><div class="status-line"><span class="label">Rank</span><span class="value">'+TM.esc(c.rank)+'</span></div><div class="status-line"><span class="label">Department</span><span class="value">'+TM.esc(c.department)+'</span></div><div class="status-line"><span class="label">Billet</span><span class="value">'+TM.esc(c.billet)+'</span></div><div class="status-line"><span class="label">Upbringing</span><span class="value">'+TM.esc(c.upbringing)+'</span></div></article>'+
      '<article class="card discovery"><h3>Organic discovery</h3><p class="mini">Unresolved is not zero. Values lock only when play establishes them.</p><div class="attributes">'+attrs+'</div><div class="pool">'+pool+'</div><p class="mini">'+TM.esc(c.discoveryState.academyRank1SlotsRemaining)+' Academy rank-1 slots · department specialty '+(c.primarySpecialty?"locked":"open")+' · secondary specialty '+(c.secondarySpecialty?"locked":"open")+'</p></article>'+
    '</div>'+
    '<div class="grid two" style="margin-top:18px">'+
      '<article class="card"><h3>Skills</h3><table class="table"><thead><tr><th>Skill</th><th>Rank</th></tr></thead><tbody>'+skills+'</tbody></table></article>'+
      '<article class="card"><h3>Established details</h3><div class="list">'+details+'</div><h3 style="margin-top:20px">Qualifications</h3><div class="list">'+quals+'</div></article>'+
    '</div>';
};

TM.renderCrew=()=>{
  const d=TM.S.data;
  const deps=["ALL",...new Set(d.crew.materialized.map(x=>x.department).sort())];
  const list=d.crew.materialized.filter(p=>(TM.S.crewDept==="ALL"||p.department===TM.S.crewDept)&&(!TM.S.crewQuery||[p.name,p.rank,p.billet,p.species,p.department].join(" ").toLowerCase().includes(TM.S.crewQuery.toLowerCase())));
  TM.$("#view").innerHTML='<div class="toolbar"><input id="crew-search" placeholder="Search crew…" value="'+TM.esc(TM.S.crewQuery)+'"><select id="crew-dept">'+deps.map(x=>'<option '+(x===TM.S.crewDept?"selected":"")+'>'+TM.esc(x)+'</option>').join("")+'</select><span class="pill">'+list.length+' shown</span></div><div class="crew-grid">'+list.map(p=>'<article class="crew-card" data-id="'+TM.esc(p.id)+'"><div class="crew-rank">'+TM.esc(p.rank)+' · '+TM.esc(p.department)+'</div><div class="crew-name">'+TM.esc(p.name)+'</div><div class="crew-meta">'+TM.esc(p.species)+'<br>'+TM.esc(p.billet)+'<br>'+TM.esc(p.primaryShift)+' shift</div></article>').join("")+'</div>';
  TM.$("#crew-search").oninput=e=>{TM.S.crewQuery=e.target.value;TM.renderCrew()};
  TM.$("#crew-dept").onchange=e=>{TM.S.crewDept=e.target.value;TM.renderCrew()};
  document.querySelectorAll(".crew-card").forEach(x=>x.onclick=()=>TM.showCrew(x.dataset.id));
};

TM.showCrew=id=>{
  const p=TM.S.data.crew.materialized.find(x=>x.id===id);if(!p)return;
  const rel=p.relationships.length?TM.esc(p.relationships.map(r=>r.type||r.status||"Established").join(", ")):"No personal history established yet";
  TM.showModal('<div class="crew-rank">'+TM.esc(p.rank)+' · '+TM.esc(p.department)+'</div><h2>'+TM.esc(p.name)+'</h2><p>'+TM.esc(p.billet)+'</p><dl class="kv"><dt>Species</dt><dd>'+TM.esc(p.species)+'</dd><dt>Shift</dt><dd>'+TM.esc(p.primaryShift)+'</dd><dt>Relationship</dt><dd>'+rel+'</dd></dl>');
};

TM.renderThreads=()=>{
  const d=TM.S.data;
  const threads=d.threads.map(t=>'<div class="item"><strong>'+TM.esc(t.title)+'</strong><small>'+TM.esc(t.type)+' · '+TM.esc(t.status)+'<br>'+TM.esc(t.summary)+'</small></div>').join("")||TM.empty();
  const cal=d.calendar.events.map(e=>'<div class="item"><strong><span class="time">'+TM.esc(e.shipTime)+'</span>'+TM.esc(e.title)+'</strong><small>Stardate '+TM.esc(e.stardate)+' · '+TM.esc(e.status)+'</small></div>').join("")||TM.empty();
  TM.$("#view").innerHTML='<div class="grid two">'+TM.card("Open threads",'<div class="list">'+threads+'</div>')+TM.card("Known schedule",'<div class="list">'+cal+'</div>')+'</div>';
};

TM.renderTimeline=()=>{
  const rows=TM.S.data.timeline;
  const body=rows.length?rows.map(r=>'<div class="timeline-item"><div class="timeline-date">'+TM.esc(r.year)+' · '+(r.stardate?"SD "+TM.esc(r.stardate):"")+'</div><div class="timeline-title">'+TM.esc(r.title)+'</div><div class="timeline-copy">'+TM.esc(r.summary)+'</div></div>').join(""):TM.empty();
  TM.$("#view").innerHTML='<article class="card"><h3>Service & discovery timeline</h3><div class="timeline">'+body+'</div></article>';
};
