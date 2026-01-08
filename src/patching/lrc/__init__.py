import patching_script_general as psg
from patch_config import SOURCE_DUMP, get_mod_root, LRC_FILES
from .logic import patch_npc_vision, patch_vision_scanners, patch_weapons, patch_npc_attributes
from .utils import load_weapon_stats_map

def run():
    print("--- Running LongRangeCombat Patching ---")
    mod_root = get_mod_root("LongRangeCombat")
    patcher = psg.ModPatcher(SOURCE_DUMP, mod_root)
    patcher.load_files(LRC_FILES)
    
    weapon_stats = load_weapon_stats_map(patcher)
    print(f"DEBUG: Loaded stats for {len(weapon_stats)} weapons.")
    
    patch_npc_vision(patcher)
    patch_vision_scanners(patcher)
    patch_weapons(patcher)
    patch_npc_attributes(patcher, weapon_stats)
    
    patcher.save_all("LongRangeCombat")
