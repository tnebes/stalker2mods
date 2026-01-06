import os
import re
import patching_script_general as psg

# Constants
SOURCE_DUMP = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P\Stalker2\Content\GameLite\GameData'

FILES = [
    'ObjPrototypes/GeneralNPCObjPrototypes.cfg',
    'WeaponData/CharacterWeaponSettingsPrototypes/NPCWeaponSettingsPrototypes.cfg',
    'WeaponData/CharacterWeaponSettingsPrototypes/PlayerWeaponSettingsPrototypes.cfg',
    'AIPrototypes/VisionScannerPrototypes.cfg',
    'WeaponData/WeaponAttributesPrototypes/NPCWeaponAttributesPrototypes.cfg'
]

# --- MODIFIERS FOR VIABLE LONG RANGE ---
# Restore detection but slow down reaction and tracking

# --- DEBUG VISION & SPOTTING (COMMENTED OUT) ---
VISION_DISTANCE_MULT = 0.01
VISION_CHECK_TIME_MULT = 10.0
VISION_LOSE_TIME_MULT = 0.01
PLAYER_STEALTH_COMFORT_MULT = 0.1
PLAYER_STEALTH_LOUDNESS_MULT = 0.1

# VISION_DISTANCE_MULT = 1.0  
# VISION_CHECK_TIME_MULT = 1.5 
# VISION_LOSE_TIME_MULT = 0.75 
# PLAYER_STEALTH_COMFORT_MULT = 1.0
# PLAYER_STEALTH_LOUDNESS_MULT = 1.0

# Weapon Accuracy & Range
NPC_WEAPON_DISPERSION_MULT = 2.0 
NPC_RANGE_MULT = 1.5             

DEBUG_GUARANTEED_HITS = False # DEBUG: Every shot hits

def get_npc_base_defaults(patcher):
    """Dynamically reads defaults from NPCBase in the source files."""
    filename = "GeneralNPCObjPrototypes.cfg"
    content = patcher.file_contents.get(filename)
    if not content:
        return {
            "EnemyCouldBeVisibleMaxDistance": 5600.0,
            "LoseEnemyVisibilityTime": 4.0,
            "CheckEnemyTime": 20.0
        }
    
    struct_data = psg.get_struct_content(content, "NPCBase")
    if not struct_data: return {}
    
    cp_data = psg.get_struct_content(struct_data, "CombatParameters")
    target_data = cp_data if cp_data else struct_data
    
    return {
        "EnemyCouldBeVisibleMaxDistance": psg.get_value(target_data, "EnemyCouldBeVisibleMaxDistance"),
        "LoseEnemyVisibilityTime": psg.get_value(target_data, "LoseEnemyVisibilityTime"),
        "CheckEnemyTime": psg.get_value(target_data, "CheckEnemyTime")
    }

def patch_npc_vision(patcher):
    inheritors = patcher.get_all_inheritors("NPCBase")
    defaults = get_npc_base_defaults(patcher)
    print(f"DEBUG: Found {len(inheritors)} NPCs inheriting from NPCBase.")
    
    vision_multipliers = {
        "EnemyCouldBeVisibleMaxDistance": VISION_DISTANCE_MULT,
        "LoseEnemyVisibilityTime": VISION_LOSE_TIME_MULT,
        "CheckEnemyTime": VISION_CHECK_TIME_MULT
    }

    count = 0
    for struct_name in inheritors:
        # Don't skip NPCBase itself, but skip other specials
        if psg.is_special_npc(struct_name) and struct_name != "NPCBase":
            continue

        filename_info = patcher.struct_to_file.get(struct_name)
        if not filename_info: continue
        filename, _ = filename_info
        
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
                new_val = v * mult
                p_props[key] = f"{new_val:.4f}f"

        if p_props:
            patch = psg.generate_bpatch(struct_name, ["CombatParameters"], values=None, direct_properties=p_props)
            patcher.add_patch(filename, patch)
            count += 1
    print(f"DEBUG: Applied vision patches to {count} structs in GeneralNPCObjPrototypes.cfg")

