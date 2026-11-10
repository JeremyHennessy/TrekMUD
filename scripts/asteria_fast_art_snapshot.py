#!/usr/bin/env python3
"""Pack/verify a reusable Asteria fast-art base; never alter published routes.

The producer runs only after the existing full scene/Chromium gate passes.
The consumer requires a pinned Actions run, SHA and unchanged source inputs.
The command Blender source is deliberately NOT pinned: it is the art variable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

IMMUTABLE = (
    "ui/3d-preview-v3/index.html",
    "ui/3d-preview-v5-command/src/main.js",
    "ui/3d-preview-v5-command/src/index.html",
    "ui/3d-preview-v5/package-lock.json",
    "scripts/extract_asteria_v3_for_v5.py",
    "scripts/build_asteria_v5_assets.py",
    "scripts/asteria_hero_chair_blender.py",
    "scripts/asteria_fetch_cc0_velour.py",
    "scripts/asteria_three_rib_bays_blender.py",
    "scripts/asteria_envelope_blender.py",
    "scripts/asteria_stage28_coffer_geometry.py",
    "scripts/asteria_stage29_forward_geometry.py",
    "scripts/asteria_envelope_scanned_pbr.py",
    "scripts/asteria_command_pbr_maps.py",
)
V3_SHA = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
COMMAND = "models/asteria-command-set-candidate.glb"
REQUIRED = (
    "index.html", "app.js", "models/asteria-v3-restored-pbr.glb",
    "models/asteria-hero-chair-candidate.glb", COMMAND,
    "models/asteria-three-original-pitch-rib-bays-04.glb",
    "models/asteria-realistic-architectural-envelope-08.glb",
    "models/envelope-manifest.json", "models/manifest.json",
)
def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()

def source_hashes() -> dict[str, str]:
    hashes = {}
    for name in IMMUTABLE:
        path = Path(name)
        assert path.is_file(), ("Missing protected source", name)
        hashes[name] = digest(path)
    original = subprocess.check_output(
        ["git", "hash-object", "ui/3d-preview-v3/index.html"], text=True
    ).strip()
    assert original == V3_SHA, ("Frozen V3 changed", original)
    return hashes

def collect(root: Path) -> dict[str, str]:
    assert (root / "site").is_dir() and (root / "maps").is_dir()
    for rel in REQUIRED:
        assert (root / "site" / rel).is_file(), ("Missing model", rel)
    assert (root / "maps" / "material-provenance.json").is_file()
    found = {}
    for folder in ("site", "maps"):
        for file in sorted((root / folder).rglob("*")):
            assert not file.is_symlink(), ("Refusing symlink", str(file))
            if file.is_file():
                found[file.relative_to(root).as_posix()] = digest(file)
    return found

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("pack", "verify"))
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--site", type=Path)
    ap.add_argument("--maps", type=Path)
    ap.add_argument("--base-sha", required=True)
    args = ap.parse_args()
    assert len(args.base_sha) == 40 and all(c in "0123456789abcdef" for c in args.base_sha)
    if args.mode == "pack":
        assert args.site and args.maps and not args.root.exists()
        args.root.mkdir(parents=True)
        shutil.copytree(args.site, args.root / "site")
        shutil.copytree(args.maps, args.root / "maps")
        record = {
            "kind": "ASTERIA_FAST_ART_VERIFIED_BASE_V1",
            "sourceCommit": args.base_sha,
            "frozenV3Blob": V3_SHA,
            "sourceHashes": source_hashes(),
            "fileHashes": collect(args.root),
            "artVariable": "candidate command GLB only",
            "productionApproved": False,
        }
        (args.root / "snapshot.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    else:
        record = json.loads((args.root / "snapshot.json").read_text())
        assert record["kind"] == "ASTERIA_FAST_ART_VERIFIED_BASE_V1"
        assert record["sourceCommit"] == args.base_sha
        assert record["frozenV3Blob"] == V3_SHA
        assert record["sourceHashes"] == source_hashes(), "Frozen source diverged; rebuild full base"
        assert record["fileHashes"] == collect(args.root), "Baseline payload hash mismatch"
        assert record["artVariable"] == "candidate command GLB only"
        assert record["productionApproved"] is False
    print("ASTERIA_SHA_PINNED_FAST_ART_BASE", args.mode, len(record["fileHashes"]),
          record["sourceCommit"], flush=True)

if __name__ == "__main__":
    main()
