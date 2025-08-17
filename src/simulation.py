"""The main simulation module."""
import sys
import os
import argparse
import yaml
import random
import numpy as np
import bpy
from core.block import Block
from core.scene import Scene
import math

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# Load scene configuration and constants
def load_scene_config(yml_path):
    with open(yml_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

# Initialize the scene with attributes
def initialize_scene(config):
    num_blocks = config['Scene']['num_blocks']
    red_or_green = config['General']['red_or_green']
    ground = config['Scene']['ground']
    background = config['Scene']['background']
    scene = Scene()
    scene.initialize(num_blocks, red_or_green, ground, background)
    return scene

# Generate a list of blocks with attributes
def generate_blocks_data(config):
    blocks_data = []
    num_blocks = config['Scene']['num_blocks']
    color_dic = config['Block']['num_colors']
    size_dic = config['Block']['sizes']
    rot_range = config['Block']['rot_range']
    rot_range = [math.radius(rot_range[0]), math.radius(rot_range[1])]
    
    ped_num = random.randint(2, 5)
    for i in range(num_blocks):
        if i < ped_num:
            block_data = {
                'index' : i,
                'color' : random.choice([key for key in color_dic.keys() if color_dic[key] > 0]),
                'material' : config['Block']['material'],
                'size' : [0.5, 0.5, 1.5],
                'position' : (0, 0, 0),
                'rotation' : (0, 0, random.uniform(rot_range[0], rot_range[1]))
            }
        else:
            block_data = {
                'index' : i,
                'color' : random.choice([key for key in color_dic.keys() if color_dic[key] > 0]),
                'material' : config['Block']['material'],
                'size' : random.choice([key for key in size_dic.keys() if size_dic[key] > 0]),
                'position' : (0, 0, 0),
                'rotation' : (0, 0, random.uniform(rot_range[0], rot_range[1]))
            }
        color_dic[block_data['color']]-=1
        size_dic[block_data['size']]-=1
        blocks_data.append(block_data)
    return blocks_data



# Main method to run the simulation
def run_simulation(config_path, save_path):
    config = load_scene_config(config_path)
    
    num_scenes = config['General']['num_scenes']
    fall = config['General']['fall']
    red_or_green = config['General']['red_or_green']
    video_lenth = config['General']['video_length']
    video_fps = config['General']['video_fps']
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for i in range(num_scenes):
        scene = initialize_scene(config)
        scene.enable_rtx3090_rendering()
        
        blocks_data = generate_blocks_data(config)
        scene.build_tower(blocks_data)

        save_path = os.path.join(save_path, f"simulation_{i+1:04d}.mp4")
        scene.setup_render_settings(save_path)
        scene.render_animation()
        print(f"Simulation {i} completed successfully.")