def patch_vision_scanners(patcher):
    filename = "VisionScannerPrototypes.cfg"
    content = patcher.file_contents.get(filename)
    if not content: return
    
    # Use '^(\w+)' to ensure we only catch top-level structs (no indentation)
    structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    
    # Identify defaults from "DefaultNPC"
    base_scanner = "DefaultNPC"
    base_data = psg.get_struct_content(content, base_scanner)
    if not base_data: return
    
    scanner_defaults = {}
    for key in ["CentralVisionDistance", "PeripheralVisionDistance", "TooCloseVisionDistance"]:
        val = psg.get_value(base_data, key)
        if val is not None:
            scanner_defaults[key] = val

    count = 0
    for s in structs:
        if s in ["Player", "NoVision", "ScarBoss", "Boss"]: continue
        
        data = psg.get_struct_content(content, s)
        props = {}
        for key, base_val in scanner_defaults.items():
            val = psg.get_value(data, key)
            if val is None:
                val = base_val
            
            if val is not None and isinstance(val, (int, float)):
                new_val = val * VISION_DISTANCE_MULT
                props[key] = f"{new_val:.4f}f"
        
        if props:
            patcher.add_patch(filename, psg.generate_bpatch(s, direct_properties=props))
            count += 1
    print(f"DEBUG: Applied patches to {count} vision scanners in VisionScannerPrototypes.cfg")

def patch_weapons(patcher):
    # NPC Weapons
    npc_weapon_file = "NPCWeaponSettingsPrototypes.cfg"
    npc_content = patcher.file_contents.get(npc_weapon_file)
    if npc_content:
        structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', npc_content, re.MULTILINE)
        count = 0
        for s in structs:
            if psg.is_special_npc(s): continue
            data = psg.get_struct_content(npc_content, s)
            props = {}
            for key in ["DispersionRadius", "DispersionRadiusZombieAddend"]:
                val = psg.get_value(data, key)
                if val is not None and isinstance(val, (int, float)):
                    new_val = val * NPC_WEAPON_DISPERSION_MULT
                    props[key] = f"{new_val:.2f}"
            if props:
                patcher.add_patch(npc_weapon_file, psg.generate_bpatch(s, direct_properties=props))
                count += 1
        print(f"DEBUG: Applied weapon dispersion patches to {count} structs in NPCWeaponSettingsPrototypes.cfg")

    # Player Weapons (Stealth components)
    player_weapon_file = "PlayerWeaponSettingsPrototypes.cfg"
    player_content = patcher.file_contents.get(player_weapon_file)
    if player_content:
        structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', player_content, re.MULTILINE)
        count = 0
        for s in structs:
            if psg.is_special_npc(s): continue
            data = psg.get_struct_content(player_content, s)
            props = {}
            for key, mult in [("BaseComfort", PLAYER_STEALTH_COMFORT_MULT), ("FireLoudness", PLAYER_STEALTH_LOUDNESS_MULT)]:
                val = psg.get_value(data, key)
                if val is not None and isinstance(val, (int, float)):
                    new_val = val * mult
                    props[key] = f"{new_val:.4f}"
            if props:
                patcher.add_patch(player_weapon_file, psg.generate_bpatch(s, direct_properties=props))
                count += 1
        print(f"DEBUG: Applied stealth patches to {count} structs in PlayerWeaponSettingsPrototypes.cfg")

