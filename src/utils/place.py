import bpy
import numpy as np
from src.core.heightmap import Heightmap
from src.core.block import Block
from src.core.scene import Scene

def place_blocks(scene, fall, red_or_green):
    """
    Place blocks in the scene.
    """
    blocks = scene.get_blocks()
    ground = scene.get_ground()
    heightmap = scene.get_heightmap()
    for block in blocks:
        position = None
        if fall:
            # Place blocks above the ground to let them fall
            position = (0, 0, 5 + block.get_index() * 2)
        else:
            # Place blocks on the ground using the heightmap
            if red_or_green == 'red':
                x, y = heightmap.get_random_position(color='red')
            elif red_or_green == 'green':
                x, y = heightmap.get_random_position(color='green')
            else:
                x, y = heightmap.get_random_position(color='any')
            position = (x, y, 0.5 + block.get_index() * 0.1)
        block.position = position
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
        obj = bpy.context.object
        obj.name = f"Block_{block.get_index()}"
        mat = bpy.data.materials.new(name=f"Material_{block.get_index()}")
        mat.diffuse_color = block.get_color() + (1.0,)
        obj.data.materials.append(mat)
        block.set_block_physics()

def generate_candidates(height_map):
    """基于高度图生成候选位置"""
    # 实现细节：寻找高度突变区域边缘
    # 返回 [(x, y, z)] 位置列表
    pass

def find_valid_position(height_map, block_size, existing_blocks):
    candidate_positions = generate_candidates(height_map)
    
    valid_positions = []
    for pos in candidate_positions:
        if not check_collision(pos, block_size, existing_blocks):
            valid_positions.append(pos)
    
    return min(valid_positions, key=lambda p: p[1]) if valid_positions else None

def check_collision(position, size, objects):
    for obj in objects:
        obj_pos = obj.location
        if (abs(position[0] - obj_pos.x) < (size[0] + obj.dimensions.x)/2 and
            abs(position[2] - obj_pos.z) < (size[2] + obj.dimensions.z)/2):
            return True
    return False
        
def analyze_collapse_direction(blocks):
    """分析倒塌方向 (物理模拟后调用)"""
    final_positions = [obj.location for obj in blocks]
    
    avg_x = sum(p.x for p in final_positions) / len(final_positions)
    return "red" if avg_x > 0 else "green"

