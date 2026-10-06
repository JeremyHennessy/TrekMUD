#!/usr/bin/env python3
"""Append player-visible career records as one coherent campaign revision.

This tool records only facts already established in play. It never invents
hidden GM state and never advances in-universe time by itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_campaign import validate

ROOT = Path(__file__).resolve().parents[1]

STREAMS = {
    "duty": ("dutyLogs", "DUTY-"),
    "science": ("scienceFindings", "SCI-"),
    "mission": ("missionRecords", "MIS-"),
    "relationship": ("relationshipMilestones", "RELM-"),
    "ship": ("shipEvents", "SHIPLOG-"),
}


class RecordError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RecordError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain an object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def next_id(rows: list[dict[str, Any]], prefix: str) -> str:
    numbers: list[int] = []
    for row in rows:
        value = row.get("id")
        if isinstance(value, str) and value.startswith(prefix):
            try:
                numbers.append(int(value[len(prefix):]))
            except ValueError:
                pass
    return f"{prefix}{max(numbers, default=0) + 1:05d}"


def text_field(event: dict[str, Any], key: str) -> str:
    value = event.get(key)
    require(isinstance(value, str) and value.strip(), f"{key} is required")
    return value.strip()


def apply(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    state_path = root / "campaign" / "state.json"
    state = load(state_path)
    require(state.get("status") in {"READY_TO_START", "ACTIVE"},
            "player records require a created campaign")
    require(state.get("revision", 0) >= 4,
            "player records require the records component initialized")

    events = request.get("events")
    require(isinstance(events, list) and events, "events must be a non-empty list")

    components = state.get("components") or {}
    require("records" in components, "state has no records component")

    docs = {key: load(root / rel) for key, rel in components.items()}
    old_revision = state["revision"]
    for key, doc in docs.items():
        require(doc.get("revision") == old_revision,
                f"component {key} revision mismatch before record append")

    records = docs["records"]
    character = (docs["character"].get("character") or {})
    crew_ids = {row["id"] for row in docs["crew"].get("materializedCrew", [])}
    relationship_ids = {
        row["id"] for row in docs["relationships"].get("relationships", [])
    }
    current = state.get("currentTime") or {}

    added: list[dict[str, str]] = []

    for event in events:
        require(isinstance(event, dict), "each event must be an object")
        event_type = event.get("type")
        require(event_type in STREAMS, f"unsupported record type: {event_type}")
        stream_name, prefix = STREAMS[event_type]
        rows = records[stream_name]

        row: dict[str, Any] = {
            "id": next_id(rows, prefix),
            "year": event.get("year", current.get("year")),
            "title": text_field(event, "title"),
            "summary": text_field(event, "summary"),
            "source": "PLAYER_VISIBLE_CAMPAIGN",
        }

        if event_type in {"duty", "science", "relationship", "ship"}:
            row["stardate"] = event.get("stardate", current.get("stardate"))

        if event_type in {"duty", "ship"}:
            row["shipTime"] = event.get("shipTime", current.get("shipTime"))

        if event_type == "duty":
            row["department"] = event.get("department", character.get("department"))
            row["status"] = event.get("status", "LOGGED")
            if event.get("locationId") is not None:
                row["locationId"] = event["locationId"]

        elif event_type == "science":
            row["domain"] = event.get("domain", "General Science")
            row["status"] = event.get("status", "OBSERVATION")
            if event.get("confidence") is not None:
                row["confidence"] = event["confidence"]
            if event.get("locationId") is not None:
                row["locationId"] = event["locationId"]

        elif event_type == "mission":
            row["startStardate"] = event.get("startStardate", current.get("stardate"))
            row["endStardate"] = event.get("endStardate")
            row["role"] = event.get("role", character.get("billet"))
            row["status"] = event.get("status", "ACTIVE")
            row["outcome"] = event.get("outcome")
            if event.get("sourceThreadId") is not None:
                row["sourceThreadId"] = event["sourceThreadId"]

        elif event_type == "relationship":
            target_id = event.get("targetId")
            require(target_id in crew_ids,
                    f"relationship milestone targetId is not a materialized crew member: {target_id}")
            row["targetId"] = target_id
            relationship_id = event.get("relationshipId")
            require(relationship_id is None or relationship_id in relationship_ids,
                    f"unknown relationshipId: {relationship_id}")
            if relationship_id is not None:
                row["relationshipId"] = relationship_id
            if event.get("tone") is not None:
                row["tone"] = event["tone"]

        elif event_type == "ship":
            row["shipId"] = event.get("shipId", (state.get("ship") or {}).get("id"))
            row["system"] = event.get("system", "General")
            row["severity"] = event.get("severity", "INFO")
            row["status"] = event.get("status", "LOGGED")

        rows.append(row)
        added.append({"type": event_type, "id": row["id"], "title": row["title"]})

    revision = old_revision + 1
    for doc in docs.values():
        doc["revision"] = revision

    state["revision"] = revision
    state["checkpoint"] = {
        "lastCheckpointId": (state.get("checkpoint") or {}).get("lastCheckpointId"),
        "validated": False,
    }

    chronicle_path = root / "campaign" / "CHRONICLE.md"
    chronicle = chronicle_path.read_text(encoding="utf-8").rstrip()
    chronicle += f"\n\n## Player-visible records — revision {revision}\n\n"
    for row in added:
        chronicle += f"- {row['id']} · {row['title']} ({row['type']}).\n"

    for key, rel in components.items():
        write(root / rel, docs[key])
    write(state_path, state)
    chronicle_path.write_text(chronicle + "\n", encoding="utf-8")

    result = validate(root)
    require(result["valid"] is True and result["revision"] == revision,
            "post-record campaign validation failed")

    return {
        "valid": True,
        "previousRevision": old_revision,
        "revision": revision,
        "added": added,
        "checkpointRequired": f"r{revision:05d}",
        "shipTime": state["currentTime"]["shipTime"],
        "stardate": state["currentTime"]["stardate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    request = load(args.input.resolve())
    print(json.dumps(apply(args.root.resolve(), request), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
