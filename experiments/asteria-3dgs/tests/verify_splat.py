#!/usr/bin/env python3
"""Validate experimental splat data format and room registration."""
import json, struct, sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);raw=p.read_bytes();assert len(raw)>50000 and len(raw)%32==0
v=np.frombuffer(raw,dtype=[('position','<f4',3),('sigma','<f4',3),('rgba','u1',4),('quat','u1',4)])
assert len(v)>10000 and len(v)<100000
assert np.isfinite(v['position']).all() and np.isfinite(v['sigma']).all()
assert (v['sigma']>0).all() and np.all(v['sigma']<.5)
assert np.all(v['position'][:,1]>.3) and np.all(v['position'][:,1]<2.7)
assert np.ptp(v['position'][:,0])>1.3 and np.ptp(v['position'][:,2])>.8
assert v['rgba'][:,3].min()>100
report=json.loads(p.with_suffix('.json').read_text());assert report['room_id']=='AST-D01-BRIDGE'
assert report['training'].startswith('none:')
assert report['gaussians']==len(v)
print(json.dumps({'valid':True,'gaussians':len(v),'bytes':len(raw),'bounds':[v['position'].min(axis=0).tolist(),v['position'].max(axis=0).tolist()]}))