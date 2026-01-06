import os
import re
import math
import patching_script_general as psg

# Paths
SOURCE_DUMP = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P\Stalker2\Content\GameLite\GameData'

# Files and their relative paths from GameData
FILES = {
    'NPC_PROTOTYPES': 'ObjPrototypes/GeneralNPCObjPrototypes.cfg',
    'NPC_WEAPONS': 'WeaponData/CharacterWeaponSettingsPrototypes/NPCWeaponSettingsPrototypes.cfg',
    'PLAYER_WEAPONS': 'WeaponData/CharacterWeaponSettingsPrototypes/PlayerWeaponSettingsPrototypes.cfg'
}

EXCLUSIONS = ['Guard', 'Korshunov', 'Strelok', 'Scar', 'Duga']

def round_05(val):
    """Rounds to the nearest 0.5."""
    return round(val * 2) / 2.0

def is_excluded(name):
    for exc in EXCLUSIONS:
        if exc.lower() in name.lower():
            return True
    return False

def get_struct_content_fixed(file_content, struct_name):
    """
    Returns the full string content of a struct definition, allowing leading whitespace.
    """
    pattern = re.compile(rf'^\s*{struct_name}\s*:\s*struct\.begin', re.MULTILINE | re.IGNORECASE)
    match = pattern.search(file_content)
    if not match:
        return None
    
    start_pos = match.start()
    brace_level = 0
    content_slice = file_content[start_pos:]
    
    markers = re.finditer(r'struct\.begin|struct\.end', content_slice, re.IGNORECASE)
    for m in markers:
        if m.group().lower() == 'struct.begin':
            brace_level += 1
        else:
            brace_level -= 1
        
        if brace_level == 0:
            return content_slice[:m.end()]
            
    return None

def get_value(content, key):
    match = re.search(rf'{key}\s*=\s*([\d\.\w]+)', content, re.IGNORECASE)
    if not match:
        return None
    val = match.group(1).lower().replace('f', '')
    try:
        return float(val)
    except ValueError:
        return val

def patch_npc_vision(global_tree, file_contents, struct_to_file):
    inheritors = psg.find_all_inheritors(global_tree, "NPCBase")
    inheritors.add("NPCBase")
    
    print(f"DEBUG: Found {len(inheritors)} inheritors for NPCBase")
    patches = {}
    
    # Defaults from NPCBase to use if children don't override
    defaults = {
        "EnemyCouldBeVisibleMaxDistance": 5600.0,
        "LoseEnemyVisibilityTime": 4.0,
        "CheckEnemyTime": 20.0
    }
    
    for struct_name in inheritors:
        if is_excluded(struct_name):
            continue

        filename = struct_to_file.get(struct_name)
        if not filename:
             continue
        if filename != os.path.basename(FILES['NPC_PROTOTYPES']):
            continue
        
        content = file_contents[filename]
        struct_data = get_struct_content_fixed(content, struct_name)
        if not struct_data:
            continue
            
        has_cp_override = re.search(r'CombatParameters\s*:\s*struct\.begin', struct_data, re.IGNORECASE)
        cp_content = get_struct_content_fixed(struct_data, "CombatParameters") if has_cp_override else struct_data
        
        p_props = {}
        vals = {
            "EnemyCouldBeVisibleMaxDistance": 0.85,
            "LoseEnemyVisibilityTime": 0.5,
            "CheckEnemyTime": 1.5
        }
        
        for key, mult in vals.items():
            v = get_value(cp_content, key)
            if v is not None and isinstance(v, float):
                p_props[key] = f"{round_05(v * mult)}f"
            elif key in defaults:
                # If local value is missing, use default from NPCBase
                # This ensures we patch EVERY child even if they don't have local overrides
                p_props[key] = f"{round_05(defaults[key] * mult)}f"

        if p_props:
            patch = f"{struct_name} : struct.begin {{bpatch}}\n"
            patch += "   CombatParameters : struct.begin {bpatch}\n"
            for k, v in p_props.items():
                patch += f"      {k} = {v}\n"
            patch += "   struct.end\n"
            patch += "struct.end\n"
            
            if filename not in patches:
                patches[filename] = []
            patches[filename].append(patch)
            
    return patches

def patch_weapon_settings(file_key, multipliers):
    filename = os.path.basename(FILES[file_key])
    file_path = os.path.join(SOURCE_DUMP, FILES[file_key])
    
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return {}

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        
    struct_pattern = re.compile(r'^(\w+)\s*:\s*struct\.begin', re.MULTILINE | re.IGNORECASE)
    matches = list(struct_pattern.finditer(content))
    # print(f"DEBUG: Found {len(matches)} structs in {filename}")
    
    patches = []
    for match in matches:
        struct_name = match.group(1)
        if is_excluded(struct_name):
            continue

        struct_data = get_struct_content_fixed(content, struct_name)
        if not struct_data:
            continue
            
        p_props = {}
        for key, mult in multipliers.items():
            val = get_value(struct_data, key)
            if val is not None and isinstance(val, float):
                rounded = round_05(val * mult)
                p_props[key] = f"{rounded:g}"
        
        if p_props:
            patch = f"{struct_name} : struct.begin {{bpatch}}\n"
            for k, v in p_props.items():
                patch += f"   {k} = {v}\n"
            patch += "struct.end\n"
            patches.append(patch)
            
    return {filename: patches}

def main():
    global_tree = {}
    file_contents = {}
    struct_to_file = {}
    
    npc_file_path = os.path.join(SOURCE_DUMP, FILES['NPC_PROTOTYPES'])
    if os.path.exists(npc_file_path):
        tree = psg.get_inheritance_tree(npc_file_path)
        global_tree.update(tree)
        with open(npc_file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            filename = os.path.basename(FILES['NPC_PROTOTYPES'])
            file_contents[filename] = content
            for struct_name in tree.keys():
                struct_to_file[struct_name] = filename

    all_patches = patch_npc_vision(global_tree, file_contents, struct_to_file)
    
    npc_weapon_patches = patch_weapon_settings('NPC_WEAPONS', {
        'DispersionRadius': 1.2,
        'DispersionRadiusZombieAddend': 1.2
    })
    all_patches.update(npc_weapon_patches)
    
    player_weapon_patches = patch_weapon_settings('PLAYER_WEAPONS', {
        'BaseComfort': 0.85,
        'FireLoudness': 0.90
    })
    all_patches.update(player_weapon_patches)

    print(f"DEBUG: all_patches keys: {list(all_patches.keys())}")
    wrote_any = False
    for filename, patches in all_patches.items():
        if not patches:
            print(f"DEBUG: No patches for {filename}")
            continue
        wrote_any = True
        base_name = os.path.splitext(filename)[0]
        
        rel_path = ""
        for k, v in FILES.items():
            if v.endswith(filename):
                rel_path = os.path.dirname(v)
                break
        
        target_dir = os.path.join(MOD_ROOT, rel_path, base_name)
        print(f"DEBUG: Writing to {target_dir} for {filename}")
        os.makedirs(target_dir, exist_ok=True)
        
        target_file = os.path.join(target_dir, f"{base_name}_patch_LongRangeCombat.cfg")
        print(f"Writing {len(patches)} patches to {target_file}...")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(patches))

    if not wrote_any:
        print("No patches generated!")
    else:
        print("Success.")

if __name__ == "__main__":
    main()
