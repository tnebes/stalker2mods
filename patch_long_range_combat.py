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
    'WeaponData/CharacterWeaponSettingsPrototypes.cfg',
    'AIPrototypes/VisionScannerPrototypes.cfg',
    'WeaponData/WeaponAttributesPrototypes/NPCWeaponAttributesPrototypes.cfg'
]

# --- MODIFIERS FOR VIABLE LONG RANGE ---
# Restore detection but slow down reaction and tracking

# --- DEBUG VISION & SPOTTING (COMMENTED OUT) ---
# VISION_DISTANCE_MULT = 0.01
# VISION_CHECK_TIME_MULT = 10.0
# VISION_LOSE_TIME_MULT = 0.01
# PLAYER_STEALTH_COMFORT_MULT = 0.1
# PLAYER_STEALTH_LOUDNESS_MULT = 0.1

VISION_DISTANCE_MULT = 0.9  
VISION_CHECK_TIME_MULT = 1.5 
VISION_LOSE_TIME_MULT = 2 # actually increased to 2 as we want them to react slower. additionally, for 10s the enemy will suppress player's last location. doesn't make sense for them to search if they are suppressing. 
PLAYER_STEALTH_COMFORT_MULT = 0.8
PLAYER_STEALTH_LOUDNESS_MULT = 0.8

# Weapon Accuracy & Range
NPC_WEAPON_DISPERSION_MULT = 0.05
NPC_RANGE_MULT = 1.5             

DEBUG_GUARANTEED_HITS = False # DEBUG: Every shot hits

