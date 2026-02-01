import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

from src.patching.v2.difficulty.difficulty_patcher import patch_difficulty
from src.patching.v2.difficulty.better_difficulty.difficulty_values import DIFFICULTY_VALUES

MOD_NAME = "BetterDifficulty"
MOD_ROOT = r"C:\dev\stalker2\mods\mods\BetterDifficulty\BetterDifficulty_P"

if __name__ == "__main__":
    try:
        patch_difficulty(DIFFICULTY_VALUES, MOD_NAME, MOD_ROOT)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
