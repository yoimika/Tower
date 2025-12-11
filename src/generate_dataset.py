import os
import subprocess
from typing import Dict, List

import yaml


def get_project_root() -> str:
    """返回工程根目录（包含 main.blend 的目录）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_cube_config(
    output_dir: str,
    num_blocks: int,
    seed: int = 42,
    video_len: int = 3,
    fps: int = 15,
) -> Dict:
    """
    构造一个只包含正方体方块的场景配置：
    - 所有方块尺寸统一为 (0.5, 0.5, 0.5)
    - 方块总数从外部传入（例如 4、5、6、...）
    - 斜面角度 DEGREE=0，只在水平桌面上建塔
    """
    # 简单按顺序平均分配 4 种颜色
    base_colors = ["yellow", "blue", "green", "red"]
    color_counts = {c: 0 for c in base_colors}
    for i in range(num_blocks):
        color = base_colors[i % len(base_colors)]
        color_counts[color] += 1

    config = {
        "General": {
            "SEED": seed,
            "INTERSECTION_THRESHOLD": 0.01,
            "FATNESS": 0.2,
            # 每个 yml 只生成若干个场景，你也可以改大一点
            "NUM_SCENES": 50,
            "VIDEO_LEN": video_len,
            "FPS": fps,
            "DEGREE": 0,
            "POINT": None,
            "PROJECTION_X": [-1.0, 3.0],
            "PROJECTION_Y": [-1.5, 1.5],
            "ROT_DISCRETE": False,
            # 输出目录形如 output/cubes_4, output/cubes_5, ...
            "OUTPUT_PATH": output_dir,
            "RENDER_VIDEO": False,
            # 全程导出 VIDEO_LEN * FPS 张 PNG 帧序列
            "SAVE_ALL_FRAMES_IMAGES": True,
            # 是否额外再保存首帧 / 末帧的单独 PNG（可以按需保留或关闭）
            "SAVE_LAST_FRAME_IMAGE": False,
            "SAVE_FIRST_FRAME_IMAGE": False,
            "STACK_ON_EXISTING_PROB": 0.5,
        },
        "Scene": {
            "num_blocks": num_blocks,
            "num_colors": color_counts,
            # 只用一种尺寸：正方体
            "sizes": {
                "(0.5, 0.5, 0.5)": num_blocks,
            },
            "rot_range": [0, 360],
            # 全部使用木材质，你可以按需改成 metal/stone 或混合
            "num_materials": {
                "wood": num_blocks,
            },
        },
    }
    return config


def write_yaml(path: str, config: Dict) -> None:
    """把配置写入 yml 文件。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)


def run_blender(blender_exe: str, project_root: str, config_path: str) -> None:
    """使用给定的 yml 配置调用 Blender + main.py 生成数据。"""
    main_blend = os.path.join(project_root, "main.blend")
    main_py = os.path.join(project_root, "src", "main.py")

    cmd = [
        blender_exe,
        "-b",
        main_blend,
        "-P",
        main_py,
        "--",
        config_path,
    ]

    print(f"\n=== 生成方块数 = {os.path.basename(config_path)} ===")
    print("命令：", " ".join(f'"{c}"' if " " in c else c for c in cmd))
    subprocess.run(cmd, cwd=project_root, check=True)


def main() -> None:
    """
    生成一组「只用正方体」的塔：
    - 方块总数从 4, 5, 6, ... 一直扫到 max_blocks（默认 20）
    - 对于每个方块总数 N：
        * 生成一个 tmp/cubes_N.yml
        * General.OUTPUT_PATH = output/cubes_N
        * 内部只包含 num_blocks=N、size=(0.5,0.5,0.5) 的配置
    """
    project_root = get_project_root()
    blender_exe = os.environ.get("BLENDER_PATH", "blender")

    # 你可以按需把 20 改成更大，比如 30、40
    min_blocks = 4
    max_blocks = 20

    tmp_dir = os.path.join(project_root, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    for n in range(min_blocks, max_blocks + 1):
        output_dir = os.path.join(project_root, "output", f"cubes_{n}")
        cfg = build_cube_config(output_dir=output_dir, num_blocks=n, seed=42 + n)
        cfg_path = os.path.join(tmp_dir, f"config_cubes_{n}.yml")
        write_yaml(cfg_path, cfg)

        print(f"写入配置：{cfg_path}")
        run_blender(blender_exe, project_root, cfg_path)

    print("全部正方体塔（从 4 块到 max_blocks）已生成完成。")


if __name__ == "__main__":
    main()
