#!/usr/bin/env python3
"""Opt-in Stage44: restore real PBR UV0 on the original PORT command housing.

No new geometry, no removal, no other node changes. The SHA-pinned baseline
housing has 76 triangles, a photographed powder_ivory glTF material, but NO
TEXCOORD_0: the texture cannot sample across its visible surface. This trial
measures whether that missing mapping is a real source of the flat look.
Draft PR #84 only. Not artistically accepted; never deploy automatically.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import asteria_command_blender as original

make_pylon_original = original.make_pylon
changed = []
def make_pylon_mapped(side, mats, correct_screen_uv=False, stage33=False):
    assert not stage33, "Do not stack rejected source art"
    before = set(original.COMMAND.objects)
    make_pylon_original(side, mats, correct_screen_uv=correct_screen_uv, stage33=False)
    if side != -1: return
    name = "Command / -1 / moulded eight-corner closed cast pedestal"
    found = [o for o in original.COMMAND.objects if o not in before and o.name == name]
    assert len(found) == 1, (name, len(found))
    ob = found[0]
    assert ob.type == "MESH" and len(ob.data.polygons) == 76
    assert len(ob.data.uv_layers) == 0, "Root cause changed; do not silently overwrite authored UV"
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.018, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    assert len(ob.data.uv_layers) == 1
    ob.data.uv_layers[0].name = "AST_PORT_CABINET_PBR_UV0"
    assert len(ob.data.polygons) == 76, "UV0 fix must not change original faces"
    changed.append(name)

def main():
    original.make_pylon = make_pylon_mapped
    original.main()
    assert changed == ["Command / -1 / moulded eight-corner closed cast pedestal"], changed
    a = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out = Path(a[a.index("--out")+1])
    (out/"stage44-art-trial.json").write_text(json.dumps({
       "trial":"STAGE44_SOURCE_EXACT_ORIGINAL_PORT_PBR_UV0_ONLY",
       "modifiedNodes":changed,
       "removedNodes":[], "addedNodes":[],
       "originalPylonTriangles":76,
       "sourceV3Unchanged":True,"screensControlsHUDUnchanged":True,
       "newGeometry":False,"newMaterials":False,"productionModified":False,
       "artApproved":False,"fullReleaseValidated":False
    },indent=2)+"\n")
if __name__ == "__main__": main()
