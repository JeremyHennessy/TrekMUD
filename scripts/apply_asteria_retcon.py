#!/usr/bin/env python3
"""Apply the approved pre-play USS Asteria Nebula-class baseline retcon.

This is a zero-time, zero-narrative migration from public checkpoint r00002.
It preserves Jeremy, the 20 persistent NPC identities, RNG commitment/counter,
calendar, active thread, and all organic character discovery state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_campaign import validate

ROOT=Path(__file__).resolve().parents[1]

class RetconError(RuntimeError): pass
def require(c:bool,m:str)->None:
    if not c: raise RetconError(m)
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8"));require(isinstance(v,dict),f"{p} must contain object");return v
def write(p:Path,v:dict[str,Any])->None:
    p.write_text(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def apply(root:Path)->dict[str,Any]:
    state_path=root/"campaign"/"state.json"
    state=load(state_path)
    require(state.get("revision")==2,"Asteria retcon requires revision 2")
    require((state.get("checkpoint") or {}).get("lastCheckpointId")=="r00002","Asteria retcon requires r00002")
    require((state.get("checkpoint") or {}).get("validated") is True,"r00002 must be validated")
    require(state.get("status")=="READY_TO_START","retcon only permitted before Scene One")
    require(state.get("ship",{}).get("id")=="USS-MERIDIAN","expected pre-retcon USS Meridian baseline")

    components=state["components"]
    docs={key:load(root/rel) for key,rel in components.items()}
    character_doc=docs["character"]; character=character_doc.get("character") or {}
    require(character.get("id")=="PC-001","player character missing")
    require(docs["rng"].get("counter")==0,"pre-play retcon requires zero RNG draws")

    topology=load(root/"world"/"asteria"/"topology.json")
    crew_structure=load(root/"world"/"asteria"/"crew-structure.json")
    crew_directory=load(root/"world"/"asteria"/"crew-directory.json")

    revision=3
    for doc in docs.values():
        require(doc.get("revision")==2,"all campaign components must start at revision 2")
        doc["revision"]=revision

    # Character assignment and location references.
    character["assignment"]["shipId"]="USS-ASTERIA"
    character["assignment"]["shipName"]="USS Asteria"
    character["assignment"]["registry"]="NCC-63542"
    character["quartersId"]="AST-D07-S12-0712C"

    # Public ship state.
    ship=docs["ship"]["ship"]
    ship.update({
        "id":"USS-ASTERIA",
        "name":"USS Asteria",
        "registry":"NCC-63542",
        "registrySource":"TREKMUD_ORIGINAL",
        "class":"Nebula-class",
        "commissioned":2367,
        "location":"Starbase 375",
        "mission":None,
        "alertCondition":"normal",
        "commandingOfficerId":"CREW-001",
        "executiveOfficerId":"CREW-002",
        "secondOfficerId":"CREW-003",
    })
    ship["systems"]={
        "dorsalPod":{
            "type":"triangular sensor/science pod",
            "status":"nominal",
            "levels":4,
        }
    }

    # Crew complement includes Jeremy.
    docs["crew"].update({
        "shipId":"USS-ASTERIA",
        "nominalCrewComplement":crew_structure["nominalComplement"],
        "playerIncludedInComplement":True,
        "baselineStatus":"APPROVED_RETCON",
        "baselineVersion":"asteria-v1",
        "materializedCrew":crew_directory["people"],
        "backgroundPopulation":{
            "count":crew_structure["nominalComplement"]-len(crew_directory["people"])-1,
            "note":"Tier-3 background crew excluding Jeremy and 20 materialized NPCs; identities materialize through play."
        },
    })
    docs["crew"].pop("baselineCommit",None)

    # Authoritative live geography.
    docs["locations"].update({
        "shipId":"USS-ASTERIA",
        "baselineStatus":"APPROVED_RETCON",
        "baselineVersion":"asteria-v1",
        "locations":topology["locations"],
        "edges":topology["edges"],
    })
    docs["locations"].pop("baselineCommit",None)

    # Assignment knowledge and service history are pre-play corrections.
    for fact in docs["knowledge"].get("facts",[]):
        if fact.get("id")=="KN-00001":
            fact["subject"]="USS Asteria"
            fact["fact"]="Assigned vessel is USS Asteria, NCC-63542, Nebula-class."
    for event in docs["serviceRecord"].get("events",[]):
        if event.get("id")=="SR-00001":
            event["shipId"]="USS-ASTERIA"
            event["summary"]="Reported aboard USS Asteria for initial assignment."

    state["revision"]=revision
    state["ship"].update({
        "id":"USS-ASTERIA",
        "name":"USS Asteria",
        "registry":"NCC-63542",
        "class":"Nebula-class",
        "location":"Starbase 375",
        "mission":None,
        "alertCondition":"normal",
        "commandingOfficerId":"CREW-001",
        "executiveOfficerId":"CREW-002",
    })
    state["player"]["locationId"]="AST-D09-TR-02"
    state["checkpoint"]={"lastCheckpointId":"r00002","validated":False}

    config_path=root/"campaign"/"config.json"
    config=load(config_path)
    config["campaignName"]="TrekMUD: USS Asteria"
    config["start"].update({
        "ship":"USS Asteria",
        "registry":"NCC-63542",
        "shipClass":"Nebula-class",
        "arrivalLocationId":"AST-D09-TR-02",
        "quartersId":"AST-D07-S12-0712C",
        "location":"Starbase 375",
    })
    config["baselines"]["currentShip"]="asteria-v1"
    config["shipRetcon"]={
        "from":"USS Meridian / Akira-class",
        "to":"USS Asteria / Nebula-class",
        "reason":"Pre-play campaign baseline revision requested before Scene One.",
        "effectiveRevision":3,
        "inUniverseEvent":False,
    }

    chronicle_path=root/"campaign"/"CHRONICLE.md"
    chronicle=chronicle_path.read_text(encoding="utf-8").rstrip()
    chronicle += (
        "\n\n## Pre-play ship baseline retcon — revision 3\n\n"
        "- Before Scene One, the assigned vessel baseline was revised from USS Meridian (Akira-class) to USS Asteria, NCC-63542 (Nebula-class).\n"
        "- This is a campaign-baseline correction, not an in-universe rename, refit, or transfer.\n"
        "- Transporter Room 2 remains the opening room on Deck 9.\n"
        "- Assigned quarters remain Deck 7, Section 12, cabin 0712-C.\n"
        "- The Asteria uses a 28-deck TrekMUD layout plus a four-level triangular sensor/science pod.\n"
        "- Nominal complement is 750 including Jeremy; 20 NPC identities remain materialized and 729 crew remain background.\n"
        "- Ship time remains 1217, Stardate 49317.4; RNG counter remains 0; no narrative action occurred.\n"
    )

    for key,rel in components.items(): write(root/rel,docs[key])
    write(state_path,state);write(config_path,config)
    chronicle_path.write_text(chronicle+"\n",encoding="utf-8")

    result=validate(root)
    require(result["valid"] is True and result["revision"]==revision,"post-retcon validation failed")
    return {
        "valid":True,"revision":revision,"checkpointRequired":"r00003",
        "ship":"USS Asteria","class":"Nebula-class","registry":"NCC-63542",
        "locations":len(topology["locations"]),"edges":len(topology["edges"]),
        "nominalComplement":crew_structure["nominalComplement"],
        "backgroundCrew":docs["crew"]["backgroundPopulation"]["count"],
        "playerLocation":state["player"]["locationId"],
        "shipTime":state["currentTime"]["shipTime"],"stardate":state["currentTime"]["stardate"],
        "rngCounter":docs["rng"]["counter"],
    }

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(apply(a.root.resolve()),indent=2));return 0
if __name__=="__main__": raise SystemExit(main())