def patch_npc_attributes(patcher):
    filename = "NPCWeaponAttributesPrototypes.cfg"
    content = patcher.file_contents.get(filename)
    if not content: return
    
    structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    count = 0
    
    # Fine-tuning rules
    rank_configs = {
        "Newbie": {
            "range_mult": 0.75, 
            "ignore_disp": {"Short": 0, "Medium": 0, "Long": 0}
        },
        "Experienced": {
            "range_mult": 1.5, 
            "ignore_disp": {"Short": 1, "Medium": 0, "Long": 0}
        },
        "Veteran": {
            "range_mult": 1.5, 
            "ignore_disp": {"Short": 1, "Medium": 1, "Long": 0}
        },
        "Master": {
            "range_mult": 1.1, 
            "ignore_disp": {"Short": 1, "Medium": 1, "Long": 1}
        },
        "Zombie": {
            "range_mult": 1.0, 
            "ignore_disp": {"Short": 0, "Medium": 0, "Long": 0}
        }
    }

    for s in structs:
        if psg.is_special_npc(s): continue
        data = psg.get_struct_content(content, s)
        
        ai_params = psg.get_struct_content(data, "AIParameters")
        if not ai_params: continue
        
        behavior_types_full = psg.get_struct_content(ai_params, "BehaviorTypes")
        if not behavior_types_full: continue
        
        # Skip original declaration
        body = "\n".join(behavior_types_full.splitlines()[1:])
        
        # Find indent of direct children (ranks)
        indents = re.findall(r'^(\s+)\w+\s*:\s*struct\.begin', body, re.MULTILINE)
        if not indents: continue
        min_indent = min(len(i) for i in indents)
        types = re.findall(rf'^\s{{{min_indent}}}(\w+)\s*:\s*struct\.begin', body, re.MULTILINE)
        
        sid_patch_lines = [
            f"{s} : struct.begin {{bpatch}}", 
            "   AIParameters : struct.begin {bpatch}", 
            "      BehaviorTypes : struct.begin {bpatch}"
        ]
        has_any_sid_change = False

        for t in types:
            t_data = psg.get_struct_content(behavior_types_full, t)
            config = rank_configs.get(t, {"range_mult": 1.5, "ignore_disp": {}})
            
            rank_lines = [f"         {t} : struct.begin {{bpatch}}"]
            has_any_rank_change = False
            
            # Engagement Range
            dist_max = psg.get_value(t_data, "CombatEffectiveFireDistanceMax")
            if dist_max:
                rank_lines.append(f"            CombatEffectiveFireDistanceMax = {dist_max * config['range_mult']:.1f}")
                has_any_rank_change = True
            
            # IgnoreDispersion logic
            for bracket in ["Short", "Medium", "Long"]:
                b_data = psg.get_struct_content(t_data, bracket)
                if b_data:
                    # Default to 0 unless specified in config
                    ignore_val = config["ignore_disp"].get(bracket, 0)
                    if DEBUG_GUARANTEED_HITS:
                        ignore_val = 100
                    rank_lines.append(f"            {bracket} : struct.begin {{bpatch}}")
                    rank_lines.append(f"               IgnoreDispersionMinShots = {ignore_val}")
                    rank_lines.append(f"               IgnoreDispersionMaxShots = {ignore_val}")
                    rank_lines.append(f"            struct.end")
                    has_any_rank_change = True
            
            if has_any_rank_change:
                rank_lines.append("         struct.end")
                sid_patch_lines.extend(rank_lines)
                has_any_sid_change = True
        
        if has_any_sid_change:
            sid_patch_lines.extend(["      struct.end", "   struct.end", "struct.end"])
            patcher.add_patch(filename, "\n".join(sid_patch_lines))
            count += 1
            
    print(f"DEBUG: Applied logic patches to {count} weapons in NPCWeaponAttributesPrototypes.cfg")

def main():
    patcher = psg.ModPatcher(SOURCE_DUMP, MOD_ROOT)
    patcher.load_files(FILES)
    
    patch_npc_vision(patcher)
    patch_vision_scanners(patcher)
    patch_weapons(patcher)
    patch_npc_attributes(patcher)
    
    patcher.save_all("LongRangeCombat")

if __name__ == "__main__":
    main()
