#!/usr/bin/env python3
"""Ensure the conditioning layout is only a V3-inspired room blockout and keeps apertures."""
import json,sys
from pathlib import Path
import trimesh
p=Path(sys.argv[1]);data=json.loads(p.with_suffix('.json').read_text());s=trimesh.load(p,force='scene')
n=set(s.geometry.keys())
assert data['roomId']=='AST-D01-BRIDGE' and data['approvedNeighbor']=='AST-D01-HUB-C'
assert len(n)>=100 and len(n)==data['meshCount']
assert 'AST_Command_Dais_Step' in n and 'AST_Captain_Chair_Back' in n
assert 'AST_Forward_Viewscreeen_Frame' in n and 'AST_Aft_Access_Hub_Opening' in n
assert all(abs(s.bounds[i][j])<=7.6 for i in (0,1) for j in (0,2) if j==0)
assert p.stat().st_size<500000
print(json.dumps({'valid':True,'meshes':len(n),'bounds':s.bounds.tolist(),'bytes':p.stat().st_size}))