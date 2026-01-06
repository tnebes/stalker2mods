import os
import re
import patching_script_general as psg

# Constants
SOURCE_DUMP = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P\Stalker2\Content\GameLite\GameData'

FILES = [
    'ObjPrototypes/GeneralNPCObjPrototypes.cfg',
    'WeaponData/CharacterWeaponSettingsPrototypes/NPCWeaponSettingsPrototypes.cfg',
    'WeaponData/CharacterWeaponSettingsPrototypes/PlayerWeaponSettingsPrototypes.cfg'
]

def patch_npc_vision(patcher):
    inheritors = patcher.get_all_inheritors("NPCBase")
    
    # Defaults from NPCBase to use if children don't override
    defaults = {
        "EnemyCouldBeVisibleMaxDistance": 5600.0,
        "LoseEnemyVisibilityTime": 4.0,
        "CheckEnemyTime": 20.0
    }
    
    vision_multipliers = {
        "EnemyCouldBeVisibleMaxDistance": 0.85,
        "LoseEnemyVisibilityTime": 0.5,
        "CheckEnemyTime": 1.5
    }

    for struct_name in inheritors:
        if psg.is_special_npc(struct_name):
            continue

        filename_info = patcher.struct_to_file.get(struct_name)
        if not filename_info: continue
        filename, rel_path = filename_info
        
        if filename != "GeneralNPCObjPrototypes.cfg":
            continue
        
        content = patcher.file_contents[filename]
        struct_data = psg.get_struct_content(content, struct_name)
        if not struct_data: continue
            
        has_cp_override = re.search(r'CombatParameters\s*:\s*struct\.begin', struct_data, re.IGNORECASE)
        cp_content = psg.get_struct_content(struct_data, "CombatParameters") if has_cp_override else struct_data
        
        p_props = {}
        for key, mult in vision_multipliers.items():
            v = psg.get_value(cp_content, key)
            if v is None and key in defaults:
                v = defaults[key]
            
            if v is not None and isinstance(v, (int, float)):
                rounded = psg.round_to_nearest(v * mult, 0.5)
                p_props[key] = f"{rounded:.1f}f"

        if p_props:
            patch = psg.generate_bpatch(struct_name, ["CombatParameters"], values=None, direct_properties=p_props)
            patcher.add_patch(filename, patch)

def patch_weapons(patcher):
    # NPC Weapons
    npc_weapon_file = "NPCWeaponSettingsPrototypes.cfg"
    npc_content = patcher.file_contents.get(npc_weapon_file)
    if npc_content:
        structs = re.findall(r'^\s*(\w+)\s*:\s*struct\.begin', npc_content, re.MULTILINE)
        for s in structs:
            if psg.is_special_npc(s): continue
            data = psg.get_struct_content(npc_content, s)
            props = {}
            for key in ["DispersionRadius", "DispersionRadiusZombieAddend"]:
                val = psg.get_value(data, key)
                if val is not None and isinstance(val, (int, float)):
                    props[key] = f"{psg.round_to_nearest(val * 1.2, 0.5):g}"
            if props:
                patcher.add_patch(npc_weapon_file, psg.generate_bpatch(s, direct_properties=props))

    # Player Weapons
    player_weapon_file = "PlayerWeaponSettingsPrototypes.cfg"
    player_content = patcher.file_contents.get(player_weapon_file)
    if player_content:
        structs = re.findall(r'^\s*(\w+)\s*:\s*struct\.begin', player_content, re.MULTILINE)
        for s in structs:
            if psg.is_special_npc(s): continue
            data = psg.get_struct_content(player_content, s)
            props = {}
            for key, mult in [("BaseComfort", 0.85), ("FireLoudness", 0.90)]:
                val = psg.get_value(data, key)
                if val is not None and isinstance(val, (int, float)):
                    props[key] = f"{psg.round_to_nearest(val * mult, 0.5):g}"
            if props:
                patcher.add_patch(player_weapon_file, psg.generate_bpatch(s, direct_properties=props))

def main():
    patcher = psg.ModPatcher(SOURCE_DUMP, MOD_ROOT)
    patcher.load_files(FILES)
    
    patch_npc_vision(patcher)
    patch_weapons(patcher)
    
    patcher.save_all("LongRangeCombat")

if __name__ == "__main__":
    main()
