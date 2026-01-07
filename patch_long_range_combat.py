import os
import re
import patching_script_general as psg

# Constants
SOURCE_DUMP = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P\Stalker2'

FILES = [
    'Content/GameLite/GameData/ObjPrototypes/GeneralNPCObjPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/CharacterWeaponSettingsPrototypes/NPCWeaponSettingsPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/CharacterWeaponSettingsPrototypes/PlayerWeaponSettingsPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/CharacterWeaponSettingsPrototypes.cfg',
    'Content/GameLite/GameData/AIPrototypes/VisionScannerPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/WeaponAttributesPrototypes/NPCWeaponAttributesPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg'
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

def load_weapon_stats_map(patcher):
    """Parses WeaponGeneralSetupPrototypes.cfg to map SIDs to MaxAmmo, RecoilRadius, and FirstShotDispersionRadius."""
    # Use absolute path directly to be safe
    filepath = os.path.join(SOURCE_DUMP, "Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg")
    if not os.path.exists(filepath):
        print(f"DEBUG: {filepath} not found.")
        return {}
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    stats_map = {}
    current_sid = None
    for line in content.splitlines():
        sid_match = re.search(r'SID\s*=\s*(\w+)', line)
        if sid_match:
            current_sid = sid_match.group(1)
            if current_sid not in stats_map:
                stats_map[current_sid] = {}
        
        # MaxAmmo
        ammo_match = re.search(r'^\s*MaxAmmo\s*=\s*(\d+)', line, re.IGNORECASE)
        if ammo_match and current_sid:
            stats_map[current_sid]['MaxAmmo'] = int(ammo_match.group(1))
        
        # RecoilRadius
        recoil_match = re.search(r'^\s*RecoilRadius\s*=\s*([\d\.]+)', line, re.IGNORECASE)
        if recoil_match and current_sid:
            stats_map[current_sid]['RecoilRadius'] = float(recoil_match.group(1))

        # FirstShotDispersionRadius
        fsd_match = re.search(r'^\s*FirstShotDispersionRadius\s*=\s*([\d\.]+)', line, re.IGNORECASE)
        if fsd_match and current_sid:
            stats_map[current_sid]['FirstShotDispersionRadius'] = float(fsd_match.group(1))
            
    return stats_map

def get_struct_names(content):
    """Returns a list of top-level struct SIDs found in the content."""
    return re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)

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
        if struct_name == "GunRpg7_GL_NPC":
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
        if s == "GunRpg7_GL_NPC":
            print(f"DEBUG: Skipping RPG-7 {s}")
            continue

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
            s_clean = s.strip()
            if psg.is_special_npc(s_clean): continue
            if "RPG7" in s_clean.upper():
                continue
            
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

