#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import argparse

ROOT=Path(__file__).resolve().parents[1]

class IntegrityError(RuntimeError):
    pass

def require(condition: bool, message: str)->None:
    if not condition:
        raise IntegrityError(message)

def load(path:Path)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value,dict),f"{path} must contain an object")
    return value

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def verify(root:Path=ROOT)->dict:
    state=load(root/"campaign/state.json")
    meta=state.get("checkpoint") or {}
    checkpoint_id=meta.get("lastCheckpointId")
    require(isinstance(checkpoint_id,str),"active checkpoint id missing")
    require(meta.get("validated") is True,"active checkpoint not validated")
    manifest_path=root/"campaign/checkpoints"/f"{checkpoint_id}.json"
    require(manifest_path.exists(),f"manifest missing: {checkpoint_id}")
    manifest=load(manifest_path)
    require(manifest.get("checkpointId")==checkpoint_id,"checkpoint id mismatch")
    require(manifest.get("revision")==state.get("revision"),"revision mismatch")
    expected=manifest.get("files")
    require(isinstance(expected,dict) and expected,"checkpoint hashes missing")
    drift=[]
    for relative,expected_hash in expected.items():
        path=root/relative
        actual="MISSING" if not path.exists() else sha256_file(path)
        if actual!=expected_hash:
            drift.append(relative)
    require(not drift,"checkpoint file drift: "+", ".join(drift))
    previous=manifest.get("previousCheckpointId")
    if previous:
        require((root/"campaign/checkpoints"/f"{previous}.json").exists(),
                f"previous checkpoint missing: {previous}")
    return {
        "valid":True,
        "checkpointId":checkpoint_id,
        "revision":state.get("revision"),
        "previousCheckpointId":previous,
        "hashedFiles":len(expected),
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    args=parser.parse_args()
    print(json.dumps(verify(args.root.resolve()),indent=2))
