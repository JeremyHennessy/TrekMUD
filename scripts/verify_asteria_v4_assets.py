#!/usr/bin/env python3
"""Immutable campaign, glTF mesh count/material and self-contained scene checks."""
import json, sys
from pathlib import Path
import trimesh
root=Path(__file__).resolve().parents[1]
site=Path(sys.argv[1]) if len(sys.argv)>1 else root/'dist'
model=site/'models'/'asteria-bridge-shell.glb'
report=site/'models'/'asset-report.json'
assert model.is_file() and model.stat().st_size>1_000_000
assert report.is_file()
data=json.loads(report.read_text())
scene=trimesh.load(model,force='scene')
names=set(scene.graph.nodes_geometry)
assert len(names)>=440, len(names)
for needle in ('AST_Captain_Seat_Padded_Contour','AST_Captain_Seat_Outer_Composite_Shell','AST_Command_Pylon_Base_1','AST_Flight_Desk_Raked_Molded_Console','AST_Ceiling_Light_Diffuser_1_0','AST_Viewer_Header'):
 assert needle in names, needle
assert data['originalRoomId']=='AST-D01-BRIDGE'
assert data['triangles']>50000
assert data['glbBytes']==model.stat().st_size
assert 7.4<float(scene.bounds[1][0])<7.6
assert 4.2<float(scene.bounds[1][1])<4.6
materials={getattr(g.visual.material,'name','') for g in scene.geometry.values()}
assert len(materials)>=13, materials
for k in ('carpet','wall','upholstery','bronze'):
 found=[g for g in scene.geometry.values() if getattr(g.visual.material,'name','')=='ASTERIA_'+k]
 assert found, k
 assert found[0].visual.material.normalTexture is not None,k
 assert found[0].visual.material.metallicRoughnessTexture is not None,k
html=(site/'index.html').read_text()
assert 'script src="./app.js"' in html
assert './style.css' in html
assert 'https://' not in html
bundle=(site/'app.js').read_text()
for keyword in ('AST-D01-BRIDGE','asteria-bridge-shell.glb','GLTFLoader','v4Ready'):
 assert keyword in bundle,keyword
for forbidden in ('TrekMUD-GM','secretSeedHex','campaign/state.json','plot-clocks'):
 assert forbidden not in bundle,forbidden
print(json.dumps({'valid':True,'nodes':len(names),'faces':sum(len(g.faces) for g in scene.geometry.values()),'materials':len(materials),'bytes':model.stat().st_size},indent=2))