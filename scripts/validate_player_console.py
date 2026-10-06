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
    public_json = (output / "data/player-console.json").read_text(encoding="utf-8")

    assert payload["source"]["campaignRevision"] == state["revision"]
    assert payload["source"]["checkpointId"] == state["checkpoint"]["lastCheckpointId"]
    assert payload["source"]["rulesVersion"] == state["rulesVersion"]
    assert payload["character"]["id"] == character_doc["character"]["id"]
    assert payload["now"]["locationId"] == state["player"]["locationId"]
    assert payload["now"]["shipTime"] == state["currentTime"]["shipTime"]
    assert payload["now"]["stardate"] == state["currentTime"]["stardate"]
    assert payload["crew"]["materializedCount"] == 20
    assert payload["crew"]["nominalComplement"] == 500
    assert len(payload["map"]["locations"]) == 131
    assert len(payload["map"]["edges"]) == 138
    assert len(payload["map"]["deckNumbers"]) == 19
    assert len(payload["map"]["profile"]) == 19
    assert payload["map"]["currentDeck"] == 9
    assert set(payload["map"]["deckPlans"]) == {str(i) for i in range(1, 20)}
    assert payload["map"]["deckPlans"]["9"]["label"] == "Transport & Operations"
    assert payload["map"]["deckPlans"]["9"]["compartmentCount"] >= 4

    # Organic character state must remain visibly unresolved instead of being
    # silently converted to zeroes by the presentation layer.
    assert sum(value is None for value in payload["character"]["attributes"].values()) == 5
    assert payload["character"]["skills"]["Science"] == 2
    assert payload["character"]["discoveryState"]["academyRank1SlotsRemaining"] == 3

    # The browser artifact is deliberately player-safe. It must never reveal
    # private-repository names, RNG secrets, hidden relationship state, or GM
    # storage file names.
    for token in FORBIDDEN_TOKENS:
        assert token not in public_json, f"forbidden player-console token: {token}"

    # Public commitment is useful for audits but has no gameplay value in the
    # console; keeping it out also prevents accidental coupling to GM storage.
    assert "publicCommitment" not in public_json
    assert payload["rng"]["counter"] == 0

    print(json.dumps({
        "valid": True,
        "checkpointId": payload["source"]["checkpointId"],
        "campaignRevision": payload["source"]["campaignRevision"],
        "locations": len(payload["map"]["locations"]),
        "edges": len(payload["map"]["edges"]),
        "crew": payload["crew"]["materializedCount"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
