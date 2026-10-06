#!/usr/bin/env python3
"""Validate the candidate USS Meridian location graph."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "world" / "meridian" / "topology.json"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "topology must be a JSON object")
    return value


def validate(path: Path) -> dict[str, Any]:
    data = load(path)
    require(data.get("schemaVersion") == 1, "schemaVersion must be 1")
    require(data.get("shipId") == "USS-MERIDIAN", "shipId must be USS-MERIDIAN")
    require(data.get("deckCount") == 19, "candidate baseline must have 19 numbered decks")

    locations = data.get("locations")
    edges = data.get("edges")
    require(isinstance(locations, list) and locations, "locations must be a non-empty list")
    require(isinstance(edges, list) and edges, "edges must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    numbered_decks: set[int] = set()
    for index, row in enumerate(locations):
        require(isinstance(row, dict), f"locations[{index}] must be an object")
        loc_id = row.get("id")
        require(isinstance(loc_id, str) and loc_id.startswith("MER-"), f"invalid location id at index {index}")
        require(loc_id not in by_id, f"duplicate location id: {loc_id}")
        by_id[loc_id] = row
        deck = row.get("deck")
        if deck is not None:
            require(isinstance(deck, int) and 1 <= deck <= 19, f"{loc_id} has invalid numbered deck {deck}")
            numbered_decks.add(deck)
        require(row.get("access") in {"crew", "restricted", "assigned"}, f"{loc_id} has invalid access")
        require(row.get("source") in {"SETTING_FILL", "CANON_CONSTRAINED"}, f"{loc_id} has invalid source")

    require(numbered_decks == set(range(1, 20)), "all numbered decks 1–19 must be represented")

    adjacency: dict[str, set[str]] = defaultdict(set)
    edge_keys: set[tuple[str, str, str]] = set()
    for index, row in enumerate(edges):
        require(isinstance(row, dict), f"edges[{index}] must be an object")
        a, b = row.get("from"), row.get("to")
        edge_type = row.get("type")
        require(a in by_id, f"edge {index} unknown from: {a}")
        require(b in by_id, f"edge {index} unknown to: {b}")
        require(a != b, f"edge {index} is a self-loop")
        require(isinstance(edge_type, str) and edge_type, f"edge {index} missing type")
        key = (str(a), str(b), edge_type)
        reverse = (str(b), str(a), edge_type)
        require(key not in edge_keys and reverse not in edge_keys, f"duplicate/reversed edge at index {index}: {a} <-> {b}")
        edge_keys.add(key)
        adjacency[str(a)].add(str(b))
        if row.get("bidirectional", True):
            adjacency[str(b)].add(str(a))

    opening = data.get("playerOpening")
    require(isinstance(opening, dict), "playerOpening is required")
    arrival = opening.get("arrivalLocationId")
    quarters = opening.get("assignedQuartersId")
    require(arrival == "MER-D09-TR-02", "opening arrival must preserve Transporter Room 2")
    require(quarters == "MER-D07-S12-0712C", "opening quarters must preserve 0712-C")
    require(arrival in by_id and quarters in by_id, "opening locations must resolve")
    require(by_id[quarters].get("deck") == 7, "0712-C must be on Deck 7")
    require(str(by_id[quarters].get("section")) == "12", "0712-C must be in Section 12")

    # Every location must be reachable from the opening location through the graph.
    seen = {str(arrival)}
    queue = deque([str(arrival)])
    while queue:
        current = queue.popleft()
        for nxt in adjacency[current]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)

    unreachable = sorted(set(by_id) - seen)
    require(not unreachable, f"unreachable locations from opening: {unreachable[:10]}")

    # One central turbolift and corridor hub per numbered deck.
    for deck in range(1, 20):
        dd = f"{deck:02d}"
        require(f"MER-D{dd}-TL-C" in by_id, f"deck {deck} missing central turbolift")
        require(f"MER-D{dd}-HUB-C" in by_id, f"deck {deck} missing central corridor hub")

    return {
        "valid": True,
        "locations": len(locations),
        "edges": len(edges),
        "numberedDecks": len(numbered_decks),
        "reachableLocations": len(seen),
        "openingArrival": arrival,
        "openingQuarters": quarters,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    try:
        result = validate(args.path.resolve())
        print(json.dumps(result, indent=2))
        return 0
    except (ValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"INVALID MERIDIAN TOPOLOGY: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
