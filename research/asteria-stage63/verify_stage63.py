#!/usr/bin/env python3
"""Verify Stage63 archived research bytes; never imply art/release approval."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main(source_zip, proof_zip):
    with zipfile.ZipFile(source_zip) as src, zipfile.ZipFile(proof_zip) as proof:
        assert src.testzip() is None and proof.testzip() is None, "ZIP integrity failure"
        snapshot = json.loads(src.read("snapshot.json"))
        for path, expected in snapshot["fileHashes"].items():
            assert digest(src.read(path)) == expected, f"Pinned source mismatch: {path}"
        assert len(snapshot["fileHashes"]) == 30
        evidence = json.loads(proof.read("photo_uv0_test/evidence.json"))
        assert evidence["sourceCommandGLBSHA256"] == digest(
            src.read("site/models/asteria-command-set-candidate.glb"))
        assert evidence["sourceEnvelopeGLBSHA256"] == digest(
            src.read("site/models/asteria-realistic-architectural-envelope-08.glb"))
        for material, record in evidence["embeddedSourceMaps"].items():
            name = f"photo_uv0_test/polyhaven-derived-paint-composite-{material}.png"
            raw = proof.read(name)
            assert digest(raw) == record["sha256"] and len(raw) == record["bytes"], name
        assert digest(proof.read("photo_uv0_test/" + evidence["outputGLB"])) == evidence["outputGLBSHA256"]
        assert evidence["sourcePedestalTriangles"] == 76
        assert evidence["protectedOtherCommandNodes"] == 89
        assert evidence["notAnIntegratedCommandGLB"] is True
        assert evidence["notChromiumOrCyclesVerified"] is True
        assert evidence["notProfessionalArtAcceptance"] is True
        print(json.dumps({
            "source_files_verified": 30,
            "material_maps_verified": 3,
            "experimental_glb_sha256": evidence["outputGLBSHA256"],
            "art_approved": False,
            "deployment_approved": False,
        }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python verify_stage63.py PINNED-SOURCE.zip STAGE63-PROOF.zip")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
