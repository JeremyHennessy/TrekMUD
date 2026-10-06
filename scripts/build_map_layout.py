#!/usr/bin/env python3
"""Presentation-only layout helpers for the TrekMUD player console.

Canonical geography remains campaign/locations.json. This module turns that
graph into deterministic ship/deck schematics without changing location IDs,
connections, or gameplay topology.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

DECK_LABELS = {
    1: "Command",
    2: "Command Support",
    3: "Officers & Diplomatic",
    4: "Science",
    5: "Medical",
    6: "Recreation",
    7: "Junior Officers",
    8: "Security",
    9: "Transport & Operations",
    10: "Forward Flight Ops",
    11: "Main Flight Deck",
    12: "Shuttle & Cargo",
    13: "Damage Control",
    14: "Engineering Upper",
    15: "Main Engineering",
    16: "Engineering Lower",
    17: "Deflector & Tactical",
    18: "Environmental",
    19: "Lower Systems",
}

# Broadest amidships, tapered toward command and lower engineering decks.
DECK_WIDTHS = {
    1: 44, 2: 55, 3: 66, 4: 76, 5: 84,
    6: 91, 7: 96, 8: 100, 9: 100, 10: 98,
    11: 96, 12: 92, 13: 87, 14: 80, 15: 74,
    16: 68, 17: 61, 18: 53, 19: 45,
}

TYPE_PRIORITY = {
    "bridge": 0,
    "office": 1,
    "conference": 2,
    "lab": 3,
    "medical": 4,
    "security": 5,
    "operations": 6,
    "computer": 7,
    "transporter": 8,
    "flight-control": 9,
    "hangar": 10,
    "engineering": 11,
    "cargo": 12,
    "quarters": 13,
    "lounge": 14,
    "mess": 15,
    "holodeck": 16,
    "recreation": 17,
    "training": 18,
    "equipment": 19,
    "service": 20,
    "safety": 21,
    "airlock": 22,
}

DEPARTMENT_ORDER = {
    "command": 0,
    "science": 1,
    "medical": 2,
    "operations": 3,
    "engineering": 4,
    "security": 5,
    "tactical": 6,
    "flight": 7,
    "counseling": 8,
    "personnel": 9,
    "shipwide": 10,
}


def _room_sort(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        TYPE_PRIORITY.get(str(row.get("type")), 50),
        DEPARTMENT_ORDER.get(str(row.get("department")), 50),
        str(row.get("name", "")),
        str(row.get("id", "")),
    )


def _rows_for_count(count: int) -> list[int]:
    """Distribute room count into visually balanced rows of max 4."""
    if count <= 4:
        return [count]
    if count <= 8:
        top = math.ceil(count / 2)
        return [top, count - top]
    # Three rows: keep the center row smaller around the central spine.
    top = min(4, math.ceil(count / 3))
    bottom = min(4, math.ceil((count - top) / 2))
    middle = count - top - bottom
    return [top, middle, bottom]


def _row_positions(count: int, hull_x: float, hull_w: float, y: float) -> list[dict[str, float]]:
    if count <= 0:
        return []
    pad = max(4.0, hull_w * 0.055)
    usable = hull_w - (pad * 2)
    gap = 2.1
    width = min(19.0, (usable - gap * (count - 1)) / count)
    total = width * count + gap * (count - 1)
    start = 50.0 - total / 2
    return [
        {"x": round(start + i * (width + gap), 2), "y": y, "w": round(width, 2), "h": 12.5}
        for i in range(count)
    ]


def _middle_side_positions(count: int, hull_x: float, hull_w: float) -> list[dict[str, float]]:
    if count <= 0:
        return []
    positions: list[dict[str, float]] = []
    left = 50.0 - min(31.0, hull_w * 0.32)
    right = 50.0 + min(31.0, hull_w * 0.32)
    for i in range(count):
        side_x = left if i % 2 == 0 else right
        level = i // 2
        positions.append({
            "x": round(side_x - 8.5, 2),
            "y": round(42.5 + level * 14.0, 2),
            "w": 17.0,
            "h": 11.5,
        })
    return positions


def deck_plan(deck: int, rows: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    width = float(DECK_WIDTHS.get(deck, 80))
    hull_x = round(50.0 - width / 2, 2)

    turbolifts = [r for r in rows if str(r.get("id", "")).endswith("-TL-C")]
    hubs = [r for r in rows if str(r.get("id", "")).endswith("-HUB-C")]
    corridors = [
        r for r in rows
        if r.get("type") == "corridor"
        and r not in hubs
        and r not in turbolifts
    ]
    rooms = sorted(
        [r for r in rows if r not in turbolifts and r not in hubs and r not in corridors],
        key=_room_sort,
    )

    compartment_positions: list[dict[str, float]] = []
    row_counts = _rows_for_count(len(rooms))
    if len(row_counts) == 1:
        compartment_positions.extend(_row_positions(row_counts[0], hull_x, width, 31.0))
    elif len(row_counts) == 2:
        compartment_positions.extend(_row_positions(row_counts[0], hull_x, width, 22.0))
        compartment_positions.extend(_row_positions(row_counts[1], hull_x, width, 68.0))
    else:
        compartment_positions.extend(_row_positions(row_counts[0], hull_x, width, 18.0))
        compartment_positions.extend(_middle_side_positions(row_counts[1], hull_x, width))
        compartment_positions.extend(_row_positions(row_counts[2], hull_x, width, 73.0))

    compartments = []
    for room, position in zip(rooms, compartment_positions):
        compartments.append({
            "id": room.get("id"),
            "name": room.get("name"),
            "type": room.get("type"),
            "department": room.get("department"),
            "access": room.get("access"),
            "section": room.get("section"),
            **position,
        })

    # Central circulation is deliberately explicit and consistent on every deck.
    circulation = []
    if turbolifts:
        row = turbolifts[0]
        circulation.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "kind": "turbolift",
            "x": round(hull_x + 4.0, 2),
            "y": 43.5,
            "w": 9.0,
            "h": 13.0,
        })
    if hubs:
        row = hubs[0]
        circulation.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "kind": "hub",
            "x": 44.0,
            "y": 43.0,
            "w": 12.0,
            "h": 14.0,
        })

    for idx, row in enumerate(corridors):
        circulation.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "kind": "corridor",
            "x": round(28.0 + idx * 13.0, 2),
            "y": 46.0,
            "w": 12.0,
            "h": 8.0,
        })

    deck_ids = {r.get("id") for r in rows}
    deck_edges = [
        {
            "from": e.get("from"),
            "to": e.get("to"),
            "type": e.get("type"),
            "access": e.get("access"),
        }
        for e in edges
        if e.get("from") in deck_ids and e.get("to") in deck_ids
    ]

    departments = Counter(str(r.get("department", "shipwide")) for r in rooms)
    primary_department = departments.most_common(1)[0][0] if departments else "shipwide"

    return {
        "deck": deck,
        "label": DECK_LABELS.get(deck, f"Deck {deck}"),
        "hull": {
            "x": hull_x,
            "width": width,
            "noseY": 7.0,
            "tailY": 93.0,
        },
        "primaryDepartment": primary_department,
        "roomCount": len(rows),
        "compartmentCount": len(compartments),
        "compartments": compartments,
        "circulation": circulation,
        "edges": deck_edges,
    }


def build_map_layout(
    locations: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    current_location_id: str | None,
) -> dict[str, Any]:
    numbered = [r for r in locations if isinstance(r.get("deck"), int)]
    decks = sorted({int(r["deck"]) for r in numbered})
    plans = {
        str(deck): deck_plan(
            deck,
            [r for r in numbered if r.get("deck") == deck],
            edges,
        )
        for deck in decks
    }

    current = next((r for r in locations if r.get("id") == current_location_id), None)
    current_deck = current.get("deck") if current else None

    profile = []
    for deck in decks:
        plan = plans[str(deck)]
        profile.append({
            "deck": deck,
            "label": plan["label"],
            "width": DECK_WIDTHS.get(deck, 80),
            "roomCount": plan["roomCount"],
            "primaryDepartment": plan["primaryDepartment"],
            "current": deck == current_deck,
        })

    return {
        "currentDeck": current_deck,
        "profile": profile,
        "deckPlans": plans,
        "deckNumbers": decks,
        "podLevels": sorted({
            str(r.get("section"))
            for r in locations
            if r.get("deck") is None and r.get("section")
        }),
    }
