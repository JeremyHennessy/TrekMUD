#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path:Path)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"{path} must contain an object")
    return value

def build(root:Path)->dict:
    state=load(root/"campaign/state.json")
    char=(load(root/"campaign/character.json").get("character") or {})
    cal=load(root/"campaign/calendar.json")
    threads=load(root/"campaign/active-threads.json")
    records=load(root/"campaign/records.json")
    rng=load(root/"campaign/rng.json")
    locations=load(root/"campaign/locations.json")
    by_id={row["id"]:row for row in locations.get("locations",[])}
    loc_id=(state.get("player") or {}).get("locationId")
    loc=by_id.get(loc_id) or {}
    discovery=char.get("discoveryState") or {}
    events=sorted(cal.get("events",[]),key=lambda x:(x.get("stardate",999999),x.get("shipTime","99:99")))
    return {
        "checkpointId":(state.get("checkpoint") or {}).get("lastCheckpointId"),
        "revision":state.get("revision"),
        "rulesVersion":state.get("rulesVersion"),
        "campaignStatus":state.get("status"),
        "currentTime":state.get("currentTime"),
        "ship":state.get("ship"),
        "player":{
            "id":char.get("id"),"name":char.get("name"),"rank":char.get("rank"),
            "department":char.get("department"),"billet":char.get("billet"),
            "locationId":loc_id,"locationName":loc.get("name"),
            "deck":loc.get("deck"),"section":loc.get("section"),
            "quartersId":char.get("quartersId"),
        },
        "organicDiscovery":{
            "unresolvedAttributes":sum(v is None for v in (char.get("attributes") or {}).values()),
            "attributePoolRemaining":discovery.get("attributePoolRemaining",[]),
            "academyRank1SlotsRemaining":discovery.get("academyRank1SlotsRemaining"),
            "departmentSpecialtyAvailable":discovery.get("departmentSpecialtyAvailable"),
            "secondarySpecialtyAvailable":discovery.get("secondarySpecialtyAvailable"),
        },
        "activeThreads":threads.get("threads",[]),
        "nextCalendarEvents":events[:5],
        "recordCounts":{
            "duty":len(records.get("dutyLogs",[])),
            "science":len(records.get("scienceFindings",[])),
            "missions":len(records.get("missionRecords",[])),
            "relationships":len(records.get("relationshipMilestones",[])),
            "ship":len(records.get("shipEvents",[])),
        },
        "rng":{"status":rng.get("status"),"counter":rng.get("counter")},
    }

def markdown(packet:dict)->str:
    p=packet["player"];t=packet["currentTime"];s=packet["ship"];d=packet["organicDiscovery"];r=packet["recordCounts"]
    lines=[
      "# TrekMUD resume packet","",
      f"- Checkpoint: {packet['checkpointId']} / revision {packet['revision']}",
      f"- Status: {packet['campaignStatus']} · Rules v{packet['rulesVersion']}",
      f"- Time: {t.get('shipTime')} · Stardate {t.get('stardate')} · {t.get('year')}",
      f"- Ship: {s.get('name')} {s.get('registry')} · {s.get('class')} · {s.get('location')}",
      f"- Player: {p.get('rank')} {p.get('name')} · {p.get('department')} · {p.get('billet')}",
      f"- Location: {p.get('locationName')} ({p.get('locationId')})",
      f"- RNG counter: {packet['rng'].get('counter')}","",
      "## Organic character","",
      f"- Unresolved attributes: {d.get('unresolvedAttributes')}",
      f"- Remaining attribute pool: {d.get('attributePoolRemaining')}",
      f"- Academy rank-1 slots: {d.get('academyRank1SlotsRemaining')}","",
      "## Active threads",""
    ]
    lines += [f"- {x.get('id')} · {x.get('title')}: {x.get('summary')}" for x in packet["activeThreads"]] or ["- None"]
    lines += ["","## Upcoming calendar",""]
    lines += [f"- {x.get('shipTime')} · {x.get('title')} · {x.get('status')}" for x in packet["nextCalendarEvents"]] or ["- None"]
    lines += ["","## Player-visible record counts","",
              f"- Duty: {r['duty']}",f"- Science: {r['science']}",f"- Missions: {r['missions']}",
              f"- Relationships: {r['relationships']}",f"- Ship events: {r['ship']}",""]
    return "\n".join(lines)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--write-json",type=Path)
    parser.add_argument("--write-md",type=Path)
    args=parser.parse_args()
    packet=build(args.root.resolve())
    if args.write_json:
        args.write_json.write_text(json.dumps(packet,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.write_md:
        args.write_md.write_text(markdown(packet),encoding="utf-8")
    print(json.dumps(packet,indent=2,ensure_ascii=False))
