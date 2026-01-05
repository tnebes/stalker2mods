import os
import sys

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import patching_script_general as psg

# replace with your own paths
BASE_FILE = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\WeaponData\WeaponGeneralSetupPrototypes.cfg'
PATCH_FILE = r'C:\dev\stalker2\mods\mods\LessSway\LessSway_P\Stalker2\Content\GameLite\GameData\WeaponData\WeaponGeneralSetupPrototypes\WeaponGeneralSetupPrototypes_patch_LessSway.cfg'
EFFECTS = ["LessSwayX", "LessSwayY", "LessSwayTime"]
NESTED_PATH = ["AimingEffects", "PlayerOnlyEffects"]

def main():
    if not os.path.exists(BASE_FILE):
        print(f"Base file not found: {BASE_FILE}")
        return

    print(f"Analyzing {os.path.basename(BASE_FILE)}...")
    with open(BASE_FILE, 'r', encoding='utf-8-sig') as f:
        base_content = f.read()
        
    tree = psg.get_inheritance_tree(BASE_FILE)
    
    print("Finding inheritors of TemplateWeapon...")
    inheritors = psg.find_all_inheritors(tree, 'TemplateWeapon')
    
    target_structs = list(inheritors)
    if 'TemplateWeapon' not in target_structs:
        target_structs.append('TemplateWeapon')
    
    print(f"Applying filters to {len(target_structs)} structs...")
    
    all_final_patches = []
    for struct in target_structs:
        # User requirement: append IF AND ONLY IF node present in chain
        if psg.check_node_in_chain(tree, base_content, struct, NESTED_PATH):
            all_final_patches.append(psg.generate_bpatch(struct, NESTED_PATH, EFFECTS))
    
    if all_final_patches:
        print(f"Writing {len(all_final_patches)} patches to {PATCH_FILE}...")
        os.makedirs(os.path.dirname(PATCH_FILE), exist_ok=True)
        # Overwrite file to ensure a clean state
        with open(PATCH_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_final_patches))
        print("Done.")
    else:
        print("No patches needed.")

if __name__ == "__main__":
    main()