def patch_npc_attributes(patcher, weapon_stats):
    filename = "NPCWeaponAttributesPrototypes.cfg"
    content = patcher.file_contents.get(filename)
    if not content: return
    
    # Identify shotguns and snipers by tracing settings inheritance
    shotgun_settings_sids = patcher.get_all_inheritors("TemplateShotgun")
    sniper_settings_sids = patcher.get_all_inheritors("TemplateSniper")
    print(f"DEBUG: Found {len(shotgun_settings_sids)} shotgun and {len(sniper_settings_sids)} sniper settings SIDs.")
    
    structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    count = 0
    
    # Fine-tuning rules (Generated via generate_rank_curves.py & Manual Tuning)
    rank_configs = {
        "Newbie": {
            "range_mult": 0.8,
            "ignore_disp_min": {'Short': 0, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0, 'Medium': 0, 'Long': 0},
            "ignore_disp_chance_max": {'Short': 0.0567, 'Medium': 0, 'Long': 0},
            "burst_logic": {'burst_mult': 1.25, 'min_add': 0, 'max_add': 0, 'guaranteed_add_long': 0, 'guaranteed_add_medium': 0, 'guaranteed_add_short': 0}
        },
        "Experienced": {
            "range_mult": 1.5,
            "ignore_disp_min": {'Short': 1, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0.2445, 'Medium': 0.0458, 'Long': 0},
            "ignore_disp_chance_max": {'Short': 0.5623, 'Medium': 0.1783, 'Long': 0.0026},
            "burst_logic": {'burst_mult': 1.0, 'long_burst_mult': 0.9, 'min_add': 0, 'max_add': 0, 'guaranteed_add_long': 0, 'guaranteed_add_medium': 0, 'guaranteed_add_short': 0, 'ignore_disp_max_inc_if_small': 1}
        },
        "Veteran": {
            "range_mult": 1.5,
            "ignore_disp_min": {'Short': 1, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 0}, # Phase 4 Nerf: 0 bonus at Long
            "ignore_disp_chance_min": {'Short': 0.1783, 'Medium': 0.1177, 'Long': 0.0458},
            "ignore_disp_chance_max": {'Short': 0.4406, 'Medium': 0.4285, 'Long': 0.3541},
            "burst_logic": {'burst_mult': 1.0, 'long_burst_mult': 0.75, 'medium_burst_mult': 0.85, 'short_burst_mult': 1.1, 'min_add': 0, 'max_add': 1}
        },
        "Master": {
            "range_mult": 1.5,
            "ignore_disp_min": {'Short': 1, 'Medium': 1, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 1, 'Long': 1},
            "ignore_disp_chance_min": {'Short': 0.4406, 'Medium': 0.3983, 'Long': 0.2},
            "ignore_disp_chance_max": {'Short': 0.6889, 'Medium': 0.6774, 'Long': 0.5017},
            "burst_logic": {'burst_mult': 1.0, 'long_burst_mult': 0.4, 'medium_burst_mult': 0.75, 'short_burst_mult': 1.25, 'min_add': 0, 'max_add': 0, 'guaranteed_add_long_min': 0, 'guaranteed_add_long_max': -1, 'guaranteed_add_medium_min': 0, 'guaranteed_add_medium_max': 1, 'guaranteed_add_short_mag_pct': 0.04}
        },
        "Zombie": {
            "range_mult": 1.0,
            "ignore_disp_min": {'Short': 0, 'Medium': 0, 'Long': 0},
            "ignore_disp_max": {'Short': 1, 'Medium': 0, 'Long': 0},
            "ignore_disp_chance_min": {'Short': 0.0458, 'Medium': 0, 'Long': 0},
            "ignore_disp_chance_max": {'Short': 0.1783, 'Medium': 0.0105, 'Long': 0},
            "burst_logic": {'burst_mult': 1.5, 'min_add': 0, 'max_add': 0}
        }
    }
    structs = get_struct_names(content)
    print(f"DEBUG: Found {len(structs)} structs in {filename}.")
    count = 0
    
    for s in structs:
        s_clean = s.strip()
        if psg.is_special_npc(s_clean): continue
        if "RPG7" in s_clean.upper():
            continue
        data = psg.get_struct_content(content, s)
        
        ai_params = psg.get_struct_content(data, "AIParameters")
        if not ai_params: continue
        
        # Identify weapon type
        settings_sid_match = re.search(r'CharacterWeaponSettingsSID\s*=\s*(\w+)', data, re.IGNORECASE)
        settings_sid = settings_sid_match.group(1) if settings_sid_match else None

        is_shotgun = settings_sid in shotgun_settings_sids if settings_sid else False
        is_sniper = settings_sid in sniper_settings_sids if settings_sid else False

        if is_shotgun:
            print(f"DEBUG: Identify shotgun {s} (SettingsSID: {settings_sid}) - will apply range nerf/clamp but skip dispersion/burst")
        
        # Attempt to find stats for this weapon
        w_stats = weapon_stats.get(settings_sid, {}) if settings_sid else {}
        if not w_stats and settings_sid:
            # Try stripped version
            stripped_sid = settings_sid.replace("_NPC", "").replace("_Player", "")
            w_stats = weapon_stats.get(stripped_sid, {})

        max_ammo = w_stats.get('MaxAmmo', 30) # Default to 30 if not found
        fsd = w_stats.get('FirstShotDispersionRadius', 500.0) # Conservative default
        if s == "GunAK74_ST_NPC":
            print(f"DEBUG: AK74 FSD={fsd}, stats found: {bool(w_stats)}, SID={settings_sid}")

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
            config = rank_configs.get(t, {"range_mult": 1.5, "burst_logic": {}})
            blogic = config.get("burst_logic", {})
            
            rank_lines = [f"         {t} : struct.begin {{bpatch}}"]
            has_any_rank_change = False
            
            # Engagement Range
            dist_max = psg.get_value(t_data, "CombatEffectiveFireDistanceMax")
            dist_min = psg.get_value(t_data, "CombatEffectiveFireDistanceMin")
            if dist_max:
                new_dist_max = dist_max * config['range_mult']
                if is_shotgun:
                    new_dist_max *= 0.75 # USER: "decrease their range by 25%"
                
                # Range Clamping: Max must remain > Min
                current_min = dist_min if dist_min is not None else 0
                if new_dist_max <= current_min:
                    # Decrease Min to 90% of New Max
                    new_min = new_dist_max * 0.9
                    rank_lines.append(f"            CombatEffectiveFireDistanceMin = {new_min:.1f}")
                
                rank_lines.append(f"            CombatEffectiveFireDistanceMax = {new_dist_max:.1f}")
                has_any_rank_change = True
            
            # Skip IgnoreDispersion for shotguns entirely
            process_dispersion = not is_shotgun
            # Skip Burst sizes for snipers AND shotguns
            process_burst = not is_sniper and not is_shotgun

            for bracket in ["Short", "Medium", "Long"]:
                b_data = psg.get_struct_content(t_data, bracket)
                if not b_data: continue

                # Get original values for reference even if skipping burst patching
                orig_min = psg.get_value(b_data, "MinShots") or 1
                orig_max = psg.get_value(b_data, "MaxShots") or 1
                
                # Default new values to originals
                new_min, new_max = orig_min, orig_max

                # Burst size patching (skip for snipers)
                if process_burst:
                    mult = blogic.get("burst_mult", 1.0)
                    if bracket == "Long": mult *= blogic.get("long_burst_mult", 1.0)
                    elif bracket == "Medium": mult *= blogic.get("medium_burst_mult", 1.0)
                    elif bracket == "Short": mult *= blogic.get("short_burst_mult", 1.0)

                    new_min = int(orig_min * mult) + blogic.get("min_add", 0)
                    new_max = int(orig_max * mult) + blogic.get("max_add", 0)

                    # Base case scenario: ensure at least 1 shot change if mult > 1 and it didn't move
                    if mult > 1.0 and new_max == orig_max:
                        new_max += 1

                    # Cap by MaxAmmo
                    new_max = min(new_max, max_ammo)
                    new_min = min(new_min, new_max)
                    if new_min < 1: new_min = 1
                    if new_max < new_min: new_max = new_min

                # IgnoreDispersion logic (skip for shotguns)
                ignore_min, ignore_max = None, None
                if process_dispersion:
                    floor_min = config.get("ignore_disp_min", {}).get(bracket, 0)
                    floor_max = config.get("ignore_disp_max", {}).get(bracket, 0)
                    chance_min = config.get("ignore_disp_chance_min", {}).get(bracket, 0)
                    chance_max = config.get("ignore_disp_chance_max", {}).get(bracket, 0)

                    # Base ignored shots based on new/orig min shots
                    ignore_min = max(floor_min, int(new_min * chance_min))
                    ignore_max = max(floor_max, int(new_min * chance_max))

                    # User rules:
                    # 1. Experienced: ignoredispersionmaxshots may only increase by 1 if shots < 4
                    if blogic.get("ignore_disp_max_inc_if_small") and new_max < 4:
                        ignore_max += 1

                    # 2. Veteran: gain 1 max shot long, 1 min shot medium
                    if bracket == "Long": ignore_max += blogic.get("guaranteed_add_long", 0)
                    if bracket == "Medium":
                        ignore_min += blogic.get("guaranteed_add_medium_min", 0)
                        ignore_max += blogic.get("guaranteed_add_medium_max", 0)

                    # 3. Master: refinements
                    if t == "Master":
                        if bracket == "Long":
                            ignore_min += blogic.get("guaranteed_add_long_min", 0)
                            ignore_max += blogic.get("guaranteed_add_long_max", 0)
                        elif bracket == "Medium":
                            ignore_min += blogic.get("guaranteed_add_medium_min", 0)
                            ignore_max += blogic.get("guaranteed_add_medium_max", 0)
                        elif bracket == "Short":
                            mag_floor = int(max_ammo * blogic.get("guaranteed_add_short_mag_pct", 0))
                            ignore_min = max(ignore_min, mag_floor)
                            ignore_max = max(ignore_max, mag_floor)

                    # 6. Veteran Long Range Nerf
                    if t == "Veteran" and bracket == "Long":
                        # Original ignore_max for Veteran Long was 0.
                        # The config now has ignore_disp_max: {'Short': 1, 'Medium': 1, 'Long': 0}
                        # So floor_max for Long is 0.
                        # This means ignore_max will be max(0, int(new_min * chance_max))
                        # The change is that it should not get any bonus from guaranteed_add_long.
                        # Since guaranteed_add_long is 0 for Veteran, this line is effectively a no-op
                        # but serves as a clear marker for the nerf.
                        pass # No bonus +1

                    # 5. Snipers overrides (Phase 3) - Explicitly setting values
                    if is_sniper:
                        if t == "Experienced":
                            if bracket == "Short": 
                                ignore_max = 1
                        elif t == "Veteran":
                            if bracket == "Short": 
                                ignore_min = 1
                                ignore_max = 1
                            elif bracket == "Medium":
                                ignore_min = 0 # No guaranteed min mentioned for medium
                                ignore_max = 1
                        elif t == "Master":
                            ignore_max = 1
                            if bracket in ["Short", "Medium"]:
                                ignore_min = 1
                            else:
                                ignore_min = 0 # Long range min is 0

                    if t == "Master" and bracket == "Long":
                        # Phase 4: Marksman Trait
                        # Precision weapons (FSD < 160): no penalty, floor of 1
                        # Imprecise weapons (FSD >= 160): keep -1 penalty
                        original_ignore_max = psg.get_value(b_data, "IgnoreDispersionMaxShots") or 0
                        if fsd < 160:
                             ignore_max = max(1, original_ignore_max) # 0 bonus, floor 1
                        else:
                             ignore_max = max(0, original_ignore_max - 1) # -1 penalty
                    
                    # Capping
                    ignore_max = min(ignore_max, new_max)
                    ignore_min = min(ignore_min, ignore_max)

                # Generate bpatch for bracket
                bracket_lines = []
                if process_burst:
                    bracket_lines.append(f"               MinShots = {new_min}")
                    bracket_lines.append(f"               MaxShots = {new_max}")
                if process_dispersion:
                    bracket_lines.append(f"               IgnoreDispersionMinShots = {ignore_min}")
                    bracket_lines.append(f"               IgnoreDispersionMaxShots = {ignore_max}")
                
                if bracket_lines:
                    rank_lines.append(f"            {bracket} : struct.begin {{bpatch}}")
                    rank_lines.extend(bracket_lines)
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
    
    # Load weapon data
    weapon_stats = load_weapon_stats_map(patcher)
    print(f"DEBUG: Loaded stats for {len(weapon_stats)} weapons.")
    
    defaults = get_npc_base_defaults(patcher)
    patch_npc_vision(patcher)
    patch_vision_scanners(patcher)
    patch_weapons(patcher)
    patch_npc_attributes(patcher, weapon_stats)
    
    patcher.save_all("LongRangeCombat")

if __name__ == "__main__":
    main()
