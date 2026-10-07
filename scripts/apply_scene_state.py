#!/usr/bin/env python3
"""Apply basic visible scene state as one coherent campaign revision."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from validate_campaign import validate

ROOT=Path(__file__).resolve().parents[1]

class SceneError(RuntimeError): pass

def require(c:bool,m:str)->None:
    if not c: raise SceneError(m)

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value,dict),f"{path} must contain an object")
    return value

def write(path:Path,value:dict[str,Any])->None:
    path.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def minutes(value:str)->int:
    h,m=map(int,value.split(":"))
    require(0<=h<24 and 0<=m<60,f"invalid ship time: {value}")
    return h*60+m

def time_text(value:int)->str:
    require(0<=value<1440,"basic scene tool cannot cross a ship-day boundary")
    return f"{value//60:02d}:{value%60:02d}"

def apply(root:Path,request:dict[str,Any])->dict[str,Any]:
    state_path=root/"campaign/state.json"
    state=load(state_path)
    require(state.get("status") in {"READY_TO_START","ACTIVE"},"campaign is not playable")

    components=state["components"]
    docs={key:load(root/rel) for key,rel in components.items()}
    old_revision=state["revision"]
    for key,doc in docs.items():
        require(doc.get("revision")==old_revision,f"{key} revision mismatch")

    summary=request.get("summary")
    require(isinstance(summary,str) and summary.strip(),"summary is required")
    changes=[]

    advance=request.get("advanceMinutes",0)
    require(isinstance(advance,int) and 0<=advance<=720,"advanceMinutes must be 0-720")
    if advance:
        old=state["currentTime"]["shipTime"]
        new=time_text(minutes(old)+advance)
        state["currentTime"]["shipTime"]=new
        docs["calendar"]["current"]["shipTime"]=new
        changes.append(f"time {old} -> {new}")

    destination=request.get("locationId")
    if destination is not None:
        by_id={row["id"]:row for row in docs["locations"].get("locations",[])}
        require(destination in by_id,f"unknown location: {destination}")
        require(by_id[destination].get("access")!="restricted","basic scene move cannot enter a restricted location")
        old=state["player"]["locationId"]
        state["player"]["locationId"]=destination
        changes.append(f"location {old} -> {destination}")

    if request.get("activateCampaign") is True and state["status"]=="READY_TO_START":
        state["status"]="ACTIVE"
        changes.append("campaign READY_TO_START -> ACTIVE")

    updates=request.get("calendarStatusUpdates",[])
    require(isinstance(updates,list),"calendarStatusUpdates must be a list")
    by_event={row["id"]:row for row in docs["calendar"].get("events",[])}
    for row in updates:
        require(isinstance(row,dict),"calendar update must be an object")
        event_id=row.get("id")
        require(event_id in by_event,f"unknown calendar event: {event_id}")
        status=row.get("status")
        require(isinstance(status,str) and status.strip(),"calendar status is required")
        by_event[event_id]["status"]=status.strip()
        changes.append(f"calendar {event_id} -> {status.strip()}")

    new_revision=old_revision+1
    for doc in docs.values(): doc["revision"]=new_revision
    state["revision"]=new_revision
    state["checkpoint"]={"lastCheckpointId":state["checkpoint"]["lastCheckpointId"],"validated":False}

    chronicle=root/"campaign/CHRONICLE.md"
    text=chronicle.read_text(encoding="utf-8").rstrip()
    text+=f"\n\n## Scene state — revision {new_revision}\n\n- {summary.strip()}\n"
    for change in changes: text+=f"- {change}.\n"

    for key,rel in components.items(): write(root/rel,docs[key])
    write(state_path,state)
    chronicle.write_text(text+"\n",encoding="utf-8")

    result=validate(root)
    require(result["valid"] is True,"post-scene validation failed")
    return {
        "valid":True,
        "previousRevision":old_revision,
        "revision":new_revision,
        "checkpointRequired":f"r{new_revision:05d}",
        "changes":changes,
        "currentTime":state["currentTime"],
        "playerLocation":state["player"]["locationId"],
        "campaignStatus":state["status"],
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--input",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(apply(args.root.resolve(),load(args.input.resolve())),indent=2))
