#!/usr/bin/env python3
"""Fail closed if scene source, geometry, game isolation or texture payload drift."""
import json,struct,sys
from pathlib import Path
import trimesh
root=Path(__file__).resolve().parents[1]
dir=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'_site/3d-preview-v5'
assert (dir/'index.html').is_file() and (dir/'app.js').stat().st_size>200000
file=dir/'models/asteria-v3-restored-pbr.glb'
assert 5_000_000<file.stat().st_size<24_000_000
s=trimesh.load(file,force='scene',process=False)
assert len(s.geometry)==10,len(s.geometry)
assert sum(len(g.faces) for g in s.geometry.values())==106988
bounds=s.bounds
assert abs(bounds[0][0]+7.55)<.002 and abs(bounds[1][0]-7.55)<.002,bounds
assert abs(bounds[0][2]+6.558)<.005 and abs(bounds[1][2]-6.558)<.005,bounds
assert abs(bounds[1][1]-4.462)<.005,bounds
j=json.loads((dir/'models/manifest.json').read_text())
assert j['source_git_blob']=='74a154ae62bccb0c16d03c2ecf791a64ab19ce81'
assert j['triangles']==106988
assert 'TrekMUD-GM' not in (dir/'index.html').read_text()
print(json.dumps({'valid':True,'roomId':'AST-D01-BRIDGE','meshes':len(s.geometry),'triangles':106988,'bytes':file.stat().st_size,'bounds':bounds.tolist()}),flush=True)