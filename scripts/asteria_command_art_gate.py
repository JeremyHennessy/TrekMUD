#!/usr/bin/env python3
"""Source-exact, non-deploy Asteria command art browser gate (not an ART PASS).

Requires original files from GitHub Actions run 42749695563, artifact 13733886895.
Run each camera/arm separately to avoid SwiftShader state accumulation:

  xvfb-run -a python scripts/asteria_command_art_gate.py --original BASE \
    --candidate STANDALONE.glb --output OUT --mode before --view desktop
  # Repeat for before mobile, after desktop, after mobile. Compare images manually.

Never writes to the source archive, repo, production or published assets.
"""
import argparse
import asyncio
import hashlib
import json
import struct
from pathlib import Path
from urllib.parse import urlparse, unquote
from playwright.async_api import async_playwright

SNAPSHOT_SHA = 'bdadf652c2c83098909cc18b6f1b6a1cc828933da55416e00bfff96b13c4fa29'
COMMAND_SHA = '9b988aaec53afa557011e5cba1addc19b1de6bf8f5d8bb6a7edc560ae8452f1c'
COMMAND_PATH = 'models/asteria-command-set-candidate.glb'
SIZES = {'desktop': (1280, 800), 'mobile': (390, 844)}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def glb(blob):
    assert blob[:4] == b'glTF' and struct.unpack_from('<II', blob, 4) == (2, len(blob))
    size, kind = struct.unpack_from('<I4s', blob, 12)
    assert kind == b'JSON'
    document = json.loads(blob[20:20 + size])
    start = 20 + size
    binary_size, kind = struct.unpack_from('<I4s', blob, start)
    assert kind == b'BIN\0' and start + 8 + binary_size == len(blob)
    return document, blob[start + 8:]


def verify_append_only_pbr(before, after, original_binary, candidate_binary, provenance=None):
    """Allow new CC0 materials without permitting edits to any original atlas data.

    This validates the owner's source-byte custody, not the truth of a vendor's
    licence declaration: independent provenance review remains an ART gate.
    """
    assert candidate_binary[:len(original_binary)] == original_binary, \
        'protected original GLB binary/atlas changed'
    for key in ('accessors', 'bufferViews', 'materials', 'images', 'textures', 'samplers'):
        originals = before.get(key, [])
        candidates = after.get(key, [])
        assert candidates[:len(originals)] == originals, \
            'protected original GLB list changed: ' + key
    assert len(before['buffers']) == len(after['buffers']) == 1, 'buffer count changed'
    assert {k: v for k, v in before['buffers'][0].items() if k != 'byteLength'} == \
           {k: v for k, v in after['buffers'][0].items() if k != 'byteLength'}, \
           'protected original buffer metadata changed'
    assert after['buffers'][0]['byteLength'] == len(candidate_binary), \
        'candidate BIN length not declared correctly'
    assert len(after['nodes']) == len(before['nodes']) == 90, 'original node count changed'
    assert len(after['meshes']) == len(before['meshes']) == 90, 'original mesh count changed'
    for i in range(90):
        assert before['nodes'][i] == after['nodes'][i], 'original node changed: ' + str(i)
        if i != 52:
            assert before['meshes'][i] == after['meshes'][i], \
                'protected geometry changed: ' + str(i)
    assert before['meshes'][52] != after['meshes'][52], 'no candidate geometry change'
    allowed = {'meshes', 'accessors', 'bufferViews', 'buffers', 'materials',
               'images', 'textures', 'samplers'}
    for key in set(before) | set(after):
        if key not in allowed:
            assert before.get(key) == after.get(key), 'protected GLB structure changed: ' + key

    changed_pbr = any(len(after.get(k, [])) > len(before.get(k, []))
                      for k in ('materials', 'images', 'textures', 'samplers'))
    if changed_pbr:
        assert isinstance(provenance, dict), 'PBR additions require source provenance JSON'
        assert provenance.get('license') == 'CC0-1.0', 'CC0 source proof required'
        assert str(provenance.get('source_url', '')).startswith('https://'), \
            'PBR source URL required'
        assert str(provenance.get('author', '')).strip(), 'PBR author required'
        assert str(provenance.get('asset_name', '')).strip(), 'PBR asset name required'
    else:
        assert provenance is None, 'provenance supplied but no additional PBR materials'
    new_image_start = len(before.get('images', []))
    new_images = list(range(new_image_start, len(after.get('images', []))))
    ledger = provenance.get('images', []) if provenance else []
    assert sorted(row.get('index') for row in ledger) == new_images, \
        'PBR image provenance ledger must exactly enumerate added images'
    for row in ledger:
        img = after['images'][row['index']]
        assert 'uri' not in img, 'external image URI prohibited'
        assert img.get('mimeType') in ('image/png', 'image/jpeg', 'image/webp'), \
            'embedded image type unsupported'
        view_id = img.get('bufferView')
        assert isinstance(view_id, int) and view_id >= len(before['bufferViews']), \
            'new PBR image does not use new appended buffer view'
        view = after['bufferViews'][view_id]
        offset, length = view.get('byteOffset', 0), view['byteLength']
        assert offset >= len(original_binary) and offset + length <= len(candidate_binary), \
            'new PBR image overlaps original binary or goes out of bounds'
        assert digest(candidate_binary[offset:offset + length]) == row.get('sha256'), \
            'new PBR embedded image hash mismatches provenance'
    return {'newMaterials': len(after.get('materials', [])) - len(before.get('materials', [])),
            'newImages': len(new_images), 'provenanceDeclaredNotIndependentlyLicensed': changed_pbr}


