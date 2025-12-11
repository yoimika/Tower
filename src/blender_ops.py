import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix
from constants import COLORS, MATERIALS
import settings


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        bpy.data.materials.remove(block)

    for block in bpy.data.images:
        bpy.data.images.remove(block)

    for block in bpy.data.cameras:
        bpy.data.cameras.remove(block)

    for block in bpy.data.lights:
        bpy.data.lights.remove(block)

    for block in bpy.data.actions:
        bpy.data.actions.remove(block)

    bpy.ops.ptcache.free_bake_all()
    if bpy.context.scene.rigidbody_world is not None:
        bpy.ops.rigidbody.world_remove()

    import gc

    gc.collect()


def setup_camera(cam_loc=(0, -8, 4), cam_rot=(math.radians(60), 0, 0)):
    """
    Set up the camera.
    Args:
        cam_loc
        cam_rot
        video_len
        fps
    """
    cam_data = bpy.data.cameras.new("SceneCamera")
    cam_obj = bpy.data.objects.new("SceneCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = cam_loc
    cam_obj.rotation_euler = cam_rot
    bpy.context.scene.camera = cam_obj
    create_camera_animation(cam_obj)


def create_camera_animation(camera, target_loc=(0, 0, 2.5)):
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=target_loc)
    empty = bpy.context.object
    empty.name = "CameraTarget"

    camera.parent = empty

    total_frames = settings.VIDEO_LEN * settings.FPS
    bpy.context.scene.frame_end = total_frames

    for frame in [1, total_frames]:
        bpy.context.scene.frame_set(frame)

        if frame == 1:
            empty.rotation_euler = (0, 0, 0)
        else:
            empty.rotation_euler = (0, 0, math.radians(360))

        empty.keyframe_insert(data_path="rotation_euler", frame=frame)


