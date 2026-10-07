#!/usr/bin/env python3
"""Build and validate TrekMUD's player-facing console artifact."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from build_player_console import build

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ASSETS = {
    "index.html",
    "base.css",
    "components.css",
    "core.js",
    "views.js",
    "map.js",
    "manifest.webmanifest",
    ".nojekyll",
    "data/player-console.json",
    "data/build.json",
}
FORBIDDEN_TOKENS = {
    "secretSeedHex",
    "TrekMUD-GM",
    "npc-private",
    "relationships-private",
    "mysteries.json",
    "plot-clocks",
    "future-events",
}


def accessible_path(payload: dict, start: str, target: str) -> list[str]:
    by_id = {row["id"]: row for row in payload["map"]["locations"]}
    assert start in by_id and target in by_id
    assert by_id[start].get("access") != "restricted"
    assert by_id[target].get("access") != "restricted"

    adjacency: dict[str, list[str]] = {}
    for edge in payload["map"]["edges"]:
        if edge.get("access") == "restricted":
            continue
        a, b = edge["from"], edge["to"]
        if by_id[a].get("access") == "restricted" or by_id[b].get("access") == "restricted":
            continue
        adjacency.setdefault(a, []).append(b)
        if edge.get("bidirectional", True):
            adjacency.setdefault(b, []).append(a)

    queue = [start]
    previous: dict[str, str | None] = {start: None}
    for current in queue:
        for nxt in adjacency.get(current, []):
            if nxt in previous:
                continue
            previous[nxt] = current
            if nxt == target:
                path = [nxt]
                while previous[path[-1]] is not None:
                    path.append(previous[path[-1]])
                return list(reversed(path))
            queue.append(nxt)
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", type=Path)
    args = parser.parse_args()

    if args.keep:
        output = args.keep.resolve()
        output.mkdir(parents=True, exist_ok=True)
        payload = build(output)
    else:
        tmp = tempfile.TemporaryDirectory()
        output = Path(tmp.name)
        payload = build(output)

    missing = sorted(
        asset for asset in REQUIRED_ASSETS if not (output / asset).exists()
    )
    if missing:
        raise SystemExit(f"missing console assets: {missing}")

    state = json.loads((ROOT / "campaign/state.json").read_text(encoding="utf-8"))
    character_doc = json.loads(
        (ROOT / "campaign/character.json").read_text(encoding="utf-8")
    )
    records_doc = json.loads(
        (ROOT / "campaign/records.json").read_text(encoding="utf-8")
    )
    rng_doc = json.loads(
        (ROOT / "campaign/rng.json").read_text(encoding="utf-8")
    )
    public_json = (output / "data/player-console.json").read_text(encoding="utf-8")

    assert payload["source"]["campaignRevision"] == state["revision"]
    assert payload["source"]["checkpointId"] == state["checkpoint"]["lastCheckpointId"]
    assert payload["source"]["rulesVersion"] == state["rulesVersion"]
    assert payload["character"]["id"] == character_doc["character"]["id"]
    assert payload["now"]["locationId"] == state["player"]["locationId"]
    assert payload["now"]["shipTime"] == state["currentTime"]["shipTime"]
    assert payload["now"]["stardate"] == state["currentTime"]["stardate"]
    assert payload["ship"]["id"] == "USS-ASTERIA"
    assert payload["ship"]["name"] == "USS Asteria"
    assert payload["ship"]["class"] == "Nebula-class"
    assert payload["shipProfile"]["lengthMeters"] == 442.23
    assert payload["shipProfile"]["maximumWarp"] == 9.5
    assert payload["shipProfile"]["deckCount"] == 28
    assert payload["shipProfile"]["podLevels"] == 4
    assert "sensor/science pod" in payload["shipProfile"]["missionPod"].lower()
    assert payload["crew"]["materializedCount"] == 20
    assert payload["crew"]["nominalComplement"] == 750
    assert payload["crew"]["backgroundCount"] == 729
    assert payload["crew"]["playerIncludedInComplement"] is True
    assert len(payload["map"]["locations"]) == 200
    assert len(payload["map"]["edges"]) == 206
    assert len(payload["map"]["deckNumbers"]) == 28
    assert payload["map"]["podLevels"] == ["P1", "P2", "P3", "P4"]
    assert payload["character"]["quartersId"] == "AST-D07-S12-0712C"
    assert payload["map"]["shipSilhouette"] == "nebula"
    assert set(payload["map"]["deckPlans"]) == {str(i) for i in range(1, 29)}
    assert set(payload["map"]["podPlans"]) == {"P1", "P2", "P3", "P4"}

    # Standard-access PADD routes used by the console must remain traversable
    # without crossing restricted rooms or restricted graph edges.
    start = "AST-D09-TR-02"
    for destination in (
        "AST-D07-S12-0712C",
        "AST-D04-SCI-OFFICE",
        "AST-D06-SICKBAY",
        "AST-D12-MESS",
    ):
        path = accessible_path(payload, start, destination)
        assert path and path[0] == start and path[-1] == destination

    # Organic character state must remain visibly unresolved instead of being
    # silently converted to zeroes by the presentation layer.

    # The browser artifact is deliberately player-safe. It must never reveal
    # private-repository names, RNG secrets, hidden relationship state, or GM
    # storage file names.
    for token in FORBIDDEN_TOKENS:
        assert token not in public_json, f"forbidden player-console token: {token}"

    # Public commitment is useful for audits but has no gameplay value in the
    # console; keeping it out also prevents accidental coupling to GM storage.
    assert "publicCommitment" not in public_json
    assert payload["rng"]["counter"] == rng_doc["counter"]
    assert payload["character"]["attributes"] == character_doc["character"]["attributes"]
    assert payload["character"]["skills"] == character_doc["character"]["skills"]
    assert payload["character"]["discoveryState"] == character_doc["character"]["discoveryState"]
    assert payload["records"]["dutyLogs"] == records_doc["dutyLogs"]
    assert payload["records"]["scienceFindings"] == records_doc["scienceFindings"]
    assert payload["records"]["missionRecords"] == records_doc["missionRecords"]
    assert payload["records"]["relationshipMilestones"] == records_doc["relationshipMilestones"]
    assert payload["records"]["shipEvents"] == records_doc["shipEvents"]

    index_html = (output / "index.html").read_text(encoding="utf-8")
    assert 'data-view="ship"' in index_html
    assert 'data-view="records"' in index_html
    assert "USS Asteria" in index_html
    assert 'rel="manifest"' in index_html
    manifest = json.loads((output / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["short_name"] == "Asteria PADD"
    assert manifest["display"] == "standalone"

    print(json.dumps({
        "valid": True,
        "checkpointId": payload["source"]["checkpointId"],
        "campaignRevision": payload["source"]["campaignRevision"],
        "locations": len(payload["map"]["locations"]),
        "edges": len(payload["map"]["edges"]),
        "crew": payload["crew"]["materializedCount"],
        "nominalComplement": payload["crew"]["nominalComplement"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
