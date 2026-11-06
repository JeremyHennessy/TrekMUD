"""Non-destructive upholstery stitch study for the original Asteria command chair.

Adds restrained physical stitch geometry over the existing V3 upholstery.
This is an opt-in Cycles A/B experiment, not a replacement for the chair,
a fabric scan, or an approved design. Coordinates reproduce hero-v3.js chair().
"""
from __future__ import annotations
import math
import bpy
from mathutils import Vector

CHAIR_X = 0.0
CHAIR_Z = 1.20
WIDTH = .54
BACK_HEIGHT = 1.08


def gltf_to_blender(x, y, z):
    return Vector((x, -z, y))


def back_surface(a, t, offset=-.029):
    # Mirrored from ui/3d-preview-v3/hero-v3.js (large=true, rot=0).
    half=WIDTH*(.78+.24*math.sin(math.pi*t)-.075*t)
    rounded=1-.075*abs(a)**8
    y=.76+BACK_HEIGHT*t
    camber=.105*(1-a*a)
    z=.245+.255*t+.032*math.sin(math.pi*t)-camber+offset
    return (CHAIR_X+a*half*rounded, y, CHAIR_Z+z)


def install_stitches():
    collection=bpy.data.collections.new("ASTERIA / OPTIONAL CHAIR STITCH STUDY")
    bpy.context.scene.collection.children.link(collection)
    cloth=bpy.data.materials.new("Asteria muted thread / warm grey")
    cloth.diffuse_color=(.41,.35,.37,1)
    cloth.use_nodes=True
    p=cloth.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(.41,.35,.37,1)
    p.inputs["Roughness"].default_value=.91

    curve=bpy.data.curves.new("Asteria upholstery hand-seam",type="CURVE")
    curve.dimensions="3D"
    curve.resolution_u=2
    curve.bevel_depth=.0018
    curve.resolution_u=1
    curve.bevel_resolution=2
    curve.materials.append(cloth)
    stitch_count=0

    def stitch(a0,t0,a1,t1):
        nonlocal stitch_count
        p0=back_surface(a0,t0,offset=-.042)
        p1=back_surface(a1,t1,offset=-.042)
        # The stitch runs just ahead of the existing front surface.
        spline=curve.splines.new("POLY")
        spline.points.add(1)
        for pt,xyz in zip(spline.points,(p0,p1)):
            v=gltf_to_blender(*xyz)
            pt.co=(v.x,v.y,v.z,1)
        stitch_count+=1

    # Two shoulder-to-seat stitching lines. Short segments with actual
    # breaks read more naturally than another uniformly glowing stripe.
    for side in (-1,1):
        a=.63*side
        for n in range(56):
            t=.105+n*.0135
            stitch(a-.013,t,a+.013,t+.0055)

    # Seat-back horizontal stitching across the shoulder pad.
    for n in range(48):
        a=-.75+n*.031
        stitch(a,.80,a+.014,.80)

    obj=bpy.data.objects.new("Stitched upholstery / V3 source chair",curve)
    collection.objects.link(obj)
    collection["source"] = "ui/3d-preview-v3/hero-v3.js"
    collection["source_v3_blob"] = "74a154ae62bccb0c16d03c2ecf791a64ab19ce81"
    collection["added_stitches"] = stitch_count
    collection["status"] = "unapproved A/B production-detail test"
    return stitch_count
