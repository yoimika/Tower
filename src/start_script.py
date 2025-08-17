"""Blender simulation start script."""
import sys
import os
import bpy

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

def main():
    argv = sys.argv
    if "--" not in argv:
        argv = []
    else:
        argv = argv[argv.index("--") + 1:]

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='../configs/config.yml', help='Path to the configuration file')
    parser.add_argument('--save_path', type=str, default='../outputs/', help='Path to save the simulation results')
    args = parser.parse_args(argv)

    from simulation import run_simulation

    run_simulation(args.config, args.save_path)

if __name__ == "__main__":
    main()