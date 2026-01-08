import re
import patching_script_general as psg
from .constants import *
from .utils import get_npc_base_defaults, get_struct_names

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
    
    structs = re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
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
    npc_weapon_file = "NPCWeaponSettingsPrototypes.cfg"
    npc_content = patcher.file_contents.get(npc_weapon_file)

    if npc_content:
        shotgun_settings_sids = patcher.get_all_inheritors("TemplateShotgun")
        sniper_settings_sids = patcher.get_all_inheritors("TemplateSniper")
        pistol_settings_sids = patcher.get_all_inheritors("TemplatePistol")
        smg_settings_sids = patcher.get_all_inheritors("TemplateSMG")
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
            if s not in shotgun_settings_sids:
                is_sniper = s in sniper_settings_sids
                is_pistol = s in pistol_settings_sids
                is_smg = s in smg_settings_sids
                
                disp_mult = NPC_WEAPON_DISPERSION_MULT
                
                if is_sniper:
                    disp_mult *= SNIPER_DISPERSION_SCALING
                elif is_pistol:
                    disp_mult *= PISTOL_DISPERSION_SCALING
                elif is_smg:
                    disp_mult *= SMG_DISPERSION_SCALING

                for key in ["DispersionRadius", "DispersionRadiusZombieAddend"]:
                    val = psg.get_value(data, key)
                    if val is not None and isinstance(val, (int, float)):
                        new_val = val * disp_mult
                        props[key] = f"{new_val:.2f}"
            
            orig_bleed = psg.get_value(data, "BaseBleeding")
            if orig_bleed is not None and isinstance(orig_bleed, (int, float)):
                n_bleed = BLEEDING_BASE_MULT * orig_bleed + BLEEDING_BASE_ADD
                props["BaseBleeding"] = f"{n_bleed:.1f}"
            
            orig_chance = psg.get_value(data, "ChanceBleedingPerShot")
            if orig_chance is not None and isinstance(orig_chance, (int, float)):
                n_chance = min(orig_chance * BLEEDING_CHANCE_MULT, orig_chance - BLEEDING_CHANCE_SUB)
                n_chance = max(BLEEDING_CHANCE_MIN_FLOOR, n_chance) 
                props["ChanceBleedingPerShot"] = f"{round(n_chance * 100)}%"

            if props:
                patcher.add_patch(npc_weapon_file, psg.generate_bpatch(s, direct_properties=props))
                count += 1
        print(f"DEBUG: Applied weapon bleeding/dispersion bpatches to {count} structs in NPCWeaponSettingsPrototypes.cfg")

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
    
    shotgun_settings_sids = patcher.get_all_inheritors("TemplateShotgun")
    sniper_settings_sids = patcher.get_all_inheritors("TemplateSniper")
    
    structs = get_struct_names(content)
    count = 0
    
    for s in structs:
        s_clean = s.strip()
        if psg.is_special_npc(s_clean): continue
        if "RPG7" in s_clean.upper():
            continue
        data = psg.get_struct_content(content, s)
        
        ai_params = psg.get_struct_content(data, "AIParameters")
        if not ai_params: continue
        
        settings_sid_match = re.search(r'CharacterWeaponSettingsSID\s*=\s*(\w+)', data, re.IGNORECASE)
        settings_sid = settings_sid_match.group(1) if settings_sid_match else None

        is_shotgun = settings_sid in shotgun_settings_sids if settings_sid else False
        is_sniper = settings_sid in sniper_settings_sids if settings_sid else False
        
        w_stats = weapon_stats.get(settings_sid, {}) if settings_sid else {}
        if not w_stats and settings_sid:
            stripped_sid = settings_sid.replace("_NPC", "").replace("_Player", "")
            w_stats = weapon_stats.get(stripped_sid, {})

        max_ammo = w_stats.get('MaxAmmo', DEFAULT_MAX_AMMO) 
        fsd = w_stats.get('FirstShotDispersionRadius', DEFAULT_FSD) 

        behavior_types_full = psg.get_struct_content(ai_params, "BehaviorTypes")
        if not behavior_types_full: continue
        
        body = "\n".join(behavior_types_full.splitlines()[1:])
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
            config = RANK_CONFIGS.get(t, {"range_mult": 1.5, "burst_logic": {}})
            blogic = config.get("burst_logic", {})
            
            rank_lines = [f"         {t} : struct.begin {{bpatch}}"]
            has_any_rank_change = False
            
            dist_max = psg.get_value(t_data, "CombatEffectiveFireDistanceMax")
            dist_min = psg.get_value(t_data, "CombatEffectiveFireDistanceMin")
            if dist_max:
                new_dist_max = dist_max * config['range_mult']
                if is_shotgun:
                    new_dist_max *= SHOTGUN_MAX_DIST_MULT 
                
                current_min = dist_min if dist_min is not None else 0
                if new_dist_max <= current_min:
                    new_min = new_dist_max * MIN_DIST_FACTOR
                    rank_lines.append(f"            CombatEffectiveFireDistanceMin = {new_min:.1f}")
                
                rank_lines.append(f"            CombatEffectiveFireDistanceMax = {new_dist_max:.1f}")
                has_any_rank_change = True
            
            process_dispersion = not is_shotgun
            process_burst = not is_sniper and not is_shotgun

            for bracket in ["Short", "Medium", "Long"]:
                b_data = psg.get_struct_content(t_data, bracket)
                if not b_data: continue

                orig_min = psg.get_value(b_data, "MinShots") or 1
                orig_max = psg.get_value(b_data, "MaxShots") or 1
                new_min, new_max = orig_min, orig_max

                if process_burst:
                    mult = blogic.get("burst_mult", 1.0)
                    if bracket == "Long": mult *= blogic.get("long_burst_mult", 1.0)
                    elif bracket == "Medium": mult *= blogic.get("medium_burst_mult", 1.0)
                    elif bracket == "Short": mult *= blogic.get("short_burst_mult", 1.0)

                    new_min = int(orig_min * mult) + blogic.get("min_add", 0)
                    new_max = int(orig_max * mult) + blogic.get("max_add", 0)

                    if mult > 1.0 and new_max == orig_max:
                        new_max += 1

                    new_max = min(new_max, max_ammo)
                    new_min = min(new_min, new_max)
                    if new_min < 1: new_min = 1
                    if new_max < new_min: new_max = new_min

                ignore_min, ignore_max = None, None
                if process_dispersion:
                    floor_min = config.get("ignore_disp_min", {}).get(bracket, 0)
                    floor_max = config.get("ignore_disp_max", {}).get(bracket, 0)
                    chance_min = config.get("ignore_disp_chance_min", {}).get(bracket, 0)
                    chance_max = config.get("ignore_disp_chance_max", {}).get(bracket, 0)

                    ignore_min = max(floor_min, int(new_min * chance_min))
                    ignore_max = max(floor_max, int(new_min * chance_max))

                    if blogic.get("ignore_disp_max_inc_if_small") and new_max < IGNORE_DISP_LOW_AMMO_THRESHOLD:
                        ignore_max += 1

                    if bracket == "Long": ignore_max += blogic.get("guaranteed_add_long", 0)
                    if bracket == "Medium":
                        ignore_min += blogic.get("guaranteed_add_medium_min", 0)
                        ignore_max += blogic.get("guaranteed_add_medium_max", 0)

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

                    if is_sniper:
                        if t == "Experienced":
                            if bracket == "Short": 
                                ignore_max = 1
                            elif bracket == "Medium":
                                ignore_max = 1
                            elif bracket == "Long":
                                ignore_max = 0 # No chance for Experienced at Long
                        elif t == "Veteran":
                            if bracket == "Short": 
                                ignore_min = 1
                                ignore_max = 1
                            else: # Medium and Long
                                ignore_max = 1 # Chance to hit (might miss)
                                ignore_min = 0
                        elif t == "Master":
                            ignore_max = 1 # Always a chance (might miss)
                            if bracket in ["Short", "Medium"]:
                                ignore_min = 1 # Guaranteed hit (1/1)
                            else:
                                ignore_min = 0 # Might miss (0/1)

                    if t == "Zombie":
                        ignore_max = 1


                    if t == "Master" and bracket == "Long" and not is_sniper:
                        original_ignore_max = psg.get_value(b_data, "IgnoreDispersionMaxShots") or 0
                        if fsd < MASTER_FSD_THRESHOLD:
                             ignore_max = max(1, original_ignore_max) 
                        else:
                             ignore_max = max(0, original_ignore_max - 1) 
                    
                    ignore_max = min(ignore_max, new_max)
                    ignore_min = min(ignore_min, ignore_max)

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
