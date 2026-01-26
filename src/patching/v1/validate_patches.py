import os
import sys
import re

# Default source dump path for validation
SOURCE_DUMP = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'

def validate_mod(mod_path, source_dump=SOURCE_DUMP):
    """
    Validates a mod directory for correct patch naming and placement.
    """
    print(f"--- Validating Mod: {mod_path} ---")
    if not os.path.isdir(mod_path):
        print(f"Error: {mod_path} is not a directory.")
        return False

    errors = 0
    total_files = 0

    # Walk through the mod directory
    for root, dirs, files in os.walk(mod_path):
        for file in files:
            if not file.lower().endswith(('.cfg', '.cfg.bin')) and '_patch_' not in file:
                continue
            
            total_files += 1
            full_path = os.path.join(root, file)
            
            # 1. Path Normalization - find GameData relative path
            # We look for "GameData" in the path to determine where the game structure starts
            parts = full_path.replace('\\', '/').split('/')
            try:
                gdata_idx = parts.index('GameData')
                rel_parts = parts[gdata_idx+1:]
                rel_path = "/".join(rel_parts)
            except ValueError:
                print(f"Skipping (not in GameData): {full_path}")
                continue

            # 2. Type Detection & Rule Validation
            # Rule A: Standard/Global Patch (OriginalFileName.cfg_patch_YourModName)
            if ".cfg_patch_" in file:
                original_filename = file.split(".cfg_patch_")[0] + ".cfg"
                # Standard patches must be in the same folder as original
                # So expected folder path is rel_parts[:-1]
                expected_original_rel = "/".join(rel_parts[:-1] + [original_filename])
                
                check_original_exists(source_dump, expected_original_rel, full_path, "Standard")
                
            # Rule B: Prototype Patch (OriginalFileName_patch_YourModName.cfg)
            elif "_patch_" in file and file.endswith(".cfg"):
                # Pattern: [OriginalFileName]_patch_[ModName].cfg
                match = re.search(r'^(.*)_patch_.*\.cfg$', file, re.IGNORECASE)
                if match:
                    original_name = match.group(1)
                    original_filename = original_name + ".cfg"
                    
                    # Prototype Rule: Must be in a subfolder named exactly OriginalName
                    # rel_parts example: ["ObjPrototypes", "GeneralNPCObjPrototypes", "GeneralNPCObjPrototypes_patch_Mod.cfg"]
                    # Expected parent folder: GeneralNPCObjPrototypes
                    if len(rel_parts) < 2 or rel_parts[-2].lower() != original_name.lower():
                        print(f"[FAIL] Prototype Folder Error: {file}")
                        print(f"      File: {full_path}")
                        print(f"      Expected parent folder: '{original_name}'")
                        errors += 1
                    
                    # Check if original exists. 
                    # Note: For prototypes, the original is ONE LEVEL UP from the patch.
                    # e.g. GameData/ObjPrototypes/GeneralNPCObjPrototypes.cfg
                    # Patch: GameData/ObjPrototypes/GeneralNPCObjPrototypes/GeneralNPCObjPrototypes_patch_Mod.cfg
                    expected_original_rel = "/".join(rel_parts[:-2] + [original_filename])
                    if not check_original_exists(source_dump, expected_original_rel, full_path, "Prototype"):
                        errors += 1

    print(f"\nScan complete. Files found: {total_files}, Errors: {errors}")
    return errors == 0

def check_original_exists(source_dump, rel_path, patch_full_path, patch_type):
    """Verifies the base file exists in the source dump."""
    original_full_path = os.path.join(source_dump, rel_path.replace('/', os.sep))
    # Note: Game uses .cfg.bin usually, but SDK/Dump uses .cfg
    if not os.path.exists(original_full_path):
        # Also check for .cfg.bin if .cfg doesn't exist
        bin_path = original_full_path + ".bin"
        if not os.path.exists(bin_path):
            print(f"[FAIL] {patch_type} Missing Original: {os.path.basename(patch_full_path)}")
            print(f"      Expected Original: {original_full_path} (or .bin)")
            return False
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_patches.py <mod_folder_path> [source_dump_path]")
        sys.exit(1)
    
    mod_dir = sys.argv[1]
    src_dir = sys.argv[2] if len(sys.argv) > 2 else SOURCE_DUMP
    
    success = validate_mod(mod_dir, src_dir)
    sys.exit(0 if success else 1)
