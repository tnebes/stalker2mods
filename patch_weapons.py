import os
import patching_script_general as psg

# Constants
BASE_DIR = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\LessSway\LessSway_P\Stalker2\Content\GameLite\GameData'

NESTED_PATH = ["AimingEffects", "PlayerOnlyEffects"]
EFFECTS = ["LessSwayX", "LessSwayY", "LessSwayTime"]

def main():
    patcher = psg.ModPatcher(BASE_DIR, MOD_ROOT)
    # Weapons file
    weapon_rel_path = 'WeaponData/WeaponGeneralSetupPrototypes.cfg'
    patcher.load_files([weapon_rel_path])
    
    weapon_file = os.path.basename(weapon_rel_path)
    inheritors = patcher.get_all_inheritors('TemplateWeapon')
    
    for s in inheritors:
        # Check if node exists in chain
        if psg.has_nested_node(patcher.file_contents[weapon_file], s, NESTED_PATH):
            patch = psg.generate_bpatch(s, NESTED_PATH, EFFECTS)
            patcher.add_patch(weapon_file, patch)
        else:
            # Check parent content for nested node recursively
            current = s
            found = False
            visited = set()
            while current and current not in visited:
                visited.add(current)
                data = psg.get_struct_content(patcher.file_contents[weapon_file], current)
                if data and psg.has_nested_node(data, current, NESTED_PATH):
                    found = True
                    break
                current = patcher.global_tree.get(current)
            
            if found:
                patch = psg.generate_bpatch(s, NESTED_PATH, EFFECTS)
                patcher.add_patch(weapon_file, patch)

    patcher.save_all("LessSway")

if __name__ == "__main__":
    main()
