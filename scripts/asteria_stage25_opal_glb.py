#!/usr/bin/env python3
"""Stage25 exact-material GLB experiment: NO DEPLOY, no geometry rewrite.

Input is a genuine Blender-exported whole-room architectural GLB. Output
has an identical binary buffer and glTF document except for the single
emissiveFactor on the new six-only recessed opal diffuser material.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path

MAGIC = b'glTF'
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942
EXPECTED = 'ZONE20 / isolated six-only opal emission'


def unpack_glb(blob: bytes):
    magic, version, total = struct.unpack_from('<4sII', blob, 0)
    assert magic == MAGIC and version == 2 and total == len(blob)
    offset, chunks = 12, []
    while offset < len(blob):
        length, kind = struct.unpack_from('<II', blob, offset)
        start = offset + 8
        assert start + length <= len(blob) and length % 4 == 0
        chunks.append((kind, blob[start:start + length]))
        offset = start + length
    assert offset == len(blob) and len(chunks) == 2
    assert [kind for kind, _ in chunks] == [JSON_CHUNK, BIN_CHUNK]
    return json.loads(chunks[0][1].decode('utf-8')), chunks[1][1]


def pack_glb(doc, binary):
    raw = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    raw += b' ' * ((-len(raw)) % 4)
    total = 12 + 8 + len(raw) + 8 + len(binary)
    return (struct.pack('<4sII', MAGIC, 2, total)
            + struct.pack('<II', len(raw), JSON_CHUNK) + raw
            + struct.pack('<II', len(binary), BIN_CHUNK) + binary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('control', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--ratio', type=float, default=0.2)
    args = parser.parse_args()
    assert args.control.resolve() != args.candidate.resolve()
    assert 0 < args.ratio < 1

    original = args.control.read_bytes()
    doc, binary = unpack_glb(original)
    candidate = copy.deepcopy(doc)
    matches = [(i, m) for i, m in enumerate(candidate['materials'])
               if m['name'] == EXPECTED]
    assert len(matches) == 1, ('Missing/duplicate six-only material', matches)
    mat_index, mat = matches[0]
    emissive = mat.get('emissiveFactor')
    assert (isinstance(emissive, list) and len(emissive) == 3
            and all(0 < component <= 1 for component in emissive)), emissive

    # Keep any exported KHR_materials_emissive_strength exactly identical.
    # Changing the three linear emissiveFactor components by the same ratio
    # reduces only this six-object material's light contribution.
    before = emissive[:]
    mat['emissiveFactor'] = [round(component * args.ratio, 8)
                             for component in before]

    users = []
    for node in candidate['nodes']:
        if 'mesh' not in node:
            continue
        materials = {p.get('material') for p in
                     candidate['meshes'][node['mesh']]['primitives']}
        if mat_index in materials:
            assert materials == {mat_index}, ('Mixed-material diffuser', node.get('name'))
            users.append(node.get('name', ''))
    assert len(users) == 6, ('Diffuser must affect exactly six meshes', users)
    assert all('ZONE20' in name and 'inset opal light diffuser' in name
               for name in users), users

    reverted = copy.deepcopy(candidate)
    reverted['materials'][mat_index]['emissiveFactor'] = before
    assert reverted == doc, 'Other glTF data changed unexpectedly'
    changed = pack_glb(candidate, binary)
    args.candidate.write_bytes(changed)
    parsed, check_binary = unpack_glb(args.candidate.read_bytes())
    assert parsed == candidate and check_binary == binary

    report = {
        'stage': 'Stage25 opt-in six-opal material attribution',
        'sourceGLBSha256': hashlib.sha256(original).hexdigest(),
        'candidateGLBSha256': hashlib.sha256(changed).hexdigest(),
        'identicalBinaryGeometryUVTexturePayload': True,
        'allOtherGLTFSceneMaterialsTexturesAndExtensionsUnchanged': True,
        'changedMaterialName': EXPECTED,
        'changedMaterialIndex': mat_index,
        'users': users,
        'exactDiffuserMeshCount': len(users),
        'emissiveFactorBefore': before,
        'emissiveFactorAfter': mat['emissiveFactor'],
        'ratio': args.ratio,
        'original12FixtureMaterialUntouched': True,
        'artApproved': False,
        'deployed': False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('STAGE25_EXACT_SINGLE_MATERIAL_CHANGE', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
