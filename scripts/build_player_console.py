#!/usr/bin/env python3
"""Build the TrekMUD player console from public campaign state only."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_map_layout import build_map_layout

ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT / "ui"
DEFAULT_OUTPUT = ROOT / "_site"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def location_index(locations_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in locations_doc.get("locations", [])}


def player_safe_snapshot(root: Path) -> dict[str, Any]:
    campaign = root / "campaign"
    state = load_json(campaign / "state.json")
    character_doc = load_json(campaign / "character.json")
    crew_doc = load_json(campaign / "crew.json")
    relationships = load_json(campaign / "relationships.json")
    knowledge = load_json(campaign / "knowledge.json")
    threads = load_json(campaign / "active-threads.json")
    calendar = load_json(campaign / "calendar.json")
    service = load_json(campaign / "service-record.json")
    locations = load_json(campaign / "locations.json")
    ship_doc = load_json(campaign / "ship.json")
    inventory = load_json(campaign / "inventory.json")
    qualifications = load_json(campaign / "qualifications.json")
    rng = load_json(campaign / "rng.json")
    records_path = campaign / "records.json"
    records = load_json(records_path) if records_path.exists() else {
        "dutyLogs": [],
        "scienceFindings": [],
        "missionRecords": [],
        "relationshipMilestones": [],
        "shipEvents": [],
    }
    ship_specs = load_json(root / "world" / "asteria" / "SPECS.json")

    character = character_doc.get("character") or {}
    by_location = location_index(locations)
    current_location_id = (state.get("player") or {}).get("locationId")
    current_location = by_location.get(current_location_id)

    safe_locations = [
        {
            "id": row.get("id"),
            "deck": row.get("deck"),
            "section": row.get("section"),
            "name": row.get("name"),
            "type": row.get("type"),
            "department": row.get("department"),
            "access": row.get("access"),
            "source": row.get("source"),
        }
        for row in locations.get("locations", [])
    ]

    edges = [
        {
            "from": edge.get("from"),
            "to": edge.get("to"),
            "type": edge.get("type"),
            "access": edge.get("access"),
            "bidirectional": edge.get("bidirectional", True),
        }
        for edge in locations.get("edges", [])
    ]

    relationship_by_target = {}
    for rel in relationships.get("relationships", []):
        target = rel.get("targetId")
        if target:
            relationship_by_target.setdefault(target, []).append(rel)

    safe_crew = []
    for person in crew_doc.get("materializedCrew", []):
        safe_crew.append({
            "id": person.get("id"),
            "name": person.get("name"),
            "species": person.get("species"),
            "rank": person.get("rank"),
            "department": person.get("department"),
            "billet": person.get("billet"),
            "primaryShift": person.get("primaryShift"),
            "tier": person.get("tier"),
            "status": person.get("status"),
            "relationships": relationship_by_target.get(person.get("id"), []),
        })

    timeline = []
    for event in service.get("events", []):
        timeline.append({
            "kind": "service",
            "id": event.get("id"),
            "year": event.get("year"),
            "stardate": event.get("stardate"),
            "title": event.get("type", "Service"),
            "summary": event.get("summary"),
        })
    for lock in (character.get("discoveryState") or {}).get("locks", []):
        timeline.append({
            "kind": "discovery",
            "id": lock.get("id"),
            "year": lock.get("year"),
            "stardate": lock.get("stardate"),
            "title": "Character discovery",
            "summary": lock.get("note") or json.dumps(lock.get("value"), ensure_ascii=False),
        })

    record_streams = (
        ("duty", records.get("dutyLogs", [])),
        ("science", records.get("scienceFindings", [])),
        ("mission", records.get("missionRecords", [])),
        ("relationship", records.get("relationshipMilestones", [])),
        ("ship", records.get("shipEvents", [])),
    )
    for kind, rows in record_streams:
        for row in rows:
            timeline.append({
                "kind": kind,
                "id": row.get("id"),
                "year": row.get("year"),
                "stardate": row.get("stardate", row.get("startStardate")),
                "title": row.get("title"),
                "summary": row.get("summary"),
            })
    timeline.sort(key=lambda row: (
        row.get("year") if isinstance(row.get("year"), int) else 9999,
        row.get("stardate") if isinstance(row.get("stardate"), (int, float)) else 999999.0,
        str(row.get("id", "")),
    ))

    next_events = sorted(
        calendar.get("events", []),
        key=lambda event: (
            event.get("stardate", 999999.0),
            event.get("shipTime", "99:99"),
        ),
    )

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "campaignRevision": state.get("revision"),
            "checkpointId": (state.get("checkpoint") or {}).get("lastCheckpointId"),
            "rulesVersion": state.get("rulesVersion"),
        },
        "now": {
            "year": (state.get("currentTime") or {}).get("year"),
            "stardate": (state.get("currentTime") or {}).get("stardate"),
            "shipTime": (state.get("currentTime") or {}).get("shipTime"),
            "campaignStatus": state.get("status"),
            "locationId": current_location_id,
            "location": current_location,
            "shipLocation": (state.get("ship") or {}).get("location"),
            "alertCondition": (state.get("ship") or {}).get("alertCondition"),
            "activeThreadIds": state.get("activeThreadIds", []),
        },
        "character": {
            "id": character.get("id"),
            "name": character.get("name"),
            "species": character.get("species"),
            "age": character.get("age"),
            "pronouns": character.get("pronouns"),
            "rank": character.get("rank"),
            "department": character.get("department"),
            "billet": character.get("billet"),
            "primaryShift": character.get("primaryShift"),
            "upbringing": character.get("homeworld"),
            "quartersId": character.get("quartersId"),
            "health": character.get("health", {}),
            "attributes": character.get("attributes", {}),
            "skills": character.get("skills", {}),
            "primarySpecialty": character.get("primarySpecialty"),
            "secondarySpecialty": character.get("secondarySpecialty"),
            "discoveryState": character.get("discoveryState", {}),
        },
        "ship": ship_doc.get("ship", {}),
        "shipProfile": {
            "lengthMeters": ((ship_specs.get("referenceFacts") or {}).get("lengthMeters") or {}).get("value"),
            "maximumWarp": ((ship_specs.get("referenceFacts") or {}).get("maximumWarp") or {}).get("value"),
            "deckCount": ((ship_specs.get("referenceFacts") or {}).get("deckCount") or {}).get("value"),
            "missionPod": (ship_specs.get("trekMudSettingFill") or {}).get("missionPod"),
            "missionProfile": (ship_specs.get("trekMudSettingFill") or {}).get("missionProfile"),
            "podLevels": (ship_specs.get("trekMudSettingFill") or {}).get("podLevels"),
        },
        "crew": {
            "materialized": safe_crew,
            "materializedCount": len(safe_crew),
            "backgroundCount": (crew_doc.get("backgroundPopulation") or {}).get("count", 0),
            "nominalComplement": crew_doc.get("nominalCrewComplement"),
            "playerIncludedInComplement": bool(crew_doc.get("playerIncludedInComplement")),
        },
        "relationships": relationships.get("relationships", []),
        "knowledge": knowledge.get("facts", []),
        "threads": threads.get("threads", []),
        "calendar": {
            "current": calendar.get("current", {}),
            "events": next_events,
        },
        "serviceRecord": service.get("events", []),
        "records": {
            "dutyLogs": records.get("dutyLogs", []),
            "scienceFindings": records.get("scienceFindings", []),
            "missionRecords": records.get("missionRecords", []),
            "relationshipMilestones": records.get("relationshipMilestones", []),
            "shipEvents": records.get("shipEvents", []),
        },
        "timeline": timeline,
        "inventory": inventory.get("items", []),
        "qualifications": qualifications.get("records", []),
        "map": {
            "shipId": locations.get("shipId"),
            "locations": safe_locations,
            "edges": edges,
            **build_map_layout(safe_locations, edges, current_location_id),
        },
        "rng": {
            "algorithm": rng.get("algorithm"),
            "status": rng.get("status"),
            "counter": rng.get("counter"),
            # Intentionally omit publicCommitment from the player console; it
            # adds no play value and avoids encouraging seed/audit speculation.
        },
    }
    return payload


def build(output: Path) -> dict[str, Any]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "data").mkdir(parents=True, exist_ok=True)

    for filename in ("index.html", "base.css", "components.css", "core.js", "views.js", "map.js", "manifest.webmanifest"):
        src = UI_ROOT / filename
        if not src.exists():
            raise FileNotFoundError(f"missing UI asset: {src}")
        shutil.copy2(src, output / filename)

    payload = player_safe_snapshot(ROOT)
    (output / "data" / "player-console.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output / "data" / "build.json").write_text(
        json.dumps({
            "generatedAt": payload["generatedAt"],
            "checkpointId": payload["source"]["checkpointId"],
            "campaignRevision": payload["source"]["campaignRevision"],
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload = build(args.output.resolve())
    print(json.dumps({
        "built": True,
        "output": str(args.output.resolve()),
        "checkpointId": payload["source"]["checkpointId"],
        "campaignRevision": payload["source"]["campaignRevision"],
        "locations": len(payload["map"]["locations"]),
        "crew": payload["crew"]["materializedCount"],
        "threads": len(payload["threads"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
