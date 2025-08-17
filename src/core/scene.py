import bpy
import math
import random
from bpy.props import (
    PointerProperty,
    CollectionProperty,
    IntProperty,
    FloatVectorProperty,
    StringProperty,
)
from bpy.types import Scene as BaseScene
from mathutils import Vector
from constants import COLORS
from block import Block
from heightmap import Heightmap
from utils.collision_check import CollisionDetector

SEED = 42
random.seed(SEED)

"""Classes for the Scene."""
class Scene(BaseScene):
    heightmap = Heightmap(width=20, depth=20, resolution=0.5)
    collision_detector = CollisionDetector()

    blocks: CollectionProperty(type=Block)
    
    ground: PointerProperty(type=bpy.types.Object)
    background: PointerProperty(type=bpy.types.Object)
    camera: PointerProperty(type=bpy.types.Object)
    light: PointerProperty(type=bpy.types.Object)
    
    num_blocks: IntProperty()
    collapse_direction: StringProperty()

    def initialize(self, num_blocks, red_or_green='red', ground='default', background='default'):
        """
        Initialize the scene for static elements.
        """
        if ground == 'default':
            self.ground = self.create_red_green_ground()
        if background == 'default':
            self.background = self.create_black_background()
        self.light = self.setup_lighting()
        self.camera = self.setup_camera()
        self.num_blocks = num_blocks
        self.collapse_direction = red_or_green

    def reset_tower(self):
        """
        Remove all blocks from the scene.
        """
        blocks_to_remove = []
        for block in self.blocks:
            if block.blender_object and block.blender_object.name in bpy.data.objects:
                blocks_to_remove.append(block.blender_object)

        if blocks_to_remove:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in blocks_to_remove:
                obj.select_set(True)
            bpy.ops.object.delete()
        
        self.blocks.clear()
    
    def build_tower(self, blocks_data):
        """
        Build the tower with the given blocks data.
        """
        self.reset_tower()
        
        for block_data in blocks_data:
            placed = False
            attempts = 0
            max_attempts = 100
            new_block = self.blocks.add()

            new_block.index = block_data['index']
            new_block.color = block_data['color']
            new_block.material_type = block_data['material']
            new_block.size = Vector(block_data['size'])
            new_block.position = Vector(block_data['position'])
            new_block.rotation = Vector(block_data['rotation'])

            new_block.generate_a_block(self)
            new_block.blender_object.rigid_body.enabled = False
            
            while not placed and attempts < max_attempts:
                position = self.get_block_position(new_block)
                if not self.collision_detector.check_block_collision(self, position, new_block.size, new_block.rotation):
                    new_block.position = Vector(position)
                    new_block.blender_object.location = Vector(position)
                    new_block.blender_object.rotation_euler = Vector(new_block.rotation)
                    
                    self.heightmap.update_height(position, new_block.size, new_block.rotation)

                    placed = True
                attempts += 1
            
            if not placed:
                raise ValueError(f"Could not place block {new_block.index} after {max_attempts} attempts.")            
            
            

    def get_block_position(self, new_block):
        valid_positions = self.heightmap.get_valid_positions(new_block.size)
        if not valid_positions:
            raise ValueError("No valid positions available for the block.")
        while valid_positions:
            position = random.choice(valid_positions)
            valid_positions.remove(position)
            if not self.collision_check(position):
                return position
        raise ValueError("No valid position found for the block after checking all options.")
    





    def create_red_green_ground(self):
        """
        Create a red-green ground for the scene.
        """
        bpy.ops.mesh.primitive_circle_add(vertices=100, radius=10, fill_type='TRIFAN', location=(0, 0, 0))
        ground = bpy.context.object
        ground.name = "RedGreenGround"
        mesh = ground.data

        vcol_layer = mesh.vertex_colors.new(name="Col")

        for poly in mesh.polygons[:len(mesh.polygons)//2]:
            for loop_index in poly.loop_indices:
                vcol_layer.data[loop_index].color = COLORS['red']

        for poly in mesh.polygons[len(mesh.polygons)/2:]:
            for loop_index in poly.loop_indices:
                vcol_layer.data[loop_index].color = COLORS['green']
        
        mat = bpy.data.materials.new(name="RedGreenMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        vcol_node = nodes.new(type='ShaderNodeVertexColor')
        vcol_node.layer_name = "Col"

        output = nodes.new(type='ShaderNodeOutputMaterial')
        links.new(vcol_node.outputs[0], output.inputs[0])

        ground.data.materials.append(mat)

        bpy.ops.object.shade_smooth()
        return ground
    
    def create_black_background(self):
        """
        Create a black background for the scene.
        """
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -10))
        background = bpy.context.object
        background.name = "BlackBackground"
        
        mat = bpy.data.materials.new(name="BlackMaterial")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        
        background.data.materials.append(mat)
        return background
    
    def setup_lighting(self):
        for obj in bpy.data.objects:
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj)
        
        bpy.ops.object.light_add(
            type='AREA', 
            location=(0, 0, 0),
            radius=50.0  
        )
        main_light = bpy.context.object
        main_light.name = "MainEnvLight"
        main_light.data.energy = 5000.0  
        main_light.data.shape = 'DISK'  
        
        main_light.data.cycles.cast_shadow = False
        
        light_positions = [
            (10, 10, 10),   
            (-10, 10, 10),  
            (10, -10, 10),  
            (-10, -10, 10), 
            (0, 0, 20)      
        ]
        
        for i, pos in enumerate(light_positions):
            bpy.ops.object.light_add(
                type='AREA', 
                location=pos,
                radius=5.0
            )
            light = bpy.context.object
            light.name = f"FillLight_{i}"
            light.data.energy = 1000.0
            light.data.cycles.cast_shadow = False  
        
        bpy.ops.object.light_add(
            type='AREA', 
            location=(0, 0, -5),
            rotation=(math.pi, 0, 0),  
            radius=10.0
        )
        ground_light = bpy.context.object
        ground_light.name = "GroundReflection"
        ground_light.data.energy = 800.0
        ground_light.data.cycles.cast_shadow = False
        
        world = bpy.data.worlds.new("UniformWorld")
        self.world = world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        
        nodes.clear()
        
        background = nodes.new(type='ShaderNodeBackground')
        background.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  
        background.inputs['Strength'].default_value = 1.0  
        
        output = nodes.new(type='ShaderNodeOutputWorld')
        links.new(background.outputs['Background'], output.inputs['Surface'])
        
        world.light_settings.use_ambient_occlusion = False
        
        return main_light

    def setup_camera(self, location=(0, -10, 5), rotation=(1.2, 0, 0), lens=50):
        """
        Set up the camera for the scene.
        """
        # Clear existing cameras
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='CAMERA')
        bpy.ops.object.delete()

        # Create a new camera
        bpy.ops.object.camera_add(location=location, rotation=rotation)
        camera = bpy.context.object
        camera.name = "Camera"
        
        # Set camera properties
        camera.data.lens = lens
        
        # Set the camera as the active camera for the scene
        bpy.context.scene.camera = camera
        self.camera = camera

        self.create_camera_animation(camera)
        return camera

    def create_camera_animation(self, camera, duration=6, fps=30):
        """
        Create a simple camera animation.
        """
        # Create an empty object to serve as the camera target
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        empty = bpy.context.object
        empty.name = "CameraTarget"

        camera.parent = empty

        total_frames = duration * fps
        bpy.context.scene.frame_end = total_frames

        for frame in [1, total_frames]:
            bpy.context.scene.frame_set(frame)

            if frame == 1:
                empty.rotation_euler = (0,0,0)
            else:
                empty.rotation_euler = (0,0, math.radians(360))

            empty.keyframe_insert(data_path="rotation_euler", frame=frame)

        return empty

    def enable_rtx3090_rendering(self):
        self.render.engine = 'CYCLES'
        prefs = bpy.context.preferences
        cycles_prefs = prefs.addons['cycles'].preferences

        cycles_prefs.compute_device_type = 'OPTIX'

        cycles_prefs.refresh_devices()

        enabled_devices = []
        for device in cycles_prefs.devices:
            if 'RTX 3090' in device.name or device.type == 'OPTIX':
                device.use = True
                enabled_devices.append(device.name)

        bpy.context.scene.cycles.device = 'GPU'

        if not enabled_devices:
            raise RuntimeError("No RTX!")
        
        bpy.context.scene.cycles.use_adaptive_sampling = True
        bpy.context.scene.cycles.adaptive_threshold = 0.01
        bpy.context.scene.cycles.samples = 64
        bpy.context.scene.cycles.adaptive_min_samples = 32

        bpy.context.scene.cycles.use_auto_tile = True
        bpy.context.scene.cycles.tile_size = 256
        bpy.context.scene.cycles.texture_limit = 'OFF'

        bpy.context.scene.render.tile_x = 256
        bpy.context.scene.render.tile_y = 256
        bpy.context.scene.cycles.use_preview_adaptive_sampling = True
        bpy.context.scene.cycles.preview_adaptive_threshold = 0.1
        bpy.context.scene.cycles.use_persistent_data = True
        print("RTX.")



        

        


    def setup_render_settings(self, output_path):
        self.frame_end = 6 * 30
        
        self.render.engine = 'CYCLES'
        
        self.cycles.max_bounces = 0 
        self.cycles.diffuse_bounces = 0
        self.cycles.glossy_bounces = 0
        self.cycles.transmission_bounces = 0
        self.cycles.volume_bounces = 0
        
        self.cycles.samples = 32  
        
        self.cycles.use_shadows = False
        self.cycles.caustics_reflective = False
        self.cycles.caustics_refractive = False
        
        self.render.film_transparent = False
        self.view_settings.view_transform = 'Standard'
        self.view_settings.look = 'None'
        self.view_settings.exposure = 0.0
        self.view_settings.gamma = 1.0
        
        self.render.resolution_x = 800
        self.render.resolution_y = 800

        self.render.fps = 30
        self.render.fps_base = 1.0

        self.render.image_settings.file_format = 'FFMPEG'
        self.render.ffmpeg.format = 'MPEG4'
        self.render.ffmpeg.codec = 'H264'
        self.render.ffmpeg.constant_rate_factor = 'MEDIUM'
        self.render.ffmpeg.audio_codec = 'NONE'

        self.render.filepath = output_path

    def render_animation(self):
        if not self.camera:
            raise ValueError("No camera!")
        
        bpy.context.scene.camera = self.camera
        print("Start rendering.")
        bpy.ops.render.render(animation=True)
        print("Finish rendering.")

    def setup_physics_engine(self, duration=6, fps=30):
        """
        Set up the physics engine for the scene.
        This function initializes the physics properties of the blocks and the ground.
        """
        self.use_gravity = True
        self.gravity = (0, 0, -9.81)  # Set gravity

        if not self.rigidbody_world:
            bpy.ops.rigidbody.world_add()

        self.rigidbody_world.point_cache.frame_start = 1
        self.rigidbody_world.point_cache.frame_end = duration * fps +100

        for block in self.blocks:
            block.set_block_physics()  
        self.setup_ground_physics()  

    def setup_ground_physics(self):
        """
        Set up the physics properties for the ground.
        """
        bpy.context.view_layer.objects.active = self.ground
        if not self.ground.rigid_body:
            bpy.ops.rigidbody.object_add()
        
        rb = self.ground.rigid_body
        rb.type = 'PASSIVE'
        rb.friction = 0.5
        rb.restitution = 0.5
        rb.collision_shape = 'MESH'
        rb.use_margin = True
        rb.collision_margin = 0.001
        rb.use_deactivation = False
