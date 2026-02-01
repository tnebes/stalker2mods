import os
import sys

# Add project root to sys.path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.patching.v2.api import load_configuration
from src.patching.v2.patcher import Patcher
from src.difficulty.difficulty_values import DIFFICULTY_VALUES

# Mapping indices to SID names in DifficultyPrototypes.cfg
DIFFICULTIES = ["Easy", "Medium", "Hard", "Stalker"]
CONFIG_REL_PATH = "DifficultyPrototypes.cfg"
MOD_ROOT = r"C:\dev\stalker2\mods\mods\BetterDifficulty\BetterDifficulty_P"

def run_patching():
    """
    Applies values from DIFFICULTY_VALUES to DifficultyPrototypes.cfg 
    and generates a BPATCH file for the BetterDifficulty mod.
    """
    print("Loading DifficultyPrototypes.cfg...")
    cfg = load_configuration(CONFIG_REL_PATH)
    
    modified_count = 0
    
    for i, diff_sid in enumerate(DIFFICULTIES):
        node = cfg.getNodeByName(diff_sid)
        if not node:
            print(f"Warning: Difficulty SID '{diff_sid}' not found in configuration.")
            continue
            
        print(f"Processing difficulty: {diff_sid}...")
        for key, values_list in DIFFICULTY_VALUES.items():
            if i < len(values_list):
                new_value = values_list[i]
                
                # We only apply the value if it's not None
                if new_value is not None:
                    # Check if it actually changed (optional, Patcher.generate_patch will handle it, 
                    # but setting it here ensures we mark it for the diff engine)
                    node[key] = new_value
                    modified_count += 1

    print(f"Applied {modified_count} values to the configuration model.")
    
    # Generate the BPATCH document
    print("Generating diff patch...")
    patcher = Patcher()
    patch_doc = patcher.generate_patch(CONFIG_REL_PATH, cfg.doc)
    
    # Save the patch following the Stalker 2 mod structure
    print(f"Saving patch to {MOD_ROOT}...")
    output_path = patcher.save_patch(
        mod_root=MOD_ROOT,
        mod_name="BetterDifficulty",
        patch_doc=patch_doc
    )
    
    print(f"Succefully generated patch at: {output_path}")

if __name__ == "__main__":
    try:
        run_patching()
    except Exception as e:
        print(f"Error during patching: {e}")
        sys.exit(1)