def setup_light(light_type="SUN"):
    """
    使用单一方向光源（SUN）+ 适当的环境光，保证阴影方向统一且具有一定高光和层次。
    """
    # 主光源：模拟太阳光，固定方向，产生清晰的高光和阴影
    sun_data = bpy.data.lights.new(name="SunLight", type="SUN")
    # 略微降低直射光强度，减轻阴影对比度
    sun_data.energy = 6.0
    # 增大半影角，让阴影边缘更柔和、不那么“实”
    sun_data.angle = math.radians(5.0)

    sun_obj = bpy.data.objects.new(name="SunLight", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    # 把光源抬得更高，并稍微靠后一点，让阴影更规整、更接近俯视光
    sun_obj.location = (10.0, -15.0, 30.0)
    # 更接近从正上方斜射下来的光线，减小地面上的拉长阴影
    sun_obj.rotation_euler = (math.radians(70.0), 0.0, math.radians(35.0))

    # 略高一点的环境光，进一步抬高阴影区域亮度，让阴影不那么“死黑”
    bpy.context.scene.world.use_nodes = True
    world = bpy.context.scene.world
    env = world.node_tree.nodes.get("Background")
    if env is not None:
        env.inputs["Color"].default_value = (0.09, 0.09, 0.09, 1.0)
        env.inputs["Strength"].default_value = 1.5


def create_material(obj, color, mat_name):
    """
    Set up block's material.
    Args:
        obj: a blender object (block)
        color: string
        mat_name: string
    """
    whole_name = mat_name + color
    mat_params = MATERIALS.get(mat_name)
    mat = bpy.data.materials.new(name=whole_name)
    mat.use_nodes = True

    mat.node_tree.nodes.clear()
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    for key, value in mat_params.items():
        bsdf.inputs[key].default_value = value

    # 如果有与材质同名的贴图文件，则使用贴图作为 Base Color；
    # 否则退回到纯颜色（COLORS[color]）作为 Base Color。
    tex_node = None
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        project_root = os.path.dirname(script_dir)
        tex_path = os.path.join(project_root, "texture", f"{mat_name}.png")

        if os.path.exists(tex_path):
            img = bpy.data.images.load(tex_path)

            # 纹理坐标 + Mapping
            tex_coord = nodes.new(type="ShaderNodeTexCoord")
            tex_coord.location = (-800, 0)

            mapping = nodes.new(type="ShaderNodeMapping")
            mapping.location = (-500, 0)

            # 对于地面（WoodGround），只使用一整张贴图，且避免世界原点落在贴图的拼接交点上
            if obj.name == "WoodGround":
                # 半径约为 20，XY ∈ [-20, 20]，用 1/40 把它线性压缩到宽度 1
                s = 1.0 / 40.0
                mapping.inputs["Scale"].default_value[0] = s
                mapping.inputs["Scale"].default_value[1] = s
                mapping.inputs["Scale"].default_value[2] = 1.0
                # 把世界原点 (0,0) 映射到贴图内部 0.25,0.25 位置（而不是四等分的交点 0.5,0.5）
                mapping.inputs["Location"].default_value[0] = 0.25
                mapping.inputs["Location"].value[1] = 0.25
                mapping.inputs["Location"].value[2] = 0.0
                # 关闭重复平铺：超出 0~1 的区域使用边缘颜色，避免出现额外交界
                try:
                    tex_node.extension = "EXTEND"
                except Exception:
                    pass
            else:
                # 其他物体仍然使用适度重复的贴图细节
                mapping.inputs["Scale"].default_value[0] = 2.0
                mapping.inputs["Scale"].default_value[1] = 2.0
                mapping.inputs["Scale"].default_value[2] = 1.0

            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.location = (-200, 0)
            tex_node.image = img
            # 使用 Box 投影，可以减少在立方体上的拉伸和条纹感
            try:
                tex_node.projection = "BOX"
                tex_node.projection_blend = 0.25
            except Exception:
                pass

            # 使用 Object 坐标做“体积式”投影，比 Generated 更不容易出现方向性条纹
            links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
            links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])
    except Exception:
        # 贴图加载失败时，静默回退到纯颜色
        tex_node = None

    if tex_node is not None:
        # 贴图作为 Base Color
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = COLORS[color]

    # 略微降低粗糙度并增强高光，让表面更有光泽感
    try:
        if "Roughness" in bsdf.inputs:
            rough = bsdf.inputs["Roughness"].default_value
            bsdf.inputs["Roughness"].default_value = max(0.2, float(rough) * 0.8)
        if "Specular IOR Level" in bsdf.inputs:
            spec = bsdf.inputs["Specular IOR Level"].default_value
            bsdf.inputs["Specular IOR Level"].default_value = min(
                1.0, float(spec) + 0.1
            )
    except Exception:
        pass

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    mat.node_tree.update_tag()
    bpy.context.view_layer.update()

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    # 确保物体参与漫反射和高光、阴影计算
    try:
        obj.visible_diffuse = True
        obj.visible_glossy = True
        obj.visible_transmission = True
        obj.visible_shadow = True
        cycles_obj = obj.cycles
        cycles_obj.is_shadow_catcher = False
    except Exception:
        pass

    obj.data.update_tag()
    bpy.context.view_layer.update()


def create_ground():
    """
    创建用于物理模拟的斜坡地面和一整块木质地板。
    仅保留地面，不再在四周生成围墙。
    """
    bpy.ops.mesh.primitive_circle_add(
        vertices=100, radius=20, fill_type="TRIFAN", location=(0, 0, 0)
    )
    ground = bpy.context.object
    ground.name = "PhysicsGround"
    mesh = ground.data

    # 根据配置中的 DEGREE 给地面加一个倾斜角（固定朝 +x 方向抬起）。
    tilt_rad = math.radians(settings.DEGREE)
    ground.rotation_euler = (0.0, -tilt_rad, 0.0)

    bpy.context.view_layer.objects.active = ground
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = "PASSIVE"

    # 让物理地面只用于物理，不参与渲染
    ground.hide_render = True
    ground.hide_viewport = True

    # === 可见的“桌面”地板，使用塑料贴图 ===
    # 复制一份网格，作为真正渲染出来的桌面（大块贴图）
    wood_mesh = mesh.copy()
    wood_mesh.name = "WoodGroundMesh"
    wood_ground = bpy.data.objects.new("WoodGround", wood_mesh)
    bpy.context.scene.collection.objects.link(wood_ground)
    wood_ground.location = ground.location
    wood_ground.rotation_euler = ground.rotation_euler
    # 使用 plastic 材质，会自动优先加载 texture/plastic.png 作为大贴图
    create_material(wood_ground, "white", "plastic")
    bpy.context.view_layer.objects.active = wood_ground
    bpy.ops.object.shade_smooth()


