"""Asteria append-only PBR source custody tests. No CI image or deployment.

Run after installing playwright: python -m unittest tests.test_asteria_command_art_gate_pbr -v
These are pure GLB-ownership checks, not visual ART PASS or licence authentication.
"""
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts" / "asteria_command_art_gate.py"
spec = importlib.util.spec_from_file_location("asteria_gate", FILE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def originals():
    old_binary = b"original-atlas-bytes\0"
    old_binary += b"\0" * (-len(old_binary) % 4)
    before = {
        "asset": {"version": "2.0"},
        "scenes": [{"nodes": list(range(90))}],
        "scene": 0,
        "nodes": [{"mesh": i} for i in range(90)],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}
                   for i in range(90)],
        "buffers": [{"byteLength": len(old_binary)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 4}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 1, "type": "VEC3"}],
        "materials": [{"name": "approved"}],
        "images": [{"bufferView": 0, "mimeType": "image/png"}],
        "textures": [{"source": 0}],
        "samplers": [{"magFilter": 9729}],
    }
    after = copy.deepcopy(before)
    after["meshes"][52]["primitives"][0]["attributes"]["POSITION"] = 1
    after["bufferViews"].append({"buffer": 0, "byteOffset": len(old_binary), "byteLength": 12})
    after["accessors"].append({"bufferView": 1, "componentType": 5126,
                               "count": 1, "type": "VEC3"})
    new_binary = old_binary + b"new-mesh-xyz"
    after["buffers"][0]["byteLength"] = len(new_binary)
    return before, after, old_binary, new_binary


def with_photo(b, a, old, new):
    # Embedded bytes are an isolated test fixture, NOT an actual licensed photograph.
    image = b"\x89PNG\r\n\x1a\n" + bytes(range(20))
    index = len(a["images"])
    a["bufferViews"].append({"buffer": 0, "byteOffset": len(new), "byteLength": len(image)})
    a["images"].append({"bufferView": len(a["bufferViews"]) - 1, "mimeType": "image/png"})
    a["textures"].append({"source": index})
    a["materials"].append({"pbrMetallicRoughness": {
        "baseColorTexture": {"index": len(a["textures"]) - 1}}})
    a["meshes"][52]["primitives"][0]["material"] = len(a["materials"]) - 1
    new += image
    a["buffers"][0]["byteLength"] = len(new)
    provenance = {
        "license": "CC0-1.0",
        "source_url": "https://example.org/test-only-not-a-license",
        "author": "Synthetic test fixture",
        "asset_name": "Synthetic fixture",
        "images": [{"index": index, "sha256": hashlib.sha256(image).hexdigest()}],
    }
    return b, a, old, new, provenance


class AppendOnlyPBR(unittest.TestCase):
    def test_original_unchanged_and_geometry_only(self):
        self.assertEqual(gate.verify_append_only_pbr(*originals())["newImages"], 0)

    def test_append_only_pbr_with_hashed_embedded_image(self):
        b, a, old, new, prov = with_photo(*originals())
        receipt = gate.verify_append_only_pbr(b, a, old, new, prov)
        self.assertEqual((receipt["newMaterials"], receipt["newImages"]), (1, 1))

    def test_corrupt_source_material_node_mesh_and_scene_fail(self):
        for category in ("material", "node", "screen", "scene", "binary"):
            with self.subTest(category=category):
                b, a, old, new = originals()
                if category == "material":
                    a["materials"][0]["name"] = "tampered"
                elif category == "node":
                    a["nodes"][0]["mesh"] = 7
                elif category == "screen":
                    a["meshes"][51]["name"] = "tampered"
                elif category == "scene":
                    a["scene"] = 1
                else:
                    new = b"!" + new[1:]
                with self.assertRaises(AssertionError):
                    gate.verify_append_only_pbr(b, a, old, new)

    def test_unlicensed_external_missing_ledger_and_wrong_hash_fail(self):
        for category in ("missing", "external", "ledger", "hash", "license", "overlap"):
            with self.subTest(category=category):
                b, a, old, new, prov = with_photo(*originals())
                if category == "missing":
                    prov = None
                elif category == "external":
                    a["images"][-1]["uri"] = "https://example.org/external.png"
                elif category == "ledger":
                    prov["images"] = []
                elif category == "hash":
                    prov["images"][0]["sha256"] = "0" * 64
                elif category == "license":
                    prov["license"] = "unreviewed"
                else:
                    a["bufferViews"][-1]["byteOffset"] = 0
                with self.assertRaises(AssertionError):
                    gate.verify_append_only_pbr(b, a, old, new, prov)

    def test_changed_original_atlas_or_wrong_buffer_size_fail(self):
        for category in ("atlas", "length"):
            with self.subTest(category=category):
                b, a, old, new, prov = with_photo(*originals())
                if category == "atlas":
                    a["images"][0]["bufferView"] = 999
                else:
                    a["buffers"][0]["byteLength"] += 4
                with self.assertRaises(AssertionError):
                    gate.verify_append_only_pbr(b, a, old, new, prov)


if __name__ == "__main__":
    unittest.main()
