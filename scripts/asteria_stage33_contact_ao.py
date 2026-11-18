#!/usr/bin/env python3
"""Stage33 opt-in, genuine Cycles local-contact AO atlas for 14 formed parts.
Never touches original model, game/UI, carpet or shared non-Stage33 materials.
Not a full global-illumination lightmap.
"""
def bake(bpy,command,out):
    objects=sorted((ob for ob in command.objects
                    if ob.type=="MESH" and ob.name.startswith("STAGE33 / command ")),
                   key=lambda ob:ob.name)
    assert len(objects)==14 and sum(len(ob.data.polygons) for ob in objects)==840
    mats={ob.active_material.name:ob.active_material for ob in objects}
    assert len(mats)==3,("Expected three Stage33 material clones",list(mats))
    for ob in objects:
        assert len(ob.data.uv_layers)==2
        assert ob.data.uv_layers[0].name=="STAGE33_METRIC_PER_FACE_PBR_UV0"
        assert ob.data.uv_layers[1].name=="STAGE33_LOCAL_CONTACT_UV1"
    scene=bpy.context.scene
    old_samples,old_margin=scene.cycles.samples,scene.render.bake.margin
    scene.render.engine="CYCLES"
    scene.cycles.samples=18
    scene.render.bake.margin=2
    atlas=bpy.data.images.new("ASTERIA_STAGE33_REAL_LOCAL_CYCLES_AO",
                               width=2048,height=2048,alpha=False,float_buffer=False)
    atlas.generated_color=(1.,1.,1.,1.)
    temporary={}
    original={}
    try:
        for name,mat in mats.items():
            nodes=mat.node_tree.nodes
            output=next(n for n in nodes if n.type=="OUTPUT_MATERIAL")
            assert len(output.inputs["Surface"].links)==1
            original[name]=output.inputs["Surface"].links[0].from_socket
            tex=nodes.new("ShaderNodeTexImage")
            tex.image=atlas
            tex.label="Actual 0.26m Cycles contact AO / own UV1"
            uv=nodes.new("ShaderNodeUVMap")
            uv.uv_map="STAGE33_LOCAL_CONTACT_UV1"
            mat.node_tree.links.new(uv.outputs["UV"],tex.inputs["Vector"])
            ao=nodes.new("ShaderNodeAmbientOcclusion")
            ao.inputs["Distance"].default_value=.26
            ao.inputs["Color"].default_value=(1.,1.,1.,1.)
            ao.samples=18
            emission=nodes.new("ShaderNodeEmission")
            mat.node_tree.links.new(ao.outputs["Color"],emission.inputs["Color"])
            mat.node_tree.links.new(emission.outputs["Emission"],output.inputs["Surface"])
            for node in nodes:node.select=False
            tex.select=True
            nodes.active=tex
            temporary[name]=(tex,uv,ao,emission,output)
        bpy.ops.object.select_all(action="DESELECT")
        for ob in objects:
            ob.select_set(True)
            ob.data.uv_layers.active=ob.data.uv_layers["STAGE33_LOCAL_CONTACT_UV1"]
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.bake(type="EMIT")
    finally:
        for name,mat in mats.items():
            if name not in temporary:continue
            tex,uv,ao,emission,output=temporary[name]
            mat.node_tree.links.new(original[name],output.inputs["Surface"])
            mat.node_tree.nodes.remove(emission)
            mat.node_tree.nodes.remove(ao)
        for ob in objects:ob.data.uv_layers.active_index=0
        scene.cycles.samples=old_samples
        scene.render.bake.margin=old_margin
    file=out/"asteria-stage33-real-cycles-contact-uv1.png"
    atlas.filepath_raw=str(file.resolve())
    atlas.file_format="PNG"
    atlas.save()
    assert file.stat().st_size>10000,("Stage33 AO atlas missing or flat",file.stat().st_size)
    atlas.pack()
    group=bpy.data.node_groups.get("glTF Settings")
    if group is None:group=bpy.data.node_groups.new("glTF Settings","ShaderNodeTree")
    if "Occlusion" not in [item.name for item in group.interface.items_tree]:
        group.interface.new_socket(name="Occlusion",in_out="INPUT",socket_type="NodeSocketColor")
    for name,mat in mats.items():
        tex=temporary[name][0]
        holder=mat.node_tree.nodes.new("ShaderNodeGroup")
        holder.node_tree=group
        mat.node_tree.links.new(tex.outputs["Color"],holder.inputs["Occlusion"])
    return {"atlasFile":str(file),"resolution":[2048,2048],
            "objects":len(objects),"triangles":840,"rayDistanceMeters":.26,
            "source":"genuine Cycles local AO shader baked to disjoint UV1 triangles",
            "fullIndirectGI":False,"glTFUV1StillToVerify":True}