def create_block_mesh(size):
    """
    Create a block mesh based on the size.
    Args:
        size: lenth, width and height
    """
    size_str = f"{size[0]:.1f}X{size[1]:.1f}X{size[2]:.1f}"
    mesh_name = f"BlockMesh_{size_str}"

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)

    scale_matrix = Matrix(
        ((size[0], 0, 0, 0), (0, size[1], 0, 0), (0, 0, size[2], 0), (0, 0, 0, 1))
    )
    bmesh.ops.transform(bm, matrix=scale_matrix, verts=bm.verts)

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def generate_a_block(block_data):
    """
    Generate a block based on block_data. Add material and physics.
    """
    index = block_data["index"]
    color = block_data["color"]
    mat_name = block_data["material"]
    size = block_data["size"]
    pos = block_data["position"]
    rot = block_data["rotation"]
    mesh = create_block_mesh(size)

    obj = bpy.data.objects.new(f"block_{index}", mesh)
    obj.location = Vector(pos)
    obj.rotation_euler = Euler(rot)
    create_material(obj, color, mat_name)
    bpy.context.scene.collection.objects.link(obj)

    # set_block_physics(obj)


def create_mesh(mesh_type, block_data=None):
    """
    Create object mesh.
    Args:
        mesh_type: 'PLANE' or 'BLOCK'
        block_data: if 'BLOCK'
    """
    if mesh_type == "PLANE":
        create_ground()
    elif mesh_type == "BLOCK":
        generate_a_block(block_data)


def setup_render(resolution_x=800, resolution_y=800, samples=128):
    """
    Set up basic render settings.
    Args:
        index: scene index
        resolution_x
        resolution_y
        samples
    """
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.cycles.samples = samples

    cycles = bpy.context.scene.cycles
    cycles.device = "GPU"
    # 开启适度的光线反弹和高光反射，提高整体立体感与材质细节
    cycles.max_bounces = 6
    cycles.diffuse_bounces = 2
    cycles.glossy_bounces = 3
    cycles.transmission_bounces = 2
    cycles.transparent_max_bounces = 4

    cycles.caustics_reflective = False
    cycles.caustics_refractive = False
    cycles.use_transparent_shadows = True

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = settings.VIDEO_LEN * settings.FPS

    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"

    bpy.context.scene.render.fps = settings.FPS


