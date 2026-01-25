import os
import re

import patching_script_general as psg
from patch_config import SOURCE_DUMP


def load_weapon_stats_map(patcher):
    """Parses WeaponGeneralSetupPrototypes.cfg to map SIDs to MaxAmmo, RecoilRadius, and FirstShotDispersionRadius."""
    weapon_rel_path = "Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg"
    patcher.load_files([weapon_rel_path])
    filename = os.path.basename(weapon_rel_path)
    
    stats_map = {}
    if filename in patcher.file_asts:
        for node in patcher.file_asts[filename]:
            if isinstance(node, psg.cfg_ast.StructNode):
                sid_node = node.find_child("SID")
                if sid_node and isinstance(sid_node, psg.cfg_ast.PropertyNode):
                    sid = sid_node.value
                    stats = {}
                    
                    for key in ['MaxAmmo', 'RecoilRadius', 'FirstShotDispersionRadius']:
                        val = patcher.get_property_value(sid, key, filename)
                        if val is not None:
                            stats[key] = val
                    stats_map[sid] = stats
    return stats_map


def get_npc_base_defaults(patcher):
    """Dynamically reads defaults from NPCBase in the source files."""
    filename = "GeneralNPCObjPrototypes.cfg"
    # Ensure file is loaded
    patcher.load_files([f"Content/GameLite/GameData/ObjPrototypes/{filename}"])
    
    node = patcher.get_struct("NPCBase", filename)
    if not node:
        print(f"Error: NPCBase not found in {filename}. Returning default values.")
        return {"EnemyCouldBeVisibleMaxDistance": 5600.0, "LoseEnemyVisibilityTime": 4.0, "CheckEnemyTime": 20.0}

    return {
        "EnemyCouldBeVisibleMaxDistance": patcher.get_property_value("NPCBase", "EnemyCouldBeVisibleMaxDistance", filename),
        "LoseEnemyVisibilityTime": patcher.get_property_value("NPCBase", "LoseEnemyVisibilityTime", filename),
        "CheckEnemyTime": patcher.get_property_value("NPCBase", "CheckEnemyTime", filename)
    }


def get_struct_names(patcher, filename):
    """Returns a list of top-level struct SIDs found in the content."""
    if filename in patcher.file_asts:
        return [node.name for node in patcher.file_asts[filename] if isinstance(node, psg.cfg_ast.StructNode)]
    return []
