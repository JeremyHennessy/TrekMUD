#!/usr/bin/env python3
"""Initialize structured player-visible career records at revision 4.

This is a zero-time infrastructure migration. It creates empty record streams,
adds the component to campaign state, advances all revisioned components
coherently, and leaves narrative/RNG state unchanged.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_campaign import validate

ROOT = Path(__file__).resolve().parents[1]


class RecordsInitError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RecordsInitError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def initialize(root: Path) -> dict[str, Any]:
    state_path = root / "campaign" / "state.json"
    state = load(state_path)

    require(state.get("revision") == 3, "career-record initialization requires revision 3")
    require((state.get("checkpoint") or {}).get("lastCheckpointId") == "r00003",
            "career-record initialization requires checkpoint r00003")
    require((state.get("checkpoint") or {}).get("validated") is True,
            "r00003 must be validated")
    require(state.get("status") == "READY_TO_START",
            "career-record initialization is intended before Scene One")

    current_time = dict(state.get("currentTime") or {})
    player_location = (state.get("player") or {}).get("locationId")

    components = dict(state.get("components") or {})
    require("records" not in components, "records component already exists")

    docs: dict[str, dict[str, Any]] = {}
    for key, rel in components.items():
        doc = load(root / rel)
        require(doc.get("revision") == 3, f"{rel} must be at revision 3")
        docs[key] = doc

    rng_counter = docs["rng"].get("counter")
    require(rng_counter == 0, "pre-play records initialization must not follow RNG use")

    revision = 4
    for doc in docs.values():
        doc["revision"] = revision

    records = {
        "schemaVersion": 1,
        "revision": revision,
        "characterId": (state.get("player") or {}).get("characterId"),
        "dutyLogs": [],
        "scienceFindings": [],
        "missionRecords": [],
        "relationshipMilestones": [],
        "shipEvents": [],
        "note": (
            "Player-visible structured records. Streams begin empty because Scene One "
            "has not started; future entries are created only by observed/established play."
        ),
    }

    components["records"] = "campaign/records.json"
    state["components"] = components
    state["revision"] = revision
    state["checkpoint"] = {"lastCheckpointId": "r00003", "validated": False}

    config_path = root / "campaign" / "config.json"
    config = load(config_path)
    config["recordStreamsVersion"] = 1

    chronicle_path = root / "campaign" / "CHRONICLE.md"
    chronicle = chronicle_path.read_text(encoding="utf-8").rstrip()
    chronicle += (
        "\n\n## Player-visible records infrastructure — revision 4\n\n"
        "- Added structured Duty Log, Science Findings, Mission Records, Relationship Milestones, and Ship Events streams.\n"
        "- All streams begin empty because Scene One has not started.\n"
        "- This is an infrastructure-only revision: ship time, stardate, player location, character state, and RNG counter are unchanged.\n"
    )

    for key, rel in components.items():
        if key == "records":
            continue
        write(root / rel, docs[key])
    write(root / "campaign" / "records.json", records)
    write(state_path, state)
    write(config_path, config)
    chronicle_path.write_text(chronicle + "\n", encoding="utf-8")

    require(state["currentTime"] == current_time, "records migration changed campaign time")
    require(state["player"]["locationId"] == player_location,
            "records migration changed player location")
    require(docs["rng"]["counter"] == rng_counter, "records migration changed RNG counter")

    result = validate(root)
    require(result["valid"] is True and result["revision"] == revision,
            "post-migration campaign validation failed")

    return {
        "valid": True,
        "revision": revision,
        "checkpointRequired": "r00004",
        "streams": 5,
        "records": 0,
        "shipTime": state["currentTime"]["shipTime"],
        "stardate": state["currentTime"]["stardate"],
        "playerLocation": state["player"]["locationId"],
        "rngCounter": docs["rng"]["counter"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(initialize(args.root.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
