#!/usr/bin/env python3
"""Apply one or more organic character discoveries as one campaign revision.

This tool does not create the checkpoint itself. It advances all revisioned
campaign components coherently, records the discoveries, validates the state,
and leaves the normal checkpoint tool to freeze the new revision.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from create_character import ATTRIBUTES, SKILLS
from validate_campaign import validate

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class DiscoveryError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiscoveryError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def next_lock_id(locks: list[Any]) -> str:
    numbers = []
    for row in locks:
        if isinstance(row, dict):
            value = row.get("id")
            if isinstance(value, str) and value.startswith("DISC-"):
                try:
                    numbers.append(int(value.split("-", 1)[1]))
                except ValueError:
                    pass
    return f"DISC-{(max(numbers, default=0) + 1):05d}"


def record_lock(
    character: dict[str, Any],
    event_type: str,
    value: Any,
    source: str,
    note: str | None,
    year: int,
    stardate: float,
    revision: int,
) -> str:
    discovery = character["discoveryState"]
    lock_id = next_lock_id(discovery["locks"])
    discovery["locks"].append({
        "id": lock_id,
        "type": event_type,
        "value": value,
        "source": source,
        "note": note,
        "revision": revision,
        "year": year,
        "stardate": stardate,
    })
    return lock_id


def normalize_source(event: dict[str, Any]) -> str:
    source = event.get("source", "PLAYER_DECLARATION")
    require(
        source in {
            "PLAYER_DECLARATION",
            "REPEATED_PORTRAYAL",
            "MECHANICAL_NECESSITY",
            "CANON_BACKGROUND",
            "AUTO_REMAINDER",
        },
        f"unsupported discovery source: {source}",
    )
    return source


def apply_event(
    character: dict[str, Any],
    event: dict[str, Any],
    revision: int,
    year: int,
    stardate: float,
) -> str:
    require(isinstance(event, dict), "each discovery event must be an object")
    event_type = event.get("type")
    require(isinstance(event_type, str), "discovery event type is required")
    source = normalize_source(event)
    note = event.get("note")
    require(note is None or isinstance(note, str), "discovery note must be text or null")

    discovery = character["discoveryState"]

    if event_type == "attribute":
        name = event.get("attribute")
        value = event.get("value")
        require(name in ATTRIBUTES, f"unknown attribute: {name}")
        require(value in {1, 2}, "attribute discovery value must be 1 or 2")
        require(character["attributes"].get(name) is None, f"attribute already locked: {name}")
        pool = discovery["attributePoolRemaining"]
        require(value in pool, f"attribute value {value} is no longer available")
        character["attributes"][name] = value
        pool.remove(value)
        lock_id = record_lock(
            character, event_type, {"attribute": name, "value": value},
            source, note, year, stardate, revision,
        )

        unresolved = [key for key, current in character["attributes"].items() if current is None]
        if len(unresolved) == 1:
            require(len(pool) == 1, "final attribute resolution pool is inconsistent")
            final_name = unresolved[0]
            final_value = pool.pop()
            character["attributes"][final_name] = final_value
            record_lock(
                character,
                "attribute",
                {"attribute": final_name, "value": final_value},
                "AUTO_REMAINDER",
                "Final unresolved attribute inherited the only remaining legal starting value.",
                year,
                stardate,
                revision,
            )
        return f"{name} locked at {value} ({lock_id})"

    if event_type == "skill":
        name = event.get("skill")
        rank = event.get("rank")
        require(name in SKILLS, f"unknown skill: {name}")
        require(rank in {0, 1}, "organic starting skill discovery rank must be 0 or 1")
        require(character["skills"].get(name) is None, f"skill already locked: {name}")

        if rank == 1:
            remaining = discovery["academyRank1SlotsRemaining"]
            require(remaining > 0, "no Academy rank-1 training slots remain")
            discovery["academyRank1SlotsRemaining"] = remaining - 1
        character["skills"][name] = rank
        lock_id = record_lock(
            character, event_type, {"skill": name, "rank": rank},
            source, note, year, stardate, revision,
        )

        if discovery["academyRank1SlotsRemaining"] == 0:
            for other, current in list(character["skills"].items()):
                if current is None:
                    character["skills"][other] = 0
                    record_lock(
                        character,
                        "skill",
                        {"skill": other, "rank": 0},
                        "AUTO_REMAINDER",
                        "All three Academy rank-1 slots were established; remaining unresolved skills default to rank 0.",
                        year,
                        stardate,
                        revision,
                    )
        return f"{name} locked at rank {rank} ({lock_id})"

    if event_type == "department-specialty":
        name = event.get("name")
        require(isinstance(name, str) and name.strip(), "department specialty name required")
        require(character.get("primarySpecialty") is None, "department specialty already locked")
        require(discovery.get("departmentSpecialtyAvailable") is True,
                "department specialty slot is unavailable")
        primary_skill = next(
            (skill for skill, rank in character["skills"].items() if rank == 2),
            None,
        )
        require(primary_skill is not None, "could not identify primary department skill")
        specialty = {"skill": primary_skill, "name": name.strip()}
        character["primarySpecialty"] = specialty
        discovery["departmentSpecialtyAvailable"] = False
        lock_id = record_lock(
            character, event_type, specialty, source, note, year, stardate, revision,
        )
        return f"department specialty locked as {primary_skill} → {name.strip()} ({lock_id})"

    if event_type == "secondary-specialty":
        skill = event.get("skill")
        name = event.get("name")
        require(skill in SKILLS, f"unknown secondary specialty skill: {skill}")
        require(isinstance(name, str) and name.strip(), "secondary specialty name required")
        require(character.get("secondarySpecialty") is None, "secondary specialty already locked")
        require(discovery.get("secondarySpecialtyAvailable") is True,
                "secondary specialty slot is unavailable")
        require(character["skills"].get(skill) in {1, 2},
                "secondary specialty requires an already established trained/proficient skill")
        specialty = {"skill": skill, "name": name.strip()}
        character["secondarySpecialty"] = specialty
        discovery["secondarySpecialtyAvailable"] = False
        lock_id = record_lock(
            character, event_type, specialty, source, note, year, stardate, revision,
        )
        return f"secondary specialty locked as {skill} → {name.strip()} ({lock_id})"

    narrative_targets = {
        "background-fact": "backgroundFacts",
        "interest": "personalInterests",
        "development-area": "developmentAreas",
        "trait": "traits",
    }
    if event_type in narrative_targets:
        text = event.get("text")
        require(isinstance(text, str) and text.strip(), f"{event_type} text is required")
        target = narrative_targets[event_type]
        normalized = text.strip()
        require(normalized not in discovery[target], f"duplicate {event_type}: {normalized}")
        discovery[target].append(normalized)
        lock_id = record_lock(
            character, event_type, normalized, source, note, year, stardate, revision,
        )
        return f"{event_type} established: {normalized} ({lock_id})"

    raise DiscoveryError(f"unsupported discovery event type: {event_type}")


def apply_discoveries(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    state_path = root / "campaign" / "state.json"
    state = load_json(state_path)
    require(state.get("rulesVersion") == "1.1", "organic discovery requires Rules v1.1")
    require(state.get("status") in {"READY_TO_START", "ACTIVE"},
            "organic discovery requires a created campaign character")

    events = request.get("events")
    require(isinstance(events, list) and events, "events must be a non-empty list")

    components = state["components"]
    docs = {key: load_json(root / rel) for key, rel in components.items()}
    character_doc = docs["character"]
    character = character_doc.get("character")
    require(isinstance(character, dict), "character payload required")
    require(character.get("creationMode") == "ORGANIC_DISCOVERY_V1_1",
            "character is not using organic discovery")
    require(character_doc.get("status") == "CREATED_DISCOVERING",
            "character must be in CREATED_DISCOVERING state")

    old_revision = state["revision"]
    revision = old_revision + 1
    for doc in docs.values():
        doc["revision"] = revision

    year = state["currentTime"]["year"]
    stardate = state["currentTime"]["stardate"]
    summaries = [
        apply_event(character, event, revision, year, stardate)
        for event in events
    ]

    state["revision"] = revision
    state["checkpoint"] = {
        "lastCheckpointId": (state.get("checkpoint") or {}).get("lastCheckpointId"),
        "validated": False,
    }

    chronicle_path = root / "campaign" / "CHRONICLE.md"
    chronicle = chronicle_path.read_text(encoding="utf-8").rstrip()
    chronicle += f"\n\n## Character discovery — revision {revision}\n\n"
    for summary in summaries:
        chronicle += f"- {summary}\n"

    for key, rel in components.items():
        write_json(root / rel, docs[key])
    write_json(state_path, state)
    chronicle_path.write_text(chronicle + "\n", encoding="utf-8")

    result = validate(root)
    require(result["valid"] is True and result["revision"] == revision,
            "post-discovery campaign validation failed")

    return {
        "valid": True,
        "previousRevision": old_revision,
        "revision": revision,
        "rulesVersion": "1.1",
        "discoveries": summaries,
        "checkpointRequired": f"r{revision:05d}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    request = load_json(args.input.resolve())
    result = apply_discoveries(args.root.resolve(), request)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
