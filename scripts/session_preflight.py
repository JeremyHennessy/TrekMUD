#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

from build_player_console import player_safe_snapshot
from build_resume_packet import build as build_resume
from checkpoint_integrity import verify as verify_checkpoint
from validate_asteria import validate as validate_asteria
from validate_asteria_crew import validate as validate_asteria_crew
from validate_campaign import validate as validate_campaign

ROOT=Path(__file__).resolve().parents[1]

def run(root:Path)->dict:
    campaign=validate_campaign(root)
    asteria=validate_asteria(root/"world/asteria/topology.json")
    crew=validate_asteria_crew(
        root/"world/asteria/crew-structure.json",
        root/"world/asteria/crew-directory.json",
    )
    checkpoint=verify_checkpoint(root)
    resume=build_resume(root)
    console=player_safe_snapshot(root)

    assert console["source"]["checkpointId"]==checkpoint["checkpointId"]
    assert console["source"]["campaignRevision"]==checkpoint["revision"]
    assert console["now"]["locationId"]==resume["player"]["locationId"]
    assert console["rng"]["counter"]==resume["rng"]["counter"]

    return {
        "ready":True,
        "campaign":campaign,
        "asteria":asteria,
        "crew":crew,
        "checkpoint":checkpoint,
        "resume":resume,
        "console":{
            "checkpointId":console["source"]["checkpointId"],
            "revision":console["source"]["campaignRevision"],
            "locations":len(console["map"]["locations"]),
            "materializedCrew":console["crew"]["materializedCount"],
        },
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--write-json",type=Path)
    args=parser.parse_args()
    result=run(args.root.resolve())
    if args.write_json:
        args.write_json.parent.mkdir(parents=True,exist_ok=True)
        args.write_json.write_text(
            json.dumps(result,indent=2,ensure_ascii=False)+"\n",
            encoding="utf-8",
        )
    print(json.dumps(result,indent=2,ensure_ascii=False))
