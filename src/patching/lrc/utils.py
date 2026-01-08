import os
import re

import patching_script_general as psg
from patch_config import SOURCE_DUMP


def load_weapon_stats_map(patcher):
    """Parses WeaponGeneralSetupPrototypes.cfg to map SIDs to MaxAmmo, RecoilRadius, and FirstShotDispersionRadius."""
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


def get_npc_base_defaults(patcher):
    """Dynamically reads defaults from NPCBase in the source files."""
    filename = "GeneralNPCObjPrototypes.cfg"
    content = patcher.file_contents.get(filename)
    if not content:
        print(f"Error: {filename} not found. Returning default values.")
        return {"EnemyCouldBeVisibleMaxDistance": 5600.0, "LoseEnemyVisibilityTime": 4.0, "CheckEnemyTime": 20.0}

    struct_data = psg.get_struct_content(content, "NPCBase")
    if not struct_data: return {}

    cp_data = psg.get_struct_content(struct_data, "CombatParameters")
    target_data = cp_data if cp_data else struct_data

    return {"EnemyCouldBeVisibleMaxDistance": psg.get_value(target_data, "EnemyCouldBeVisibleMaxDistance"),
            "LoseEnemyVisibilityTime": psg.get_value(target_data, "LoseEnemyVisibilityTime"),
            "CheckEnemyTime": psg.get_value(target_data, "CheckEnemyTime")}


def get_struct_names(content):
    """Returns a list of top-level struct SIDs found in the content."""
    return re.findall(r'^(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
