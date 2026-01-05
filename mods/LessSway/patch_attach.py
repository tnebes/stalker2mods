import os
import sys
import re

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import patching_script_general as psg

# replace with your own paths
BASE_FILE = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\ItemPrototypes\AttachPrototypes.cfg'
PATCH_FILE = r'C:\dev\stalker2\mods\mods\LessSway\LessSway_P\Stalker2\Content\GameLite\GameData\ItemPrototypes\AttachPrototypes\AttachPrototypes_patch_LessSway.cfg'
EFFECTS = ["LessSwayX", "LessSwayY", "LessSwayTime"]
NESTED_PATH = ["Scope", "AimingEffects", "PlayerOnlyEffects"]

def main():
    if not os.path.exists(BASE_FILE):
        print(f"Base file not found: {BASE_FILE}")
        return

    print(f"Analyzing {os.path.basename(BASE_FILE)}...")
    with open(BASE_FILE, 'r', encoding='utf-8-sig') as f:
        base_content = f.read()
    
    tree = psg.get_inheritance_tree(BASE_FILE)
    
    print("Finding target structs...")
    all_structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', base_content, re.MULTILINE)
    
    all_final_patches = []
    
    for struct in all_structs:
        # Determine what we need to patch
        has_breath_in_chain = psg.check_property_in_chain(tree, base_content, struct, "CanHoldBreath")
        has_scope_in_chain = psg.check_node_in_chain(tree, base_content, struct, NESTED_PATH)
        
        if not (has_breath_in_chain or has_scope_in_chain):
            continue
            
        patch_props = {"CanHoldBreath": "true"} if has_breath_in_chain else None
        patch_nested_path = NESTED_PATH if has_scope_in_chain else None
        patch_values = EFFECTS if has_scope_in_chain else None
        
        all_final_patches.append(psg.generate_bpatch(struct, patch_nested_path, patch_values, patch_props))

    if all_final_patches:
        print(f"Writing {len(all_final_patches)} patches to {PATCH_FILE}...")
        os.makedirs(os.path.dirname(PATCH_FILE), exist_ok=True)
        # Overwrite file to ensure a clean state without duplicates
        with open(PATCH_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_final_patches))
        print("Done.")
    else:
        print("No patches generated.")

if __name__ == "__main__":
    main()
