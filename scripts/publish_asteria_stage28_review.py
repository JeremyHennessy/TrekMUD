#!/usr/bin/env python3
"""Build ONLY an optional source-pinned Stage28 USS Asteria Pages review route.

This is a release assembly script, not a model edit. It refuses to proceed if
any of the 51 previously published Pages files differ from their last
independently verified GitHub Pages artifact (run 42509385166).
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import struct
import tarfile
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
SOURCE = ROOT / "asteria-stage28-reviewed-source"
PREVIOUS = SITE / "3d-preview-v5-three-bays"
NEW = SITE / "3d-preview-v5-stage28-review"
BASELINE = ROOT / "docs/asteria-pages-published-sha256-20261108.json"
PINNED_MAIN = "399de4debfa202e29dbe9887cf11f82cbfbc5b3b"
PINNED_STAGE28 = "ef7078dca29ddf5a89b83aac10bee1afbfa7672c"
V3_BLOB = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*argv: str, env: dict[str, str] | None = None) -> None:
    print("STAGE28_PAGES_RUN", " ".join(map(str, argv)), flush=True)
    subprocess.run(
        [str(x) for x in argv], cwd=SOURCE,
        env={**os.environ, **(env or {})},
        check=True,
    )


def assert_original_pages(expected: dict[str, str]) -> None:
    # GitHub Pages' .nojekyll marker is an empty hosting directive, not an
    # authored site asset in the archived 51-file Pages payload.
    marker = SITE / ".nojekyll"
    if marker.exists():
        assert marker.is_file() and marker.stat().st_size == 0, (
            "Unexpected Pages hosting marker content", marker)
    actual = {
        str(f.relative_to(SITE)): sha(f)
        for f in SITE.rglob("*") if f.is_file() and not f.is_symlink()
        and str(f.relative_to(SITE)) != ".nojekyll"
        and not str(f.relative_to(SITE)).startswith("3d-preview-v5-stage28-review/")
    }
    assert len(expected) == 51, ("Expected 51 frozen published Pages assets", len(expected))
    assert actual == expected, {
        "missing": sorted(expected.keys() - actual.keys()),
        "added": sorted(actual.keys() - expected.keys()),
        "changed": sorted(k for k in expected.keys() & actual.keys()
                          if expected[k] != actual[k]),
    }
    print("STAGE28_PRIOR_PUBLISHED_PAGES_SHA256_MATCH", len(actual), flush=True)


def preserve_historical_runtime_snapshot(expected: dict[str, str]) -> None:
    """Normalize ONLY the time-varying build timestamp to last approved Pages.

    The last published 2026-11-08 artifact is an immutable baseline.
    Fail closed if ANY OTHER data payload content changed.
    """
    frozen = "2026-11-08T18:19:09.530785+00:00"
    for name in ("data/build.json", "data/player-console.json"):
        f = SITE / name
        data = f.read_text()
        pattern = r'("generatedAt": ")[^"]+(")'
        assert len(re.findall(pattern, data)) == 1, name
        fixed = re.sub(pattern, lambda m: m.group(1) + frozen + m.group(2),
                       data, count=1)
        assert json.loads(fixed)["generatedAt"] == frozen
        # Only a formatting-preserving, single-value temporal normalization.
        # Do not rewrite or reinterpret any player campaign payload.
        f.write_text(fixed)
        assert sha(f) == expected[name], (
            "Published player data has changed beyond its generation timestamp",
            name, sha(f), expected[name])
    print("STAGE28_PUBLISHED_PLAYER_PAYLOAD_RESTORED_EXACT_SHA256", flush=True)


def restore_approved_nondeterministic_glbs(expected: dict[str, str]) -> None:
    """Restore ONLY two verified, byte-exact approved Blender GLBs.

    Blender exports vary between otherwise equivalent releases. The project
    requires the already-published command models to remain immutable;
    retrieve ONLY those two files from the exact last successful Pages
    artifact, verify both against archived SHA256, never rewrite new art.
    """
    old = ROOT / "_stage28_pages_frozen_release_archive"
    assert not old.exists(), "Refuse to reuse a stale Pages download"
    old.mkdir()
    cmd = [
        "gh", "run", "download", "42509385166", "--repo",
        "JeremyHennessy/TrekMUD", "--name", "github-pages", "--dir", str(old),
    ]
    assert os.environ.get("GH_TOKEN"), "Read-only Actions token required"
    subprocess.run(cmd, cwd=ROOT, check=True)
    archive = old / "artifact.tar"
    assert archive.is_file() and archive.stat().st_size > 30_000_000
    paths = (
        "3d-preview-v5-command/models/asteria-command-set-candidate.glb",
        "3d-preview-v5-three-bays/models/asteria-command-set-candidate.glb",
    )
    with tarfile.open(archive, mode="r:") as tar:
        for name in paths:
            member = tar.getmember("./" + name)
            assert member.isfile() and member.size > 100_000, (name, member.size)
            stream = tar.extractfile(member)
            assert stream is not None
            data = stream.read()
            got = hashlib.sha256(data).hexdigest()
            assert got == expected[name], ("Incorrect frozen Pages source", name, got)
            current = SITE / name
            assert current.is_file() and current.stat().st_size > 100_000
            current.write_bytes(data)
            assert sha(current) == expected[name]
            print("RESTORED_BYTE_EXACT_ARCHIVED_COMMAND_ASSET", name, got, flush=True)


def safe_replacement(s: str, old: str, new: str) -> str:
    assert s.count(old) == 1, ("Unexpected pinned renderer anchor", old[:95], s.count(old))
    return s.replace(old, new)


def generate_verified_client(tris: int, lights: list[list[float]]) -> None:
    assert len(lights) == 6
    source = (SOURCE / "ui/3d-preview-v5-command/src/main.js").read_text()
    source = safe_replacement(
        source, "  const views={",
        "  const views={"
        "\n    envelopeWall:{x:-2.6,z:-.5,yaw:-1.18,label:'QA WHOLE WALL ONLY'},"
        "\n    envelopeCeiling:{x:-2.32,z:2.15,yaw:.22,label:'QA CEILING ONLY'},"
    )
    source = safe_replacement(
        source, "Object.assign(pos,{x:p.x,z:p.z,yaw:p.y,pitch:-.14});active=name;",
        "Object.assign(pos,{x:p.x,z:p.z,yaw:p.y,pitch:-.14});active=name;"
        "if(name==='envelopeCeiling')pos.pitch=.58;"
    )
    source = safe_replacement(
        source, "triangles!==106988-removed-commandRemoved||missing",
        "triangles!==106988-removed-commandRemoved-174-864||"
        "meta.threeRibBaysRemovedFaces!==174||"
        "(meta.threeRibBaysSourceRanges||[]).length!==3||"
        "meta.envelopeRemovedFaces!==864||"
        "(meta.envelopeSourceRanges||[]).length!==2||missing"
    )
    anchor = "    scene.add(room,hero,command);"
    extra = """    scene.add(room,hero,command);
      // Frozen, measured original V3 acoustic-fin group.
      loader.loadAsync('./models/asteria-three-original-pitch-rib-bays-04.glb')
        .then(({scene:triple})=>{
          let faces=0,meshes=0,missing=0;
          triple.traverse(o=>{
            if(!o.isMesh)return;
            meshes++;
            faces+=o.geometry.index?o.geometry.index.count/3:
                  o.geometry.attributes.position.count/3;
            if(!o.material)missing++;
            else o.material.side=THREE.DoubleSide;
            o.castShadow=!mobile;o.receiveShadow=true;
          });
          if(faces!==13098||meshes!==105||missing){
            fail('Frozen original acoustic-fin group is invalid');return;
          }
          scene.add(triple);
          document.body.dataset.threeBayFaces=String(faces);
          document.body.dataset.threeBayMeshes=String(meshes);
          document.body.dataset.threeBayLoaded='true';
          window.__asteriaThreeBayReview={excludedOriginalFaces:174,noGameWrites:true};
        }).catch(err=>fail('Original acoustic-fin asset failed: '+String(err.message||err)));
      // An opt-in Stage28 experimental roof, not an artistically approved design.
      loader.loadAsync('./models/asteria-realistic-architectural-envelope-08.glb')
        .then(({scene:architecture})=>{
          let faces=0,meshes=0,missing=0,ao=0;
          architecture.traverse(o=>{
            if(!o.isMesh)return;
            meshes++;
            faces+=o.geometry.index?o.geometry.index.count/3:
                  o.geometry.attributes.position.count/3;
            if(!o.material)missing++;
            if(o.material?.aoMap)ao++;
            if(o.material)o.material.side=THREE.DoubleSide;
            o.receiveShadow=true;
            o.castShadow=false;
          });
          if(faces!==EXPECTED_ARCH_FACES||meshes!==119||missing||ao<2){
            fail('Stage28 architectural envelope failed model/PBR/UV1 integrity');return;
          }
          scene.add(architecture);
          for(const xyz of STAGE20_LIGHT_POSITIONS){
            const practical=new THREE.PointLight(0xffddbc,1.85,2.7,2);
            practical.position.set(xyz[0],xyz[1]-.025,xyz[2]);
            scene.add(practical);
          }
          document.body.dataset.envelopeFaces=String(faces);
          document.body.dataset.envelopeMeshes=String(meshes);
          document.body.dataset.envelopeAOMaterials=String(ao);
          document.body.dataset.envelopeOriginalRemoved='864';
          document.body.dataset.envelopeLoaded='true';
          window.__asteriaEnvelopeReview={
            stage:28,originalRemoved:864,bakedCyclesAO:true,
            photographicPBR:true,originalPlayerUnchanged:true,notArtApproved:true};
        }).catch(err=>fail('Stage28 architectural envelope failed: '+String(err.message||err)));
    """
    extra = extra.replace("EXPECTED_ARCH_FACES", str(tris))
    extra = extra.replace("STAGE20_LIGHT_POSITIONS", json.dumps(lights))
    source = safe_replacement(source, anchor, extra)
    assert source.count("threeBayLoaded") == 1
    assert source.count("envelopeLoaded") == 1
    target = SOURCE / "ui/3d-preview-v5/src/__stage28_pages_review.js"
    assert not target.exists(), "Refuse to overwrite a source checkout asset"
    try:
        target.write_text(source)
        run(
            "ui/3d-preview-v5/node_modules/.bin/esbuild", str(target),
            "--bundle", "--platform=browser", "--target=es2021",
            "--format=iife", "--minify", f"--outfile={NEW / 'app.js'}",
        )
    finally:
        target.unlink(missing_ok=True)


def main() -> None:
    assert BASELINE.is_file() and SOURCE.is_dir() and PREVIOUS.is_dir()
    frozen = json.loads(BASELINE.read_text())
    assert frozen["base_main_sha"] == PINNED_MAIN
    assert frozen["source_actions_run"] == 42509385166
    original = frozen["original_files"]
    preserve_historical_runtime_snapshot(original)
    restore_approved_nondeterministic_glbs(original)
    assert_original_pages(original)
    assert not NEW.exists(), "Refuse to overwrite a previously built review route"
    assert subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True
    ).strip() == PINNED_STAGE28
    assert subprocess.check_output(
        ["git", "hash-object", "ui/3d-preview-v3/index.html"], cwd=SOURCE, text=True
    ).strip() == V3_BLOB
    shutil.copytree(PREVIOUS, NEW)
    models = NEW / "models"
    capture = {
        "ASTERIA_V3_CAPTURE_CAPTAIN_CHAIR": "1",
        "ASTERIA_V3_CAPTURE_COMMAND_SECTION": "1",
        "ASTERIA_V3_CAPTURE_INLAID_BAY": "1",
        "ASTERIA_V3_CAPTURE_THREE_RIB_BAYS": "1",
        "ASTERIA_V3_CAPTURE_ENVELOPE": "1",
    }
    run(sys.executable, "scripts/extract_asteria_v3_for_v5.py", env=capture)
    excludes = {
        "ASTERIA_V5_EXCLUDE_CAPTAIN_CHAIR": "1",
        "ASTERIA_V5_EXCLUDE_COMMAND_SECTION": "1",
        "ASTERIA_V5_EXCLUDE_THREE_RIB_BAYS": "1",
        "ASTERIA_V5_EXCLUDE_ENVELOPE": "1",
        "ASTERIA_V5_OUT_DIR": str(models.resolve()),
    }
    run(sys.executable, "scripts/build_asteria_v5_assets.py", env=excludes)
    base = json.loads((models / "manifest.json").read_text())
    assert base["source_git_blob"] == V3_BLOB
    assert base["triangles"] == 81050
    assert base["captain_chair_source_faces_removed"] == 16272
    assert base["command_section_source_faces_removed"] == 8628
    assert base["three_rib_bays_source_faces_removed"] == 174
    assert base["envelope_source_faces_removed"] == 864
    assert [x["faces"] for x in base["envelope_source_ranges"]] == [672, 192]

    run(sys.executable, "scripts/asteria_command_pbr_maps.py",
        "--out", "_command_maps", "--v3-atlas", "_v5_mesh_capture/atlas.png")
    run(sys.executable, "scripts/asteria_envelope_scanned_pbr.py",
        "--out", "_envelope_scanned_maps")
    run("blender", "-b", "-t", "4", "--python-exit-code", "1",
        "--python", "scripts/asteria_envelope_blender.py", "--",
        "--out", "_stage28_pages_envelope",
        "--materials", "_envelope_scanned_maps",
        "--command-materials", "_command_maps",
        "--source-report", "_v5_mesh_capture/envelope-source-spans.json",
        "--samples", "20", "--resolution", "960", "640",
        "--bake-ao", "--omit-radial-rails", "--stage20-zone", "--no-render")
    envelope = SOURCE / "_stage28_pages_envelope"
    report = json.loads((envelope / "architectural-report.json").read_text())
    assert report["sourceV3Blob"] == V3_BLOB
    assert report["meshObjects"] == 119
    assert report["pbrLicense"] == "CC0"
    assert report["stage20ManufacturedZone"]["zoneMeshCount"] == 44
    assert report["stage28CeilingSystem"]["meshCount"] == 45
    assert report["stage28CeilingSystem"]["cofferCount"] == 12
    assert report["stage28CeilingSystem"]["physicallyRecessedPracticalWells"] == 6
    lights = report["stage20ManufacturedZone"]["lightingPositions"]
    assert len(lights) == 6

    import trimesh
    import numpy as np
    from PIL import Image
    original_glb = envelope / "asteria-realistic-architectural-envelope-08.glb"
    assert original_glb.stat().st_size > 200_000
    scene = trimesh.load(original_glb, force="scene", process=False)
    triangles = sum(len(mesh.faces) for mesh in scene.geometry.values())
    assert triangles == 27368, triangles
    raw = original_glb.read_bytes()
    gltf = json.loads(raw[20:20 + struct.unpack_from("<I", raw, 12)[0]])
    uv1_mats = [m for m in gltf["materials"]
                if m.get("occlusionTexture", {}).get("texCoord") == 1]
    assert len(uv1_mats) >= 2 and len(gltf.get("images", [])) >= 12
    ao = {}
    for name in ("wall", "ceiling"):
        pixels = np.asarray(Image.open(envelope /
            f"asteria-envelope-{name}-real-cycles-ao.png").convert("RGB"))[:, :, 0]
        mean, std = float(pixels.mean()), float(pixels.std())
        assert mean > 145 and std > 2, (name, mean, std)
        ao[name] = {"mean": mean, "std": std}
    shutil.copyfile(original_glb, models / original_glb.name)
    proof = {
        "newEnvelopeTriangles": triangles, "meshObjects": 119,
        "sourceRemovedFaces": 864, "pbrImages": len(gltf["images"]),
        "aoMaterialCount": len(uv1_mats),
        "realCyclesAORanges": ao, "ownerVisualApproval": False
    }
    (models / "envelope-manifest.json").write_text(json.dumps(proof, indent=2) + "\n")
    generate_verified_client(triangles, lights)

    # The three published hero furniture GLBs must remain exactly as they were.
    for item in ("asteria-hero-chair-candidate.glb",
                 "asteria-command-set-candidate.glb",
                 "asteria-three-original-pitch-rib-bays-04.glb"):
        assert (models / item).read_bytes() == (PREVIOUS / "models" / item).read_bytes()
    assert (NEW / "index.html").read_bytes() == (PREVIOUS / "index.html").read_bytes()
    assert (NEW / "app.js").stat().st_size > 200_000
    assert b"AST-D01-BRIDGE" in (NEW / "app.js").read_bytes()
    # The new JS, room-model and envelope are distinct; all old game files are untouched.
    assert sha(NEW / "app.js") != sha(PREVIOUS / "app.js")
    (NEW / "review-manifest.json").write_text(json.dumps({
        "id": "USS-ASTERIA-STAGE28-OPTIONAL-REVIEW",
        "art_source": PINNED_STAGE28,
        "main_baseline": PINNED_MAIN,
        "room": "AST-D01-BRIDGE",
        "original_source_blob": V3_BLOB,
        "base_original_faces": 81050,
        "envelope_faces": triangles,
        "stage28_roof_submeshes": 45,
        "existing_routes_modified": False,
        "owner_visual_approval": False,
        "published_only_for_user_requested_review": True,
        "incomplete_new_roof_UV1_contact_AO": True,
        "physical_device_performance_unverified": True,
    }, indent=2) + "\n")
    assert_original_pages(original)
    print("STAGE28_ISOLATED_PAGES_BUILD_PASS",
          "protected_files", len(original),
          "stage28_triangles", triangles,
          "new_url_path", NEW.name,
          "stage28_git_sha", PINNED_STAGE28, flush=True)


if __name__ == "__main__":
    main()
