import os
import re
import sys

# Add src to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import patching_script_general as psg
from patch_config import SOURCE_DUMP, get_mod_root

def run():
    print("--- Running LessShotgunRecoil Patching ---")
    mod_name = "LessShotgunRecoil"
    mod_root = get_mod_root(mod_name)
    patcher = psg.ModPatcher(SOURCE_DUMP, mod_root)
    
    weapon_rel_path = 'Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg'
    patcher.load_files([weapon_rel_path])
    
    filename = os.path.basename(weapon_rel_path)
    content = patcher.file_contents[filename]
    
    # Identify all weapons inheriting from TemplateShotgun
    inheritors = patcher.get_all_inheritors('TemplateShotgun')
    
    for s in inheritors:
        # Get the effective RecoilRadius for this struct
        struct_content = psg.get_struct_content(content, s)
        if not struct_content:
            continue
            
        # We need to find RecoilRadius. It's normally inside RecoilParams.
        # psg.get_value will find it anywhere in the struct content.
        recoil_val = psg.get_value(struct_content, 'RecoilRadius')
        
        # If not found in this specific struct definition, look up the inheritance tree
        if recoil_val is None:
            curr = s
            visited = set()
            while curr and curr not in visited:
                visited.add(curr)
                parent_name = patcher.global_tree.get(curr)
                if not parent_name:
                    break
                
                parent_content = psg.get_struct_content(content, parent_name)
                if parent_content:
                    recoil_val = psg.get_value(parent_content, 'RecoilRadius')
                    if recoil_val is not None:
                        break
                curr = parent_name
        
        # If we found a numeric recoil value, reduce it by 50%
        if recoil_val is not None and isinstance(recoil_val, (int, float)) and recoil_val > 0:
            new_recoil = recoil_val * 0.5
            # Use smart_add_patch to automatically find RecoilParams
            if patcher.smart_add_patch(filename, s, 'RecoilRadius', f"{new_recoil:.1f}", parent_node='RecoilParams'):
                print(f"Patched {s}: {recoil_val} -> {new_recoil:.1f}")
            else:
                print(f"Failed to smart patch {s}")
            
    patcher.save_all(mod_name)

if __name__ == "__main__":
    run()
