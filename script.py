import bpy
import math
import sys
import os
from mathutils import Vector, Euler
import bmesh
import yaml
import ast
import random
import numpy as np
from shapely.geometry import Polygon, box 

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

COLORS = {
    "red": [1, 0, 0, 1],
    "green": [0, 1, 0, 1],
    "blue": [0, 0, 1, 1],
    "yellow": [1, 1, 0, 1],
    "purple": [1, 0, 1, 1],
    "cyan": [0, 1, 1, 1],
    "orange": [1, 0.5, 0, 1],
    "white": [1, 1, 1, 1],
    "gray": [0.5, 0.5, 0.5, 1],
    "black": [0, 0, 0, 1]
    }

MATERIALS = {
    'wood': {
        'Roughness': 0.9,
        'Metallic': 0.05,
        'Specular': 0.5
    },
    'metal': {
        'roughness': 0.3,
        'metallic': 0.8,
        'specular': 0.5
    },
    'plastic': {
        'roughness': 0.5,
        'metallic': 0.1,
        'specular': 0.6
    },
    'glass': {
        'roughness': 0.02,
        'metallic': 0.0,
        'specular': 0.9,
        'transmission': 0.95, 
        'ior': 1.52  # Index of refraction for glass
    },
    'rubber': {
        'roughness': 0.8,
        'metallic': 0.0,
        'specular': 0.1
    },
    'ceramic': {
        'roughness': 0.1,
        'metallic': 0.0,
        'specular': 0.8
    }
}

"""Class for a heightmap."""
class Heightmap:
    def __init__(self, width, depth, resolution=0.5):
        self.width = width
        self.depth = depth
        self.resolution = resolution
        self.grid_x = int(width / resolution)
        self.grid_y = int(depth / resolution)
        self.height = np.zeros((self.grid_x, self.grid_y))
        self.occupancy = np.ones((self.grid_x, self.grid_y), dtype=float)

    def world_to_grid(self, x, y):
        """Convert world coordinates to grid indices."""
        grid_x = int((x + self.width / 2) / self.resolution)
        grid_y = int((y + self.depth / 2) / self.resolution)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        """Convert grid indices to world coordinates."""
        x = grid_x * self.resolution - self.width / 2
        y = grid_y * self.resolution - self.depth / 2
        return x, y
    
    def get_height(self, x, y):
        """Get the height at world coordinates (x, y)."""
        grid_x, grid_y = self.world_to_grid(x, y)
        if 0 <= grid_x < self.grid_x and 0 <= grid_y < self.grid_y:
            return self.height[grid_x, grid_y]
        else:
            return None
    
    def update_height(self, position, size, rotation, min_ratio=0.4):
        """Update the heightmap with a block at a given position and size.
        The block can only be placed if the support area ratio is sufficient.
        """
        polygon = self.get_polygon(position, size, rotation)

        min_x, min_y = self.world_to_grid(polygon.bounds[0], polygon.bounds[1])
        max_x, max_y = self.world_to_grid(polygon.bounds[2], polygon.bounds[3])

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                grid_min_x, grid_min_y = self.grid_to_world(x, y)
                grid_max_x, grid_max_y = self.grid_to_world(x + 1, y + 1)
                cell = box(grid_min_x, grid_min_y, grid_max_x, grid_max_y)
                
                intersection = cell.intersection(polygon)
                if not intersection.is_empty:
                    grid_area = self.resolution ** 2
                    inter_area = intersection.area
                    area_ratio = inter_area / grid_area
                    if area_ratio >= min_ratio:
                        self.height[x, y] += size[2]
                        self.occupancy[x, y] = area_ratio

        
    def get_polygon(self, position, size, rotation):
        """
        Calculate the support area for a block on the heightmap.
        Only when the ratio is enough, the block can be placed.
        """
        l, w = size[0], size[1]
        angle = rotation[2]

        # Calculate the corners of the block in world coordinates
        corners = [
            (position[0] + l/2 * np.cos(angle) - w/2 * np.sin(angle),
             position[1] + l/2 * np.sin(angle) + w/2 * np.cos(angle)),
            (position[0] + l/2 * np.cos(angle) + w/2 * np.sin(angle),
             position[1] + l/2 * np.sin(angle) - w/2 * np.cos(angle)),
            (position[0] - l/2 * np.cos(angle) + w/2 * np.sin(angle),
             position[1] - l/2 * np.sin(angle) - w/2 * np.cos(angle)),
            (position[0] - l/2 * np.cos(angle) - w/2 * np.sin(angle),
             position[1] - l/2 * np.sin(angle) + w/2 * np.cos(angle))
        ]

        # Create a polygon from the corners
        polygon = Polygon(corners)
        return polygon

    def get_valid_positions(self, size, flag):
        """Get all valid positions on the heightmap."""
        valid_positions = []
        if flag:
            for _ in range(5):
                x = np.random.uniform(-1, 1)
                y = np.random.uniform(-1, 1)
                position = (x, y, 0)
                valid_positions.append(position)
        else:
            for gx in range(self.grid_x):
                for gy in range(self.grid_y):
                    if self.height[gx, gy]!=0:#self.occupancy[gx, gy] >= 0.4 and self.occupancy[gx, gy] < 1.0:
                        x, y = self.grid_to_world(gx, gy)
                        position = (x + np.random.uniform(-self.resolution, self.resolution),
                                    y + np.random.uniform(-self.resolution, self.resolution),
                                    self.height[gx, gy])
                        valid_positions.append(position)
        print(len(valid_positions))
        return valid_positions