def set_block_physics(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = "ACTIVE"


def is_block_hitting_ground(loc):
    """
    根据方块在世界坐标中的位置，射线检测到物理地面，
    只关心是否击中，不再区分红/绿区域。
    返回 True / False。
    """
    ground = bpy.data.objects.get("PhysicsGround")
    if ground is None:
        return False

    # 使用 ground 自身的 ray_cast，避免被其他物体（塔块）挡住
    # 需要把射线转换到 ground 的局部坐标系
    origin_world = Vector((loc.x, loc.y, loc.z + 10.0))
    direction_world = Vector((0.0, 0.0, -1.0))

    inv_mat = ground.matrix_world.inverted()
    origin_local = inv_mat @ origin_world
    direction_local = (inv_mat.to_3x3() @ direction_world).normalized()

    success, _, _, _ = ground.ray_cast(origin_local, direction_local)
    return bool(success)


def no_physics_render(index, config_num_colors):
    # num_blocks = config_num_colors['yellow'] + config_num_colors['blue'] + config_num_colors['white']
    # for i in range(num_blocks):
    # obj = bpy.data.objects[f'block_{i}']
    # obj.rigid_body.type = 'PASSIVE'
    bpy.context.scene.render.filepath = settings.OUTPUT_PATH + f"/{index}.mp4"
    bpy.ops.render.render(animation=True, write_still=True)


def physics_render(index, ped_num, config):
    """
    Bake and render.
    """
    if bpy.context.scene.rigidbody_world is None:
        raise ValueError("No rigidbody_world!")

    num_blocks = config["Scene"]["num_blocks"]
    for i in range(num_blocks):
        obj = bpy.data.objects[f"block_{i}"]
        bpy.context.view_layer.objects.active = obj
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = "ACTIVE"

    rigidbody_world = bpy.context.scene.rigidbody_world
    rigidbody_world.point_cache.frame_start = 1
    rigidbody_world.point_cache.frame_end = settings.VIDEO_LEN * settings.FPS

    scene = bpy.context.scene

    # 可选：在物理模拟前渲染第一帧静态图（初始状态）
    if settings.SAVE_FIRST_FRAME_IMAGE:
        render = scene.render
        prev_filepath = render.filepath
        prev_file_format = render.image_settings.file_format
        prev_ffmpeg_format = getattr(render, "ffmpeg", None)

        scene.frame_set(1)
        render.image_settings.file_format = "PNG"
        render.filepath = settings.OUTPUT_PATH + f"/{index}_f_init.png"
        bpy.ops.render.render(animation=False, write_still=True)

        # 恢复原设置
        render.image_settings.file_format = prev_file_format
        render.filepath = prev_filepath
        if prev_ffmpeg_format is not None:
            render.ffmpeg.format = prev_ffmpeg_format.format

    bpy.ops.ptcache.bake_all(bake=True)

    # 在最后一帧获取每个方块的位置，统计有多少非底座方块最终“砸到地面”。
    # 不再区分红/绿区域，只关心是否发生了倒塌。
    hit_count = 0
    bpy.context.scene.frame_set(settings.VIDEO_LEN * settings.FPS)

    for i in range(num_blocks):
        obj = bpy.data.objects[f"block_{i}"]
        loc = obj.matrix_world.to_translation()

        # 跳过底座方块
        if i < ped_num:
            continue

        if is_block_hitting_ground(loc):
            hit_count += 1

    # colors 非空表示至少有一个非底座方块最终击中了地面，
    # 将其视为“塔发生了倒塌”；否则认为“未倒塌”。
    if hit_count == 0:
        collapse_state = "stable"  # 未倒塌
    else:
        collapse_state = "collapsed"  # 发生倒塌

    # 在控制台打印当前场景的二分类结果
    print(
        f"[Scene {index}] collapse_state = {collapse_state}, "
        f"hit_ground_blocks = {hit_count}"
    )

    # 如果需要保存最后一帧图像
    if settings.SAVE_LAST_FRAME_IMAGE:
        last_frame = settings.VIDEO_LEN * settings.FPS

        # 备份当前渲染设置
        render = scene.render
        prev_filepath = render.filepath
        prev_file_format = render.image_settings.file_format
        prev_ffmpeg_format = getattr(render, "ffmpeg", None)

        scene.frame_set(last_frame)
        render.image_settings.file_format = "PNG"
        render.filepath = settings.OUTPUT_PATH + f"/{index}_p_{collapse_state}.png"
        bpy.ops.render.render(animation=False, write_still=True)

        # 恢复原设置
        render.image_settings.file_format = prev_file_format
        render.filepath = prev_filepath
        if prev_ffmpeg_format is not None:
            render.ffmpeg.format = prev_ffmpeg_format.format

    # 如果配置关闭视频渲染，则只预测（以及可选地保存单帧图像）
    if not settings.RENDER_VIDEO:
        return collapse_state

    # 渲染整段视频
    scene.render.filepath = settings.OUTPUT_PATH + f"/{index}_p_{collapse_state}.mp4"
    scene.frame_set(1)
    bpy.ops.render.render(animation=True, write_still=True)