def get_npc_base_defaults(patcher):
    """Dynamically reads defaults from NPCBase in the source files."""
    filename = "GeneralNPCObjPrototypes.cfg"
    content = patcher.file_contents.get(filename)
    if not content:
        print(f"Error: {filename} not found. Returning default values.")
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
        # Trace inheritance back to TemplateShotgun to identify shotguns
        shotgun_settings_sids = patcher.get_all_inheritors("TemplateShotgun")
        print(f"DEBUG: Found {len(shotgun_settings_sids)} shotgun settings SIDs (including templates)")
        
        # Matches top level structs
        structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', npc_content, re.MULTILINE)
        count = 0
        for s in structs:
            if psg.is_special_npc(s): continue
            
            data = psg.get_struct_content(npc_content, s)
            if not data: continue

            props = {}
            
            # 1. Dispersion Logic (Skip if it's a shotgun)
            if s not in shotgun_settings_sids:
                for key in ["DispersionRadius", "DispersionRadiusZombieAddend"]:
                    val = psg.get_value(data, key)
                    if val is not None and isinstance(val, (int, float)):
                        new_val = val * NPC_WE_DISPERSION_MULT if 'NPC_WE_DISPERSION_MULT' in locals() else val * NPC_WEAPON_DISPERSION_MULT
                        props[key] = f"{new_val:.2f}"
            
            # 2. Bleeding Logic (Use NPC original as base)
            # Formula: new = 0.646 * old + 1.54
            orig_bleed = psg.get_value(data, "BaseBleeding")
            if orig_bleed is not None and isinstance(orig_bleed, (int, float)):
                n_bleed = 0.646 * orig_bleed + 1.54
                props["BaseBleeding"] = f"{n_bleed:.1f}"
            
            # 3. Chance Logic (reduce it by 25% or to 1% whichever is higher reduction)
            # This logic maps 2% to 1% (greater of 0.5% reduction or 1% reduction)
            orig_chance = psg.get_value(data, "ChanceBleedingPerShot")
            if orig_chance is not None and isinstance(orig_chance, (int, float)):
                # We want the GREATER reduction: max(Value * 0.25, 0.01)
                # So the new value is min(Value * 0.75, Value - 0.01)
                n_chance = min(orig_chance * 0.75, orig_chance - 0.01)
                n_chance = max(0.01, n_chance) # Never below 1%
                props["ChanceBleedingPerShot"] = f"{round(n_chance * 100)}%"

            if props:
                patcher.add_patch(npc_weapon_file, psg.generate_bpatch(s, direct_properties=props))
                count += 1
        print(f"DEBUG: Applied weapon bleeding/dispersion bpatches to {count} structs in NPCWeaponSettingsPrototypes.cfg")

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
    
    # Identify shotguns by tracing settings inheritance back to TemplateShotgun
    shotgun_settings_sids = patcher.get_all_inheritors("TemplateShotgun")
    print(f"DEBUG: Found {len(shotgun_settings_sids)} shotgun settings SIDs: {shotgun_settings_sids}")
    
    structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    count = 0
    
    # Fine-tuning rules (Generated via generate_rank_curves.py & Manual Tuning)
    rank_configs = {
        "Newbie": {
            "range_mult": 0.8,
            "ignore_disp_min": {'Short': 0, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0, 'Medium': 0, 'Long': 0},
            "ignore_disp_chance_max": {'Short': 0.0567, 'Medium': 0, 'Long': 0}
        },
        "Experienced": {
            "range_mult": 1.5,
            "ignore_disp_min": {'Short': 1, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0.2445, 'Medium': 0.0458, 'Long': 0},
            "ignore_disp_chance_max": {'Short': 0.5623, 'Medium': 0.1783, 'Long': 0.0026}
        },
        "Veteran": {
            "range_mult": 1.5,
            "ignore_disp_min": {'Short': 1, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0.3983, 'Medium': 0.2445, 'Long': 0.0209},
            "ignore_disp_chance_max": {'Short': 0.6774, 'Medium': 0.5623, 'Long': 0.1177}
        },
        "Master": {
            "range_mult": 1.1,
            "ignore_disp_min": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 1},
            "ignore_disp_chance_min": {'Short': 0.4406, 'Medium': 0.3983, 'Long': 0.2},
            "ignore_disp_chance_max": {'Short': 0.6889, 'Medium': 0.6774, 'Long': 0.5017}
        },
        "Zombie": {
            "range_mult": 1.0,
            "ignore_disp_min": {'Short': 0, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 0, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0.0458, 'Medium': 0, 'Long': 0},
            "ignore_disp_chance_max": {'Short': 0.1783, 'Medium': 0.0105, 'Long': 0}
        }
    }

    for s in structs:
        if psg.is_special_npc(s): continue
        data = psg.get_struct_content(content, s)
        
        ai_params = psg.get_struct_content(data, "AIParameters")
        if not ai_params: continue
        
        # Check if it's a shotgun via its CharacterWeaponSettingsSID
        # We search the whole struct content for CharacterWeaponSettingsSID to be sure
        settings_sid_match = re.search(r'CharacterWeaponSettingsSID\s*=\s*(\w+)', data, re.IGNORECASE)
        if settings_sid_match:
            settings_sid = settings_sid_match.group(1)
            if settings_sid in shotgun_settings_sids:
                print(f"DEBUG: Skipping shotgun {s} (SettingsSID: {settings_sid})")
                continue

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
            config = rank_configs.get(t, {"range_mult": 1.5})
            
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
                    # Configuration floors (hardcoded rules)
                    floor_min = config.get("ignore_disp_min", {}).get(bracket, 0)
                    floor_max = config.get("ignore_disp_max", {}).get(bracket, 0)
                    
                    # Sigmoid curve multipliers
                    chance_min = config.get("ignore_disp_chance_min", {}).get(bracket, 0)
                    chance_max = config.get("ignore_disp_chance_max", {}).get(bracket, 0)
                    
                    min_shots = psg.get_value(b_data, "MinShots")
                    max_shots = psg.get_value(b_data, "MaxShots")

                    if min_shots is not None and max_shots is not None:
                        # Calculated values based on burst size
                        calc_min = int(min_shots * chance_min)
                        calc_max = int(min_shots * chance_max) # Using min_shots as base for max too? Or max_shots?
                        # User says: "multiplier * MinShots"
                        
                        ignore_min = max(floor_min, calc_min)
                        ignore_max = max(floor_max, calc_max)
                        
                        # Specialized override for low-shot weapons (Snipers/Bolt-actions)
                        if min_shots <= 2 and max_shots <= 2:
                            # Sniper refinement: Most ranks get 0 guaranteed hits
                            ignore_min = 0
                            ignore_max = 0
                            # Master rank at Short/Medium gets 50/50 chance (0 to 1)
                            if t == "Master" and bracket in ["Short", "Medium"]:
                                ignore_min = 0
                                ignore_max = 1

                        if DEBUG_GUARANTEED_HITS:
                            ignore_min = 100
                            ignore_max = 100

                        rank_lines.append(f"            {bracket} : struct.begin {{bpatch}}")
                        rank_lines.append(f"               IgnoreDispersionMinShots = {ignore_min}")
                        rank_lines.append(f"               IgnoreDispersionMaxShots = {ignore_max}")
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
