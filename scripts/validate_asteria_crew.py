#!/usr/bin/env python3
"""Validate USS Asteria crew structure and preserved public directory."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
class ValidationError(RuntimeError): pass
def require(c:bool,m:str)->None:
    if not c: raise ValidationError(m)
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"));require(isinstance(v,dict),f"{p} must contain object");return v

def validate(sp:Path,dp:Path)->dict[str,Any]:
    s,d=load(sp),load(dp)
    require(s.get("schemaVersion")==2 and d.get("schemaVersion")==2,"Asteria crew schemas must be 2")
    require(s.get("shipId")=="USS-ASTERIA" and d.get("shipId")=="USS-ASTERIA","shipId mismatch")
    nominal=s.get("nominalComplement");require(nominal==750,"Asteria nominal complement must be 750")
    require(s.get("complementIncludesPlayer") is True,"Asteria complement must include player")
    deps=s.get("departments");require(isinstance(deps,list) and deps,"departments required")
    dep_ids=set(); dep_total=0
    for row in deps:
        did=row.get("id");require(isinstance(did,str) and did and did not in dep_ids,f"bad department {did}")
        dep_ids.add(did);count=row.get("nominalPersonnel");require(isinstance(count,int) and count>0,f"{did} bad count");dep_total+=count
    require(dep_total==nominal,f"department total {dep_total} != {nominal}")
    shifts=(s.get("shiftModel") or {}).get("shifts");require(isinstance(shifts,list),"shifts required")
    shift_ids=set();shift_total=0
    for row in shifts:
        sid=row.get("id");require(isinstance(sid,str) and sid not in shift_ids,f"bad shift {sid}")
        shift_ids.add(sid);count=row.get("nominalPersonnel");require(isinstance(count,int) and count>0,"bad shift count");shift_total+=count
    require(shift_ids=={"ALPHA","BETA","GAMMA"},"Alpha/Beta/Gamma required")
    require(shift_total==nominal,f"shift total {shift_total} != {nominal}")

    people=d.get("people");require(isinstance(people,list) and len(people)==20,"preserve 20 starting NPC identities")
    ids=set();names=set()
    for p in people:
        pid=p.get("id");name=p.get("name")
        require(isinstance(pid,str) and pid.startswith("CREW-") and pid not in ids,f"bad crew id {pid}");ids.add(pid)
        require(isinstance(name,str) and name and name not in names,f"bad crew name {name}");names.add(name)
        require(p.get("department") in dep_ids,f"{pid} unknown department")
        require(p.get("primaryShift") in shift_ids,f"{pid} unknown shift")
        require(p.get("tier") in {1,2} and p.get("status")=="ACTIVE",f"{pid} invalid state")

    billets={p["billet"]:p for p in people}
    for dep,billet in {
      "ENGINEERING":"Chief Engineer","OPERATIONS":"Chief Operations Officer / Second Officer",
      "SCIENCE":"Chief Science Officer","MEDICAL":"Chief Medical Officer","SECURITY":"Chief Security Officer",
      "TACTICAL":"Chief Tactical Officer","FLIGHT":"Chief Flight Control Officer",
      "COUNSELING":"Chief Counselor","LOGISTICS":"Chief Logistics Officer"
    }.items():
        require(billet in billets and billets[billet]["department"]==dep,f"missing {billet}")
    require("Commanding Officer" in billets and "Executive Officer" in billets,"command chain missing")
    quarters=[p.get("quartersCandidate") for p in people if p.get("quartersCandidate")]
    require(len(quarters)==len(set(quarters)),"duplicate quarters")
    require(all(q.startswith("AST-D07-S12-0712") for q in quarters),"quarters IDs must use Asteria prefix")
    player=s.get("playerAccounting") or {}
    require(player.get("playerId")=="PC-001" and player.get("playerDepartment")=="SCIENCE","player accounting mismatch")
    return {"valid":True,"nominalComplement":nominal,"npcDirectory":len(people),"playerIncluded":True,"departments":len(dep_ids)}

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--structure",type=Path,default=ROOT/"world"/"asteria"/"crew-structure.json")
    p.add_argument("--directory",type=Path,default=ROOT/"world"/"asteria"/"crew-directory.json")
    a=p.parse_args()
    try: print(json.dumps(validate(a.structure.resolve(),a.directory.resolve()),indent=2));return 0
    except (ValidationError,OSError,json.JSONDecodeError) as e:
        print(f"INVALID ASTERIA CREW MODEL: {e}",file=sys.stderr);return 2
if __name__=="__main__": raise SystemExit(main())
