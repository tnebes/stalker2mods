import os
import sys

# Ensure project root is in path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.append(project_root)

from src.patching.v2.api import load_configuration, Node, BPATCH, NodeWrapper, StructNode
from src.patching.v2.patcher import Patcher

# Mod configuration
MOD_ROOT = r"C:\dev\stalker2\mods\mods\EternalGloom\EternalGloom_P"
MOD_NAME = "EternalGloom"
CONFIG_REL_PATH = "WeatherSelectionPrototypes.cfg"

# Atmosphere settings
GLOOMY_TYPES = ["Fogy", "Stormy", "Rainy", "Thundery"]
HAPPY_TYPES = ["Clearly"]

print("--- Initializing Eternal Gloom Patcher ---")
print(f"Loading base configuration...")
cfg = load_configuration(CONFIG_REL_PATH)

for node in cfg.doc.nodes:
    if not isinstance(node, StructNode):
        continue
    
    region = NodeWrapper(node)
    region_name = region.key_or_name
    print(f"Applying gloom to: {region_name}")

    for weather in region:
        name = weather.key_or_name
        
        # Extinguish the sun
        if name in HAPPY_TYPES:
            weather['BlendWeight'] = "0.0f"
            if 'WeatherDurationMin' in weather: weather['WeatherDurationMin'] = "5.0f"
            if 'WeatherDurationMax' in weather: weather['WeatherDurationMax'] = "15.0f"

        # Amplify the darkness
        elif name in GLOOMY_TYPES:
            # Increase probability
            if 'BlendWeight' in weather:
                current_weight = weather['BlendWeight'].to_float()
                if current_weight == 0:
                    weather['BlendWeight'] = "50.0f" # Force it to appear if it didn't before
                else:
                    weather['BlendWeight'].scale(4.0)
            
            # Make it linger
            if 'WeatherDurationMin' in weather: weather['WeatherDurationMin'].scale(3.0)
            if 'WeatherDurationMax' in weather: weather['WeatherDurationMax'].scale(3.0)
            
            # Allow it to repeat indefinitely
            if 'MaximumRepeatAmount' in weather: weather['MaximumRepeatAmount'] = "-1"

        # Frequent Blowouts
        elif name == "Emission":
            if 'MaximumCooldownWeatherAmount' in weather:
                # Halve the cooldown between emissions
                weather['MaximumCooldownWeatherAmount'].scale(0.4)

print("\n--- Generating Soul-Crushing Patch ---")
p = Patcher()
patch_doc = p.generate_patch(CONFIG_REL_PATH, cfg.doc)

# Save following the proper hierarchy
p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=patch_doc)

print(f"\nSuccess! The Zone is now a place of eternal suffering at: {MOD_ROOT}")