def preflight(base, candidate, provenance=None):
    manifest = (base / 'snapshot.json').read_bytes()
    assert digest(manifest) == SNAPSHOT_SHA, 'unpinned original manifest'
    files = json.loads(manifest)['fileHashes']
    assert len(files) == 30
    for name, expected in files.items():
        item = (base / name).resolve()
        assert item.is_relative_to(base.resolve()) and digest(item.read_bytes()) == expected, name
    original = (base / 'site' / COMMAND_PATH).read_bytes()
    assert digest(original) == COMMAND_SHA
    before, binary = glb(original)
    after, candidate_binary = glb(candidate.read_bytes())
    pbr_receipt = verify_append_only_pbr(before, after, binary, candidate_binary, provenance)
    return {'verifiedOriginalFiles': 30, 'sourceSHA256': COMMAND_SHA,
            'candidateSHA256': digest(candidate.read_bytes()),
            'unchangedOriginalMeshes': 89, 'unchangedOriginalNodes': 90,
            'originalGLBBinaryPrefixAndAtlasUnchanged': True,
            'appendOnlyPBR': pbr_receipt}


async def capture(base, candidate, output, mode, view, chrome):
    width, height = SIZES[view]
    errors, paths = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path=chrome, headless=False,
            args=['--no-sandbox', '--disable-gpu-sandbox', '--enable-webgl',
                  '--use-gl=angle', '--use-angle=swiftshader',
                  '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        try:
            page = await browser.new_page(viewport={'width': width, 'height': height},
                                          device_scale_factor=1)
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)

            async def serve(route):
                path = unquote(urlparse(route.request.url).path).lstrip('/') or 'index.html'
                disk = (base / path if path.startswith('maps/') else base / 'site' / path).resolve()
                if not disk.is_relative_to(base.resolve()) or not disk.is_file():
                    errors.append('missing: ' + path)
                    await route.abort()
                    return
                data = disk.read_bytes()
                if path == COMMAND_PATH and mode == 'after':
                    data = candidate.read_bytes()
                if path == 'app.js':
                    old = b'let ue=n.get("studioCapture");'
                    tick = b'function ee(k){requestAnimationFrame(ee);'
                    assert data.count(old) == data.count(tick) == 1, 'capture-only script drift'
                    data = data.replace(old, b'let ue=n.get("studioCapture")||"command";', 1)
                    data = data.replace(tick, b'function ee(k){window.__asteriaFrames=(window.__asteriaFrames||0)+1;if(window.__asteriaFrames<5)requestAnimationFrame(ee);', 1)
                mime = {'js': 'application/javascript', 'glb': 'model/gltf-binary',
                        'png': 'image/png', 'json': 'application/json',
                        'html': 'text/html'}.get(disk.suffix.lstrip('.'), 'application/octet-stream')
                paths.append(path)
                await route.fulfill(body=data, content_type=mime, headers={
                    'access-control-allow-origin': '*', 'cache-control': 'no-store'})

            await page.route('**/*', serve)
            html = (base / 'site/index.html').read_text().replace(
                '<head>', '<head><base href="https://asteria.local/">', 1)
            await page.set_content(html, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_function(
                'document.body.dataset.originalScenePreserved !== undefined', timeout=60000)
            await page.wait_for_timeout(800)
            frames = await page.evaluate('window.__asteriaFrames || 0')
            assert frames > 0 and COMMAND_PATH in paths and not errors, (frames, errors)
            output.mkdir(parents=True, exist_ok=True)
            screenshot = output / f'{mode}_{view}_{width}x{height}.png'
            await page.screenshot(path=str(screenshot), timeout=30000)
            return {'file': screenshot.name, 'sha256': digest(screenshot.read_bytes()),
                    'dataset': await page.evaluate('JSON.parse(JSON.stringify(document.body.dataset))'),
                    'browserFrames': frames, 'loadedCommandAsset': True, 'javascriptErrors': errors}
        finally:
            await browser.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mode', required=True, choices=('before', 'after'))
    p.add_argument('--view', required=True, choices=tuple(SIZES))
    p.add_argument('--chromium', default='/usr/bin/chromium')
    p.add_argument('--pbr-provenance', type=Path, default=None,
                   help='Required for new materials/textures: CC0 JSON + embedded image SHA-256 ledger')
    a = p.parse_args()
    provenance = json.loads(a.pbr_provenance.read_text()) if a.pbr_provenance else None
    receipt = preflight(a.original, a.candidate, provenance)
    receipt.update(browser=asyncio.run(capture(
        a.original, a.candidate, a.output, a.mode, a.view, a.chromium)),
        artVerdict='UNREVIEWED - manual art acceptance required', releaseAuthorized=False)
    (a.output / f'{a.mode}_{a.view}_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'technicalBrowserGate': 'PASS', 'artVerdict': receipt['artVerdict'],
                      'capture': receipt['browser']['file']}, indent=2))


if __name__ == '__main__':
    main()
