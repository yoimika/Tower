import os
import subprocess
from typing import List


def get_project_root() -> str:
    """返回工程根目录（即包含 main.blend 的目录）。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_config_list(root: str) -> List[str]:
    """
    默认使用的配置文件列表。
    每个 yml 内部通过 General.NUM_SCENES 控制场景数量，
    四个配置各 250 个场景时，总量约为 1000 个样本。
    """
    return [
        os.path.join(root, "configs", "config_ds_wood_low_slope.yml"),
        os.path.join(root, "configs", "config_ds_mixed_medium_slope.yml"),
        os.path.join(root, "configs", "config_ds_tall_high_slope.yml"),
        os.path.join(root, "configs", "config_ds_stone_random_slope.yml"),
    ]


def run_blender_with_config(
    blender_exe: str, project_root: str, config_path: str
) -> None:
    """
    调用 Blender，使用给定的配置文件生成一批场景。

    参数:
        blender_exe: Blender 可执行文件路径或命令名（如 "blender" 或 "blender.exe"）。
        project_root: 工程根目录。
        config_path: 要使用的配置文件绝对路径。
    """
    main_blend = os.path.join(project_root, "main.blend")
    main_py = os.path.join(project_root, "src", "main.py")

    if not os.path.exists(main_blend):
        raise FileNotFoundError(f"找不到 main.blend：{main_blend}")
    if not os.path.exists(main_py):
        raise FileNotFoundError(f"找不到 src/main.py：{main_py}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"找不到配置文件：{config_path}")

    cmd = [
        blender_exe,
        "-b",
        main_blend,
        "-P",
        main_py,
        "--",
        config_path,
    ]

    print(f"\n=== 开始生成：{os.path.basename(config_path)} ===")
    print("命令：", " ".join(f'"{c}"' if " " in c else c for c in cmd))

    # 在工程根目录下执行，保证相对路径（如 OUTPUT_PATH）正确
    subprocess.run(cmd, cwd=project_root, check=True)
    print(f"=== 完成：{os.path.basename(config_path)} ===\n")


def main() -> None:
    """
    批量生成 TowerCollapse 数据集的脚本。

    - 使用多组 yml 配置，覆盖不同塔高度 / 层数 / 方块尺寸与材质组合。
    - 每组配置内部通过 General.NUM_SCENES 控制样本数量。
    - 生成结果包括：
        * 固定视角渲染的首帧 / 末帧 PNG
        * 每个场景对应的 *_meta.json（包含倒塌二分类标签、倒塌过程序列、每帧方块位姿）
        * 如在配置中开启 RENDER_VIDEO，则还会有 mp4 视频
    """
    project_root = get_project_root()

    # 优先从环境变量读取 Blender 路径，否则退回到 "blender"
    blender_exe = os.environ.get("BLENDER_PATH", "blender")

    # 使用默认的 4 组配置（共约 1000 个样本）
    configs = default_config_list(project_root)

    for cfg in configs:
        run_blender_with_config(blender_exe, project_root, cfg)

    print(
        "全部配置的数据生成完成。请在各自的 General.OUTPUT_PATH 目录下查看 PNG 与 *_meta.json。"
    )


if __name__ == "__main__":
    main()
