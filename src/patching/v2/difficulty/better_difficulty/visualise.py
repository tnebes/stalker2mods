import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from src.patching.v2.difficulty.difficulty_mod_visualiser import run_visualisation

# Configuration and Paths
ORIGINAL_CFG_PATH = r"C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\DifficultyPrototypes.cfg"
PATCH_CFG_PATH = r"C:\dev\stalker2\mods\mods\BetterDifficulty\BetterDifficulty_P\Stalker2\Content\GameLite\GameData\DifficultyPrototypes\DifficultyPrototypes_patch_BetterDifficulty.cfg"
MOD_NAME = "BetterDifficulty"
OUTPUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comparison.html")

if __name__ == "__main__":
    try:
        run_visualisation(ORIGINAL_CFG_PATH, PATCH_CFG_PATH, MOD_NAME, OUTPUT_HTML)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