class CollisionDetector:
    def __init__(self):
        pass
    
    def get_block_vertices(self, position, size, rotation):
        """
        Get the 8 vertices of a block given its position, size, and rotation.
        """
        l, w, h = size
        half_l = l / 2
        half_w = w / 2
        half_h = h / 2
        
        # Create rotation matrix from Euler angles
        rotation_matrix = Euler(rotation, 'XYZ').to_matrix().to_4x4()
        
        # 8 vertices in local space
        local_vertices = [
            Vector(( half_l,  half_w,  half_h)),
            Vector(( half_l,  half_w, -half_h)),
            Vector(( half_l, -half_w,  half_h)),
            Vector(( half_l, -half_w, -half_h)),
            Vector((-half_l,  half_w,  half_h)),
            Vector((-half_l,  half_w, -half_h)),
            Vector((-half_l, -half_w,  half_h)),
            Vector((-half_l, -half_w, -half_h))
        ]
        
        # apply rotation and translation to get world coordinates
        world_vertices = []
        for vertex in local_vertices:
            rotated_vertex = rotation_matrix @ vertex

            world_vertex = Vector(position) + rotated_vertex
            world_vertices.append(world_vertex)
        
        return world_vertices
    
    def get_block_faces(self, vertices):
        """
        Get the faces of a block given its vertices.
        Each face is represented by a list of vertices.
        """
        faces = [
            [0, 1, 3, 2],  
            [4, 5, 7, 6],  
            [0, 4, 6, 2],  
            [1, 5, 7, 3],  
            [0, 1, 5, 4],  
            [2, 3, 7, 6]   
        ]
        
        return [[vertices[i] for i in face] for face in faces]
    
    def separating_axis_theorem(self, vertices1, vertices2):
        """
        Check for collision between two sets of vertices using the Separating Axis Theorem (SAT).
        Returns True if there is a collision, False otherwise.
        """
        # get all possible separating axes
        normals = self.get_all_separating_axes(vertices1, vertices2)
        
        # check each axis
        for normal in normals:
            min1, max1 = self.project_vertices(vertices1, normal)
            min2, max2 = self.project_vertices(vertices2, normal)
            
            if max1 <= min2 or max2 <= min1:
                return False
        # If no separating axis found, there is a collision
        return True
    
    def get_all_separating_axes(self, vertices1, vertices2):
        """
        Get all possible separating axes for two sets of vertices.
        This includes face normals and edge cross products.
        """
        faces1 = self.get_block_faces(vertices1)
        normals1 = [self.get_face_normal(face) for face in faces1]
        
        faces2 = self.get_block_faces(vertices2)
        normals2 = [self.get_face_normal(face) for face in faces2]
        
        edge_normals = []
        for i in range(len(faces1)):
            for j in range(len(faces2)):
                edges1 = self.get_face_edges(faces1[i])
                edges2 = self.get_face_edges(faces2[j])
                
                for edge1 in edges1:
                    for edge2 in edges2:
                        cross = edge1.cross(edge2)
                        if cross.length > 0.001:  # To avoid zero-length normals
                            edge_normals.append(cross.normalized())
        
        all_normals = normals1 + normals2 + edge_normals
        
        unique_normals = []
        seen = set()
        for normal in all_normals:
            # Round to avoid floating point precision issues
            key = (round(normal.x, 3), round(normal.y, 3), round(normal.z, 3))
            if key not in seen:
                seen.add(key)
                unique_normals.append(normal)
        
        return unique_normals
    
    def get_face_normal(self, face_vertices):
        """
        Calculate the normal vector of a face given its vertices.
        The face is defined by three vertices.
        """
        v0 = face_vertices[0]
        v1 = face_vertices[1]
        v2 = face_vertices[2]
        
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        normal = edge1.cross(edge2).normalized()
        return normal
    
    def get_face_edges(self, face_vertices):
        """
        Get the edges of a face defined by its vertices.
        Each edge is represented as a vector from one vertex to the next.
        """
        edges = []
        n = len(face_vertices)
        for i in range(n):
            j = (i + 1) % n
            edge = face_vertices[j] - face_vertices[i]
            edges.append(edge)
        return edges
    
    def project_vertices(self, vertices, axis):
        """
        Project the vertices onto a given axis and return the min and max values.
        The axis should be a normalized vector.
        """
        min_val = float('inf')
        max_val = float('-inf')
        
        for vertex in vertices:
            projection = vertex.dot(axis)
            
            if projection < min_val:
                min_val = projection
            if projection > max_val:
                max_val = projection
        
        return min_val, max_val
    
    def check_block_collision(self, existing_blocks, new_position, new_size, new_rotation):
        """
        Check if a new block collides with existing blocks in the scene.
        """
        new_vertices = self.get_block_vertices(new_position, new_size, new_rotation)
        
        for block in existing_blocks:
                
            existing_vertices = self.get_block_vertices(
                block['position'], 
                block['size'], 
                block['rotation']
            )
            
            if self.separating_axis_theorem(new_vertices, existing_vertices):
                return True  
        
        return False  


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_camera(location=(0, -10, 5), rotation=(1.2, 0, 0)):
    cam_data = bpy.data.cameras.new('SceneCamera')
    cam_obj = bpy.data.objects.new('SceneCamera', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = location
    cam_obj.rotation_euler = rotation
    bpy.context.scene.camera = cam_obj
    create_camera_animation(cam_obj)

def create_camera_animation(camera):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    empty = bpy.context.object
    empty.name = "CameraTarget"

    camera.parent = empty

    total_frames = 6*30
    bpy.context.scene.frame_end = total_frames

    for frame in [1, total_frames]:
        bpy.context.scene.frame_set(frame)

        if frame == 1:
            empty.rotation_euler = (0, 0, 0)
        else:
            empty.rotation_euler = (0, 0, math.radians(360))

        empty.keyframe_insert(data_path="rotation_euler", frame=frame)

def setup_light(light_type='AREA', location=(0, 0, 0), energy=5000.0, color=(1, 1, 1), radius=50.0, shape='DISK'):
    light_data = bpy.data.lights.new(name='SceneLight', type=light_type)
    light_data.energy = energy
    light_data.color = color
    light_data.size = radius
    light_data.shape = shape
    light_data.cycles.cast_shadow = False
    light_obj = bpy.data.objects.new(name='SceneLight', object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = location

    light_positions = [
            (10, 10, 10),   
            (-10, 10, 10),  
            (10, -10, 10),  
            (-10, -10, 10), 
            (0, 0, 20)      
        ]
    for i, pos in enumerate(light_positions):
        light_data = bpy.data.lights.new(name=f"FillLight_{i}", type = light_type)
        light_data.size = 5.0
        light_data.energy = 1000.0
        light_data.cycles.cast_shadow = False
        light_obj = bpy.data.objects.new(name=f"FillLight_{i}", object_data=light_data)
        bpy.context.scene.collection.objects.link(light_obj)
        light_obj.location = pos
    
    light_data = bpy.data.lights.new(name="GroundReflection", type=light_type)
    light_data.size = 10.0
    light_data.energy = 800.0
    light_data.cycles.cast_shadow = False
    light_obj = bpy.data.objects.new(name="GroundReflection", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = (0, 0, -5)
    light_obj.rotation_euler = (math.pi, 0, 0)

    bpy.context.scene.world.use_nodes = True
    env = bpy.context.scene.world.node_tree.nodes['Background']
    env.inputs['Color'].default_value = (0, 0, 0, 1)

def create_material(obj, color, mat_name):
    exist_mat = bpy.data.materials.get(mat_name)
    if not exist_mat:
        mat_params = MATERIALS.get(mat_name)
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        mat.node_tree.nodes.clear()

        bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        for key, value in mat_params.items():
            bsdf.inputs[key].default_value = value
        bsdf.inputs['Base Color'].default_value = COLORS[color]

        output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
        obj.data.materials.append(mat)
    else:
        obj.data.materials.append(exist_mat)




def create_red_green_ground():
    bpy.ops.mesh.primitive_circle_add(vertices=100, radius=10, fill_type='TRIFAN', location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "RedGreenGround"
    mesh = ground.data

    vcol_layer = mesh.vertex_colors.new(name="Col")
    for poly in mesh.polygons[:len(mesh.polygons)//2]:
        for i in poly.loop_indices:
            vcol_layer.data[i].color = COLORS['red']
    for poly in mesh.polygons[len(mesh.polygons)//2:]:
        for i in poly.loop_indices:
            vcol_layer.data[i].color = COLORS['green']

    mat = bpy.data.materials.new(name="RedGreenMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    vcol_node = nodes.new(type='ShaderNodeVertexColor')
    vcol_node.layer_name = "Col"

    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(vcol_node.outputs['Color'], output.inputs['Surface'])

    ground.data.materials.append(mat)
    bpy.ops.object.shade_smooth()

def create_block_mesh(size):
    size_str = f"{size[0]:.1f}X{size[1]:.1f}X{size[2]:.1f}"
    mesh_name = f"BlockMesh_{size_str}"

    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    L, W, H = size
    bm = bmesh.new()

    v1 = bm.verts.new((L/2, W/2, H))
    v2 = bm.verts.new((L/2, -W/2, H))
    v3 = bm.verts.new((-L/2, -W/2, H))
    v4 = bm.verts.new((-L/2, W/2, H))
    v5 = bm.verts.new((L/2, W/2, 0))
    v6 = bm.verts.new((L/2, -W/2, 0))
    v7 = bm.verts.new((-L/2, -W/2, 0))
    v8 = bm.verts.new((-L/2, W/2, 0))
    bm.faces.new((v1, v2, v3, v4))
    bm.faces.new((v8, v7, v6, v5)) 
    bm.faces.new((v1, v5, v6, v2))
    bm.faces.new((v3, v2, v6, v7))
    bm.faces.new((v4, v3, v7, v8))
    bm.faces.new((v4, v1, v8, v5))
        
    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def generate_a_block(block_data):
    index = block_data['index']
    color = block_data['color']
    mat_name = block_data['material']
    size = block_data['size']
    pos = block_data['position']
    rot = block_data['rotation']
    mesh = create_block_mesh(size)
    obj = bpy.data.objects.new(f"block_{index}",mesh)
    obj.location = Vector(pos)
    obj.rotation_euler = Euler(rot)
    create_material(obj, color, mat_name)
    bpy.context.scene.collection.objects.link(obj)


def create_mesh(mesh_type, block_data=None):
    if mesh_type == 'PLANE':
        create_red_green_ground()
    elif mesh_type == 'BLOCK':
        generate_a_block(block_data)

def setup_render(resolution_x=800, resolution_y=800, samples=128):
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    bpy.context.scene.cycles.samples = samples

def get_block_position(existing_blocks, heightmap, collisiondetector, size, flag, new_rot):
    valid_positions = heightmap.get_valid_positions(size, flag)
    if not valid_positions:
        raise ValueError("No valid positions available for the block.")
    while valid_positions:
        position = random.choice(valid_positions)
        valid_positions.remove(position)
        if not collisiondetector.check_block_collision(existing_blocks, position, size, new_rot):
            heightmap.update_height(position, size, new_rot)
            return position
    raise ValueError("No valid position found for the block after checking all options.")

def generate_blocks_data(config, heightmap, collisiondetector):
    blocks_data = []
    num_blocks = 17#config['Scene']['num_blocks']
    color_dic = {"yellow": 7, "blue": 9, "white": 1}#config['Block']['num_colors']
    size_dic = {(0.5, 0.5, 1.5): 8, (1.5, 0.5, 0.5): 9}#config['Block']['sizes']
    rot_range = [0, 90, 180, 270]#config['Block']['rot_range']
    rot_range = [math.radians(rot_range[0]), math.radians(rot_range[1]),math.radians(rot_range[2]),math.radians(rot_range[3])]
    mat = 'wood'
    
    ped_num = random.randint(2, 5)
    for i in range(num_blocks):
        if i < ped_num:
            new_rotation = (0,0, random.choice(rot_range))#(0, 0, random.uniform(rot_range[0], rot_range[1]))
            block_data = {
                'index' : i,
                'color' : random.choice([key for key in color_dic.keys() if color_dic[key] > 0]),
                'material' : mat,#config['Block']['material'],
                'size' : (0.5, 0.5, 1.5),
                'position' : get_block_position(blocks_data, heightmap, collisiondetector, (0.5, 0.5, 1.5), 1, new_rotation),
                'rotation' : new_rotation
            }
        else:
            new_size = random.choice([key for key in size_dic.keys() if size_dic[key] > 0])
            new_rotation = (0,0, random.choice(rot_range))#(0, 0, random.uniform(rot_range[0], rot_range[1]))
            block_data = {
                'index' : i,
                'color' : random.choice([key for key in color_dic.keys() if color_dic[key] > 0]),
                'material' : mat,#config['Block']['material'],
                'size' : new_size,
                'position' : get_block_position(blocks_data, heightmap, collisiondetector, new_size, 0, new_rotation),
                'rotation' : new_rotation
            }
        color_dic[block_data['color']]-=1
        size_dic[block_data['size']]-=1
        blocks_data.append(block_data)
    return blocks_data

def load_scene_config(yml_path='configs/config.yml'):
    with open(yml_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    path = r'D:\Desktop\University\Research\Intuitive_Physics\TowerTask\configs\config.yml'
    config = load_scene_config(path)
    heightmap = Heightmap(20, 20, 0.5)
    collisiondetector = CollisionDetector()
    blocks_data = generate_blocks_data(config, heightmap, collisiondetector)    
    clear_scene()
    setup_render()

    create_mesh('PLANE')

    for block_data in blocks_data:
        create_mesh('BLOCK', block_data)

    setup_camera()
    setup_light()
    print("Finish creating the scene.")

if __name__=="__main__":
    main()

