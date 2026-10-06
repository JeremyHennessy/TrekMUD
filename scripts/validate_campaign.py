#!/usr/bin/env python3
"""Validate TrekMUD's player-visible campaign state as one coherent snapshot."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "campaign" / "state.json"


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_json(relative_path: str | Path) -> dict[str, Any]:
    path = ROOT / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing file: {relative_path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {relative_path}: {exc}")
    require(isinstance(value, dict), f"{relative_path} must contain a JSON object")
    return value


def unique_ids(rows: list[Any], field: str, label: str) -> set[str]:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"{label}[{index}] must be an object")
        value = row.get(field)
        require(isinstance(value, str) and value, f"{label}[{index}].{field} is required")
        require(value not in seen, f"duplicate {label} id: {value}")
        seen.add(value)
    return seen


def main() -> int:
    try:
        state = load_json("campaign/state.json")
        require(state.get("schemaVersion") == 1, "state schemaVersion must be 1")
        revision = state.get("revision")
        require(isinstance(revision, int) and revision >= 0, "state revision must be a non-negative integer")

        components = state.get("components")
        require(isinstance(components, dict) and components, "state.components is required")

        required_components = {
            "character", "serviceRecord", "qualifications", "inventory",
            "crew", "relationships", "knowledge", "activeThreads",
            "calendar", "ship", "locations", "rng",
        }
        require(set(components) == required_components, "state.components does not match the required component set")

        loaded: dict[str, dict[str, Any]] = {}
        for name, relative_path in components.items():
            require(isinstance(relative_path, str) and relative_path.startswith("campaign/"),
                    f"component {name} must point inside campaign/")
            component = load_json(relative_path)
            require(component.get("schemaVersion") == 1, f"{relative_path} schemaVersion must be 1")
            require(component.get("revision") == revision,
                    f"{relative_path} revision {component.get('revision')} != root revision {revision}")
            loaded[name] = component

        character = loaded["character"]
        service = loaded["serviceRecord"]
        quals = loaded["qualifications"]
        inventory = loaded["inventory"]
        crew = loaded["crew"]
        relationships = loaded["relationships"]
        knowledge = loaded["knowledge"]
        threads = loaded["activeThreads"]
        calendar = loaded["calendar"]
        ship_doc = loaded["ship"]
        locations = loaded["locations"]
        rng = loaded["rng"]

        # Pre-campaign consistency.
        player = state.get("player")
        require(isinstance(player, dict), "state.player is required")
        character_id = player.get("characterId")
        if state.get("status") == "NOT_STARTED":
            require(character.get("status") == "UNCREATED", "NOT_STARTED requires character.status=UNCREATED")
            require(character.get("character") is None, "NOT_STARTED requires no character payload")
            require(character_id is None, "NOT_STARTED requires state.player.characterId=null")

        # Character references must agree once a character exists.
        if character_id is None:
            require(service.get("characterId") is None, "service record characterId must be null before character creation")
            require(quals.get("characterId") is None, "qualifications characterId must be null before character creation")
            require(inventory.get("characterId") is None, "inventory characterId must be null before character creation")
            require(relationships.get("characterId") is None, "relationships characterId must be null before character creation")
            require(knowledge.get("characterId") is None, "knowledge characterId must be null before character creation")
        else:
            payload = character.get("character")
            require(isinstance(payload, dict), "created character requires character payload")
            require(payload.get("id") == character_id, "character payload id must equal state.player.characterId")
            for label, doc in (
                ("service record", service),
                ("qualifications", quals),
                ("inventory", inventory),
                ("relationships", relationships),
                ("knowledge", knowledge),
            ):
                require(doc.get("characterId") == character_id, f"{label} characterId mismatch")

        # Time is single-source consistent.
        require(calendar.get("current") == state.get("currentTime"),
                "calendar.current must exactly match state.currentTime")

        # Ship summary must agree with ship component.
        ship = ship_doc.get("ship")
        require(isinstance(ship, dict), "campaign/ship.json must contain ship object")
        summary = state.get("ship")
        require(isinstance(summary, dict), "state.ship is required")
        for key in ("id", "name", "class", "location", "mission", "alertCondition"):
            require(summary.get(key) == ship.get(key), f"ship summary mismatch for {key}")

        ship_id = ship.get("id")
        require(crew.get("shipId") == ship_id, "crew.shipId mismatch")
        require(locations.get("shipId") == ship_id, "locations.shipId mismatch")

        # Crew population and persistent identities.
        materialized = crew.get("materializedCrew")
        require(isinstance(materialized, list), "crew.materializedCrew must be a list")
        crew_ids = unique_ids(materialized, "id", "materializedCrew")
        nominal = crew.get("nominalCrewComplement")
        background = crew.get("backgroundPopulation")
        require(isinstance(nominal, int) and nominal >= 0, "nominalCrewComplement must be non-negative")
        require(isinstance(background, dict), "backgroundPopulation must be an object")
        background_count = background.get("count")
        require(isinstance(background_count, int) and background_count >= 0,
                "backgroundPopulation.count must be non-negative")
        require(background_count + len(materialized) == nominal,
                "background count + materialized crew must equal nominal crew complement")

        # Location topology.
        location_rows = locations.get("locations")
        edge_rows = locations.get("edges")
        require(isinstance(location_rows, list), "locations.locations must be a list")
        require(isinstance(edge_rows, list), "locations.edges must be a list")
        location_ids = unique_ids(location_rows, "id", "locations")
        for index, edge in enumerate(edge_rows):
            require(isinstance(edge, dict), f"edges[{index}] must be an object")
            a, b = edge.get("from"), edge.get("to")
            require(a in location_ids, f"edge {index} has unknown from location: {a}")
            require(b in location_ids, f"edge {index} has unknown to location: {b}")
        player_location = player.get("locationId")
        require(player_location is None or player_location in location_ids,
                "state.player.locationId must resolve when non-null")

        # Stable IDs in revisioned collections.
        service_ids = unique_ids(service.get("events", []), "id", "service events")
        qual_ids = unique_ids(quals.get("records", []), "id", "qualifications")
        item_ids = unique_ids(inventory.get("items", []), "id", "inventory items")
        relationship_ids = unique_ids(relationships.get("relationships", []), "id", "relationships")
        knowledge_ids = unique_ids(knowledge.get("facts", []), "id", "knowledge facts")
        thread_ids = unique_ids(threads.get("threads", []), "id", "threads")
        calendar_ids = unique_ids(calendar.get("events", []), "id", "calendar events")
        _ = (service_ids, qual_ids, item_ids, relationship_ids, knowledge_ids, calendar_ids)

        active_ids = state.get("activeThreadIds")
        require(isinstance(active_ids, list), "state.activeThreadIds must be a list")
        require(len(active_ids) == len(set(active_ids)), "state.activeThreadIds contains duplicates")
        require(set(active_ids) == thread_ids,
                "state.activeThreadIds must exactly match campaign/active-threads.json thread IDs")

        # Relationship references can only point at the player or materialized crew.
        known_people = set(crew_ids)
        if character_id is not None:
            known_people.add(character_id)
        for rel in relationships.get("relationships", []):
            for key in ("subjectId", "targetId"):
                value = rel.get(key)
                require(value in known_people, f"relationship {rel.get('id')} has unresolved {key}: {value}")

        # RNG can be uninitialized before play, but its counter can never go backward below zero.
        require(rng.get("algorithm") == "SHA256_COUNTER_V1", "unsupported RNG algorithm")
        counter = rng.get("counter")
        require(isinstance(counter, int) and counter >= 0, "rng.counter must be a non-negative integer")
        if state.get("status") == "NOT_STARTED":
            require(rng.get("status") == "UNINITIALIZED", "pre-campaign RNG must remain UNINITIALIZED")

        # Root campaign configuration must agree on the start identity.
        config = load_json("campaign/config.json")
        start = config.get("start") or {}
        require(start.get("ship") == ship.get("name"), "config start ship mismatch")
        require(start.get("shipClass") == ship.get("class"), "config ship class mismatch")

        print(json.dumps({
            "valid": True,
            "revision": revision,
            "status": state.get("status"),
            "materializedCrew": len(materialized),
            "locations": len(location_ids),
            "threads": len(thread_ids),
            "rngCounter": counter,
        }, indent=2))
        return 0
    except ValidationError as exc:
        print(f"INVALID CAMPAIGN STATE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
