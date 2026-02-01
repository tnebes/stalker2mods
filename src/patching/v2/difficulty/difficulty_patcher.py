import os
import sys

# Mapping indices to SID names in DifficultyPrototypes.cfg
DIFFICULTIES = ["Easy", "Medium", "Hard", "Stalker"]
CONFIG_REL_PATH = "DifficultyPrototypes.cfg"

def patch_difficulty(difficulty_values, mod_name, mod_root):
    """
    Applies values from difficulty_values to DifficultyPrototypes.cfg 
    and generates a BPATCH file for the specified mod.
    """
    # Import here to avoid circular imports if needed, though not strictly necessary here
    from src.patching.v2.api import load_configuration
    from src.patching.v2.patcher import Patcher

    print(f"Loading {CONFIG_REL_PATH} for {mod_name}...")
    cfg = load_configuration(CONFIG_REL_PATH)
    
    modified_count = 0
    
    for i, diff_sid in enumerate(DIFFICULTIES):
        node = cfg.getNodeByName(diff_sid)
        if not node:
            print(f"Warning: Difficulty SID '{diff_sid}' not found in configuration.")
            continue
            
        print(f"Processing difficulty: {diff_sid}...")
        for key, values_list in difficulty_values.items():
            if i < len(values_list):
                new_value = values_list[i]
                
                # We only apply the value if it's not None
                if new_value is not None:
                    node[key] = new_value
                    modified_count += 1

    print(f"Applied {modified_count} values to the configuration model.")
    
    # Generate the BPATCH document
    print("Generating diff patch...")
    patcher = Patcher()
    patch_doc = patcher.generate_patch(CONFIG_REL_PATH, cfg.doc)
    
    # Save the patch following the Stalker 2 mod structure
    print(f"Saving patch to {mod_root}...")
    output_path = patcher.save_patch(
        mod_root=mod_root,
        mod_name=mod_name,
        patch_doc=patch_doc
    )
    
    print(f"Successfully generated patch at: {output_path}")
    return output_path
