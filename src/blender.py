import sys
import os

project_root = "D:/Desktop/University/Research/Intuitive Physics/TowerTask"
sys.path.append(os.path.join(project_root, "src"))

from start_script import main

config_path = os.path.join(project_root, "configs", "config.yml")
save_path = os.path.join(project_root, "outputs")

sys.argv = ["blender", "--", "--config", config_path, "--save_path", save_path]
main()