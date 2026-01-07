from .curves import get_rank_configs

# Multipliers
VISION_DISTANCE_MULT = 0.9  
VISION_CHECK_TIME_MULT = 1.5 
VISION_LOSE_TIME_MULT = 2 
PLAYER_STEALTH_COMFORT_MULT = 0.8
PLAYER_STEALTH_LOUDNESS_MULT = 0.8
NPC_WEAPON_DISPERSION_MULT = 0.05
NPC_RANGE_MULT = 1.5             

DEBUG_GUARANTEED_HITS = False

# Rank Configurations (Generated via curves.py)
RANK_CONFIGS = get_rank_configs()
