#!/usr/bin/env python3
"""Presentation-only Nebula-class layout helpers for the TrekMUD console.

Canonical geography remains campaign/locations.json. This module creates a
stable, human-readable visual layout for USS Asteria without changing any
campaign location IDs or topology.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

DECK_LABELS={
  1:"Command",2:"Command Support",3:"Senior Officers & Pod Access",
  4:"Primary Science",5:"Advanced Sciences",6:"Medical",
  7:"Junior Officers",8:"Crew & Families",9:"Transport & Operations",
  10:"Computer & Mission Ops",11:"Recreation",12:"Mess & Arboretum",
  13:"Flight Operations",14:"Main Shuttlebay",15:"Cargo & Logistics",
  16:"Security & Tactical",17:"Damage Control",18:"Engineering Upper",
  19:"Main Engineering",20:"Engineering Lower",21:"Deflector & Sensors",
  22:"Environmental",23:"Fuel Processing",24:"Antimatter & Emergency Power",
  25:"Lower Sensors & Maintenance",26:"Cargo & Rescue",27:"Lower Structural",
  28:"Ventral Systems",
}
DECK_WIDTHS={
  1:40,2:53,3:67,4:80,5:90,6:97,7:100,8:100,9:100,10:99,
  11:98,12:96,13:93,14:90,15:86,16:81,17:76,18:70,19:65,20:60,
  21:55,22:51,23:47,24:43,25:39,26:36,27:33,28:30,
}
POD_LABELS={
  "P1":"Science Pod Control",
  "P2":"Long-Range Sensors",
  "P3":"Mission Specialist Lab",
  "P4":"Sensor Maintenance",
}
TYPE_PRIORITY={
 "bridge":0,"office":1,"conference":2,"lab":3,"medical":4,"security":5,
 "operations":6,"computer":7,"transporter":8,"flight-control":9,"hangar":10,
 "engineering":11,"cargo":12,"quarters":13,"lounge":14,"mess":15,
 "holodeck":16,"recreation":17,"training":18,"equipment":19,"service":20,
 "safety":21,"airlock":22,"science-pod":23,
}
DEPARTMENT_ORDER={
 "command":0,"science":1,"medical":2,"operations":3,"engineering":4,
 "security":5,"tactical":6,"flight":7,"counseling":8,"personnel":9,
 "logistics":10,"shipwide":11,
}

def _sort(row:dict[str,Any])->tuple[Any,...]:
    return (
      TYPE_PRIORITY.get(str(row.get("type")),50),
      DEPARTMENT_ORDER.get(str(row.get("department")),50),
      str(row.get("name","")),str(row.get("id",""))
    )

def _row_counts(count:int)->list[int]:
    if count<=4:return [count]
    if count<=8:
        top=math.ceil(count/2);return [top,count-top]
    top=min(4,math.ceil(count/3));bottom=min(4,math.ceil((count-top)/2))
    return [top,count-top-bottom,bottom]

def _row_positions(count:int,hull_w:float,y:float)->list[dict[str,float]]:
    if count<=0:return []
    pad=max(4.0,hull_w*.055);usable=hull_w-pad*2;gap=2.0
    width=min(19.0,(usable-gap*(count-1))/count)
    total=width*count+gap*(count-1);start=50-total/2
    return [{"x":round(start+i*(width+gap),2),"y":y,"w":round(width,2),"h":12.0} for i in range(count)]

def _middle_positions(count:int,hull_w:float)->list[dict[str,float]]:
    if count<=0:return []
    left=50-min(31.0,hull_w*.32);right=50+min(31.0,hull_w*.32)
    out=[]
    for i in range(count):
        cx=left if i%2==0 else right;level=i//2
        out.append({"x":round(cx-8.2,2),"y":round(42+level*13.5,2),"w":16.4,"h":11.0})
    return out

def _plan(key:str,label:str,width:float,rows:list[dict[str,Any]],edges:list[dict[str,Any]],kind:str)->dict[str,Any]:
    hull_x=round(50-width/2,2)
    tls=[r for r in rows if str(r.get("id","")).endswith("-TL-C")]
    hubs=[r for r in rows if str(r.get("id","")).endswith("-HUB-C")]
    corridors=[r for r in rows if r.get("type")=="corridor" and r not in tls and r not in hubs]
    rooms=sorted([r for r in rows if r not in tls and r not in hubs and r not in corridors],key=_sort)
    positions=[];counts=_row_counts(len(rooms))
    if len(counts)==1: positions+=_row_positions(counts[0],width,31.0)
    elif len(counts)==2:
        positions+=_row_positions(counts[0],width,22.0);positions+=_row_positions(counts[1],width,68.0)
    else:
        positions+=_row_positions(counts[0],width,18.0);positions+=_middle_positions(counts[1],width);positions+=_row_positions(counts[2],width,73.0)
    compartments=[{
      "id":room.get("id"),"name":room.get("name"),"type":room.get("type"),
      "department":room.get("department"),"access":room.get("access"),
      "section":room.get("section"),**pos
    } for room,pos in zip(rooms,positions)]
    circulation=[]
    if tls:
        circulation.append({"id":tls[0].get("id"),"name":tls[0].get("name"),"kind":"turbolift","x":round(hull_x+4,2),"y":43.5,"w":9,"h":13})
    if hubs:
        circulation.append({"id":hubs[0].get("id"),"name":hubs[0].get("name"),"kind":"hub","x":44,"y":43,"w":12,"h":14})
    for i,row in enumerate(corridors):
        circulation.append({"id":row.get("id"),"name":row.get("name"),"kind":"corridor","x":round(28+i*13,2),"y":46,"w":12,"h":8})
    ids={r.get("id") for r in rows}
    plan_edges=[{"from":e.get("from"),"to":e.get("to"),"type":e.get("type"),"access":e.get("access")} for e in edges if e.get("from") in ids and e.get("to") in ids]
    deps=Counter(str(r.get("department","shipwide")) for r in rooms)
    return {
      "key":key,"kind":kind,"label":label,"hull":{"x":hull_x,"width":width},
      "primaryDepartment":deps.most_common(1)[0][0] if deps else "shipwide",
      "roomCount":len(rows),"compartmentCount":len(compartments),
      "compartments":compartments,"circulation":circulation,"edges":plan_edges,
    }

def build_map_layout(locations:list[dict[str,Any]],edges:list[dict[str,Any]],current_location_id:str|None)->dict[str,Any]:
    numbered=[r for r in locations if isinstance(r.get("deck"),int)]
    decks=sorted({int(r["deck"]) for r in numbered})
    deck_plans={
      str(deck):_plan(str(deck),DECK_LABELS.get(deck,f"Deck {deck}"),float(DECK_WIDTHS.get(deck,70)),[r for r in numbered if r.get("deck")==deck],edges,"deck")
      for deck in decks
    }
    pod_sections=sorted({str(r.get("section")) for r in locations if r.get("deck") is None and str(r.get("section","")).startswith("P")})
    pod_plans={
      pod:_plan(pod,POD_LABELS.get(pod,pod),54.0,[r for r in locations if r.get("deck") is None and r.get("section")==pod],edges,"pod")
      for pod in pod_sections
    }
    current=next((r for r in locations if r.get("id")==current_location_id),None)
    current_key=str(current.get("deck")) if current and current.get("deck") is not None else (str(current.get("section")) if current else None)
    profile=[{
      "deck":deck,"key":str(deck),"label":deck_plans[str(deck)]["label"],
      "width":DECK_WIDTHS.get(deck,70),"roomCount":deck_plans[str(deck)]["roomCount"],
      "primaryDepartment":deck_plans[str(deck)]["primaryDepartment"],
      "current":str(deck)==current_key
    } for deck in decks]
    pod_profile=[{
      "key":pod,"label":pod_plans[pod]["label"],"roomCount":pod_plans[pod]["roomCount"],
      "primaryDepartment":pod_plans[pod]["primaryDepartment"],"current":pod==current_key
    } for pod in pod_sections]
    return {
      "currentKey":current_key,"currentDeck":current.get("deck") if current else None,
      "profile":profile,"podProfile":pod_profile,
      "deckPlans":deck_plans,"podPlans":pod_plans,
      "deckNumbers":decks,"podLevels":pod_sections,
      "shipSilhouette":"nebula",
    }
