#!/usr/bin/env python3
"""Create an immutable TrekMUD campaign checkpoint manifest.

This does not commit anything. It validates the coherent working tree, marks the
root state with the current checkpoint ID, and writes a content-hash manifest.
The Git commit containing those changes is the actual atomic checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_campaign import ValidationError, validate

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def checkpoint_files(root: Path, state: dict[str, Any]) -> list[str]:
    paths = {
        "campaign/state.json",
        "campaign/config.json",
        "campaign/CHRONICLE.md",
        *state["components"].values(),
    }
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    root = args.root.resolve()

    # Validate the candidate snapshot before mutating checkpoint metadata.
    validate(root)

    state_path = root / "campaign" / "state.json"
    state = read_json(state_path)
    revision = state["revision"]
    checkpoint_id = f"r{revision:05d}"
    checkpoint_path = root / "campaign" / "checkpoints" / f"{checkpoint_id}.json"

    if checkpoint_path.exists():
        raise SystemExit(f"checkpoint already exists and is immutable: {checkpoint_path}")

    checkpoint_meta = state.get("checkpoint")
    if not isinstance(checkpoint_meta, dict):
        raise SystemExit("state.checkpoint must be an object")

    previous_id = checkpoint_meta.get("lastCheckpointId")
    checkpoint_meta["lastCheckpointId"] = checkpoint_id
    checkpoint_meta["validated"] = True
    # Commit SHA is intentionally not stored here: it does not exist until after
    # the files are committed. The commit that introduces this immutable
    # manifest is discoverable from Git history and is the checkpoint SHA.
    checkpoint_meta.pop("lastCheckpointCommit", None)
    write_json(state_path, state)

    # Validate again after checkpoint metadata mutation.
    result = validate(root)

    files = checkpoint_files(root, state)
    file_hashes: dict[str, str] = {}
    for relative_path in files:
        path = root / relative_path
        if not path.exists():
            raise SystemExit(f"checkpoint file missing: {relative_path}")
        file_hashes[relative_path] = sha256_file(path)

    manifest = {
        "schemaVersion": 1,
        "checkpointId": checkpoint_id,
        "revision": revision,
        "rulesVersion": state.get("rulesVersion"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "summary": args.summary,
        "previousCheckpointId": previous_id,
        "validation": result,
        "files": file_hashes,
    }
    write_json(checkpoint_path, manifest)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
