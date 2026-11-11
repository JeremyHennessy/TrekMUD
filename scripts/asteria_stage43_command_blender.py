#!/usr/bin/env python3
"""Stage43 opt-in single PORT raked monocoque sculpt — draft PR #84 ONLY.

Reuse original Asteria command builder and proven maps byte-identically;
replace only four exact source-owned lower port objects after normal source
build. No new screen/buttons, UI, atlas, camera, navigation, game, V3 or Pages
path change. Stage43 asset is intentionally NOT art/release approved.
"""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import asteria_command_blender as original

SCULPT=Path(__file__).with_name('asteria_stage43_sculpt.json')
REMOVED=('moulded eight-corner closed cast pedestal','recessed toe support',
         'rear service door','light-seam recess')
removed=[];new=[]
true_make=original.make_pylon

def stage43_make_pylon(side,mats,correct_screen_uv=False,stage33=False):
    assert not stage33, 'Never stack rejected Stage33 and Stage43 art'
    before=set(original.COMMAND.objects)
    true_make(side,mats,correct_screen_uv,stage33=False)
    if side!= -1:return  # starboard, controls and platform exactly original
    made=[ob for ob in original.COMMAND.objects if ob not in before]
    expected={f'Command / -1 / {name}' for name in REMOVED}
    found={ob.name for ob in made if ob.name in expected}
    assert found==expected,(found,expected)
    for ob in made:
        if ob.name in expected:
            removed.append(ob.name)
            bpy.data.objects.remove(ob,do_unlink=True)
    sculpt=json.loads(SCULPT.read_text())
    assert sculpt['id']=='ASTERIA_STAGE43_ART_NO_DEPLOY'
    parts=sculpt['parts']
    assert len(parts)==10
    for q in parts:
        verts=q['vertices'];faces=q['faces'];name=q['name']
        assert q['material'] in ('powder_ivory','powder_graphite','console_gasket','satin_nickel')
        assert len(verts)>=8 and len(faces)>=8 and len(set(map(tuple,verts)))==len(verts),(name,len(verts))
        for p in verts:
            assert -1.95<p[0]<-.60 and .27<=p[1]<1.12 and -.10<p[2]<1.3,(name,p)
        for f in faces:
            assert len(f)==3 and len(set(f))==3 and all(0<=i<len(verts) for i in f),(name,f)
        # Texture coordinates supplied ONLY for new geometry; unchanged original
        # control mesh/glass/screen textures remain untouched.
        uvs=[((x+2)/4,(z+.65)/3.5) for x,y,z in verts]
        ob=original.model('Command / -1 / STAGE43 / '+name,verts,faces,mats[q['material']],uvs)
        new.append(ob)

def main():
    original.make_pylon=stage43_make_pylon
    original.main()
    assert len(removed)==4 and len(new)==10,(removed,len(new))
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    out=Path(argv[argv.index('--out')+1]);out.mkdir(parents=True,exist_ok=True)
    report={'id':'STAGE43_ONE_PIECE_PORT_COMMAND_SCULPT','optIn':True,
            'sourceSculptSHA256':hashlib.sha256(SCULPT.read_bytes()).hexdigest(),
            'removedSourceNodes':sorted(removed),'addedComponents':len(new),
            'starboardUnchanged':True,'originalScreenAtlasUntouched':True,
            'originalUIAndWorldRoutesUntouched':True,'originalSourceV3Untouched':True,
            'newComponentUV1ContactAOProven':False,
            'browserArtApproval':False,'fullReleaseValidated':False,
            'productionModified':False}
    (out/'stage43-art-trial.json').write_text(json.dumps(report,indent=2)+'\n')
    print('STAGE43_ISOLATED_PORT_SCULPT',json.dumps(report))

if __name__=='__main__':main()
