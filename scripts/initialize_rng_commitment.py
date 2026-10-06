#!/usr/bin/env python3
"""Initialize TrekMUD's public deterministic RNG commitment.

The secret seed never enters the public repository. This tool accepts only the
SHA-256 seed commitment, advances all revisioned player-visible state by one
revision, records no narrative time passage, and validates the coherent result.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from validate_campaign import validate

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class RNGInitializationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RNGInitializationError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def initialize(root: Path, commitment: str) -> dict[str, Any]:
    commitment = commitment.strip().lower()
    require(HEX64.fullmatch(commitment) is not None,
            "commitment must be a lowercase 64-character SHA-256 hex digest")

    state_path = root / "campaign" / "state.json"
    state = load_json(state_path)
    require(state.get("revision") == 1, "initial RNG setup requires campaign revision 1")
    require(state.get("status") == "READY_TO_START",
            "initial RNG setup requires READY_TO_START campaign")
    require(state.get("rulesVersion") == "1.1",
            "initial RNG setup requires Rules v1.1")
    require((state.get("checkpoint") or {}).get("lastCheckpointId") == "r00001",
            "initial RNG setup requires validated parent checkpoint r00001")
    require((state.get("checkpoint") or {}).get("validated") is True,
            "parent checkpoint r00001 must be validated")

    components = state.get("components")
    require(isinstance(components, dict) and components, "state.components required")
    docs = {key: load_json(root / rel) for key, rel in components.items()}

    rng = docs["rng"]
    require(rng.get("status") == "UNINITIALIZED", "public RNG is already initialized")
    require(rng.get("publicCommitment") is None, "public RNG commitment already exists")
    require(rng.get("counter") == 0, "initial RNG counter must be 0")
    require(rng.get("algorithm") == "SHA256_COUNTER_V1",
            "unsupported RNG algorithm")

    old_revision = state["revision"]
    revision = old_revision + 1
    for doc in docs.values():
        require(doc.get("revision") == old_revision,
                "all campaign components must match current revision before RNG initialization")
        doc["revision"] = revision

    rng["status"] = "INITIALIZED"
    rng["publicCommitment"] = commitment
    rng["counter"] = 0
    rng["note"] = (
        "Secret seed is stored only in synchronized private TrekMUD-GM state. "
        "This public file contains only its SHA-256 commitment and consumed counter."
    )

    state["revision"] = revision
    state["checkpoint"] = {
        "lastCheckpointId": "r00001",
        "validated": False,
    }

    config_path = root / "campaign" / "config.json"
    config = load_json(config_path)
    config["rng"] = {
        "algorithm": "SHA256_COUNTER_V1",
        "publicCommitment": commitment,
        "privateStore": "JeremyHennessy/TrekMUD-GM",
    }

    chronicle_path = root / "campaign" / "CHRONICLE.md"
    chronicle = chronicle_path.read_text(encoding="utf-8").rstrip()
    chronicle += (
        "\n\n## RNG initialization — revision 2\n\n"
        "- Deterministic SHA256_COUNTER_V1 randomness initialized.\n"
        "- Only the public SHA-256 seed commitment is stored here; the secret seed is in private GM storage.\n"
        "- RNG counter begins at 0.\n"
        "- No in-universe time passed and no narrative event occurred.\n"
    )

    for key, rel in components.items():
        write_json(root / rel, docs[key])
    write_json(state_path, state)
    write_json(config_path, config)
    chronicle_path.write_text(chronicle + "\n", encoding="utf-8")

    result = validate(root)
    require(result["valid"] is True and result["revision"] == revision,
            "post-initialization campaign validation failed")

    return {
        "valid": True,
        "previousRevision": old_revision,
        "revision": revision,
        "rulesVersion": state["rulesVersion"],
        "status": state["status"],
        "algorithm": rng["algorithm"],
        "publicCommitment": commitment,
        "counter": 0,
        "shipTime": state["currentTime"]["shipTime"],
        "stardate": state["currentTime"]["stardate"],
        "checkpointRequired": f"r{revision:05d}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--commitment", required=True)
    args = parser.parse_args()

    result = initialize(args.root.resolve(), args.commitment)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
