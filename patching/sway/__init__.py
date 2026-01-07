import os
import re
import patching_script_general as psg
from patch_config import SOURCE_DUMP, get_mod_root

EFFECTS = ["LessSwayX", "LessSwayY", "LessSwayTime"]
WEAPON_NESTED_PATH = ["AimingEffects", "PlayerOnlyEffects"]
ATTACH_NESTED_PATH = ["Scope", "AimingEffects", "PlayerOnlyEffects"]

def patch_weapons(patcher):
    weapon_rel_path = 'Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg'
    patcher.load_files([weapon_rel_path])
    
    weapon_file = os.path.basename(weapon_rel_path)
    inheritors = patcher.get_all_inheritors('TemplateWeapon')
    
    for s in inheritors:
        # Check if node exists in chain
        if psg.has_nested_node(patcher.file_contents[weapon_file], s, WEAPON_NESTED_PATH):
            patch = psg.generate_bpatch(s, WEAPON_NESTED_PATH, EFFECTS)
            patcher.add_patch(weapon_file, patch)
        else:
            # Check parent content for nested node recursively
            current = s
            found = False
            visited = set()
            while current and current not in visited:
                visited.add(current)
                data = psg.get_struct_content(patcher.file_contents[weapon_file], current)
                if data and psg.has_nested_node(data, current, WEAPON_NESTED_PATH):
                    found = True
                    break
                current = patcher.global_tree.get(current)
            
            if found:
                patch = psg.generate_bpatch(s, WEAPON_NESTED_PATH, EFFECTS)
                patcher.add_patch(weapon_file, patch)

def patch_attachments(patcher):
    attach_file = 'Content/GameLite/GameData/ItemPrototypes/AttachPrototypes.cfg'
    patcher.load_files([attach_file])
    
    filename = os.path.basename(attach_file)
    content = patcher.file_contents[filename]
    
    structs = re.findall(r'^\s*(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    
    for s in structs:
        # Check properties in chain
        current = s
        has_breath = False
        has_scope = False
        visited = set()
        while current and current not in visited:
            visited.add(current)
            data = psg.get_struct_content(content, current)
            if data:
                if not has_breath and "CanHoldBreath" in data:
                    has_breath = True
                if not has_scope and psg.has_nested_node(data, current, ATTACH_NESTED_PATH):
                    has_scope = True
            current = patcher.global_tree.get(current)
            
        if not (has_breath or has_scope):
            continue
            
        patch_props = {"CanHoldBreath": "true"} if has_breath else None
        patch_nested_path = ATTACH_NESTED_PATH if has_scope else None
        patch_values = EFFECTS if has_scope else None
        
        patch_text = psg.generate_bpatch(s, patch_nested_path, patch_values, root_properties=patch_props)
        patcher.add_patch(filename, patch_text)

def run():
    print("--- Running LessSway Patching ---")
    mod_root = get_mod_root("LessSway")
    patcher = psg.ModPatcher(SOURCE_DUMP, mod_root)
    
    patch_weapons(patcher)
    patch_attachments(patcher)
    
    patcher.save_all("LessSway")
