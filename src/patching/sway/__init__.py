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
    
    filename = os.path.basename(weapon_rel_path)
    inheritors = patcher.get_all_inheritors('TemplateWeapon')
    
    for s in inheritors:
        # Check if path exists in struct or its inheritance chain
        curr = s
        found = False
        visited = set()
        while curr and curr not in visited:
            visited.add(curr)
            if patcher.has_property_path(curr, WEAPON_NESTED_PATH, filename):
                found = True
                break
            curr = patcher.global_tree.get(curr)
            
        if found:
            patch = psg.generate_bpatch(s, WEAPON_NESTED_PATH, EFFECTS)
            patcher.add_patch(weapon_file if 'weapon_file' in locals() else filename, patch)

def patch_attachments(patcher):
    attach_file = 'Content/GameLite/GameData/ItemPrototypes/AttachPrototypes.cfg'
    patcher.load_files([attach_file])
    
    filename = os.path.basename(attach_file)
    
    # We can get all structs from the AST now
    structs = [node.name for node in patcher.file_asts[filename] if isinstance(node, psg.cfg_ast.StructNode)]
    
    for s in structs:
        # Check properties in chain
        current = s
        has_breath = False
        has_scope = False
        visited = set()
        while current and current not in visited:
            visited.add(current)
            node = patcher.get_struct(current, filename)
            if node:
                if not has_breath and node.find_child("CanHoldBreath"):
                    has_breath = True
                if not has_scope and patcher.has_property_path(current, ATTACH_NESTED_PATH, filename):
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
