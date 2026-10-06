#!/usr/bin/env python3
"""Validate the candidate USS Asteria Nebula-class location graph."""

from __future__ import annotations
import argparse, json, sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

DEFAULT_PATH=Path(__file__).resolve().parents[1]/"world"/"asteria"/"topology.json"

class ValidationError(RuntimeError): pass
def require(c:bool,m:str)->None:
    if not c: raise ValidationError(m)
def load(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(v,dict),"topology must be an object")
    return v

def validate(path:Path)->dict[str,Any]:
    data=load(path)
    require(data.get("schemaVersion")==2,"schemaVersion must be 2")
    require(data.get("shipId")=="USS-ASTERIA","shipId mismatch")
    require(data.get("class")=="Nebula-class","class mismatch")
    require(data.get("deckCount")==28,"Asteria baseline must have 28 numbered decks")
    locs=data.get("locations"); edges=data.get("edges")
    require(isinstance(locs,list) and locs,"locations required")
    require(isinstance(edges,list) and edges,"edges required")
    by_id={}; numbered=set(); pod=set()
    for i,row in enumerate(locs):
        require(isinstance(row,dict),f"locations[{i}] must be object")
        lid=row.get("id")
        require(isinstance(lid,str) and lid.startswith("AST-"),f"invalid Asteria location id {lid}")
        require(lid not in by_id,f"duplicate location id {lid}")
        by_id[lid]=row
        deck=row.get("deck")
        if deck is not None:
            require(isinstance(deck,int) and 1<=deck<=28,f"{lid} invalid deck {deck}")
            numbered.add(deck)
        elif isinstance(row.get("section"),str) and row["section"].startswith("P"):
            pod.add(row["section"])
        require(row.get("access") in {"crew","restricted","assigned"},f"{lid} invalid access")
        require(row.get("source") in {"SETTING_FILL","CANON_CONSTRAINED"},f"{lid} invalid source")
    require(numbered==set(range(1,29)),"all decks 1-28 must exist")
    require(pod=={"P1","P2","P3","P4"},"science pod levels P1-P4 must exist")

    adj=defaultdict(set); seen_edges=set()
    for i,e in enumerate(edges):
        require(isinstance(e,dict),f"edges[{i}] must be object")
        a,b,t=e.get("from"),e.get("to"),e.get("type")
        require(a in by_id and b in by_id,f"edge {i} unresolved endpoint")
        require(a!=b,f"edge {i} self-loop")
        require(isinstance(t,str) and t,f"edge {i} missing type")
        key=(str(a),str(b),t); rev=(str(b),str(a),t)
        require(key not in seen_edges and rev not in seen_edges,f"duplicate edge {a}<->{b}")
        seen_edges.add(key); adj[str(a)].add(str(b))
        if e.get("bidirectional",True): adj[str(b)].add(str(a))

    opening=data.get("playerOpening") or {}
    arrival=opening.get("arrivalLocationId"); quarters=opening.get("assignedQuartersId")
    require(arrival=="AST-D09-TR-02","opening arrival must be Asteria Transporter Room 2")
    require(quarters=="AST-D07-S12-0712C","opening quarters must remain 0712-C")
    require(arrival in by_id and quarters in by_id,"opening locations must resolve")
    require(by_id[quarters].get("deck")==7 and str(by_id[quarters].get("section"))=="12","quarters continuity mismatch")

    reached={arrival}; q=deque([arrival])
    while q:
        cur=q.popleft()
        for nxt in adj[cur]:
            if nxt not in reached:
                reached.add(nxt); q.append(nxt)
    missing=sorted(set(by_id)-reached)
    require(not missing,f"unreachable locations: {missing[:10]}")

    for deck in range(1,29):
        dd=f"{deck:02d}"
        require(f"AST-D{dd}-TL-C" in by_id,f"deck {deck} missing turbolift")
        require(f"AST-D{dd}-HUB-C" in by_id,f"deck {deck} missing hub")

    return {
        "valid":True,"locations":len(locs),"edges":len(edges),
        "numberedDecks":len(numbered),"podLevels":len(pod),
        "reachableLocations":len(reached),"openingArrival":arrival,"openingQuarters":quarters
    }

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--path",type=Path,default=DEFAULT_PATH);a=p.parse_args()
    try:
        print(json.dumps(validate(a.path.resolve()),indent=2));return 0
    except (ValidationError,OSError,json.JSONDecodeError) as e:
        print(f"INVALID ASTERIA TOPOLOGY: {e}",file=sys.stderr);return 2
if __name__=="__main__": raise SystemExit(main())
