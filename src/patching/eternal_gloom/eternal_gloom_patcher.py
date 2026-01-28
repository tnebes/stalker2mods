import os
import sys

# Ensure project root is in path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
sys.path.append(project_root)

from src.patching.v2.api import load_configuration, Node, BPATCH, NodeWrapper, StructNode
from src.patching.v2.patcher import Patcher

# --- MOD CONFIGURATION ---
MOD_ROOT = r"C:\dev\stalker2\mods\mods\EternalGloom\EternalGloom_P"
MOD_NAME = "EternalGloom"
WEATHER_SELECTION_PATH = "WeatherSelectionPrototypes.cfg"
WEATHER_PROTOTYPES_DIR = "WeatherPrototypes"

is_extreme = "extreme" in sys.argv
is_debug = "debug" in sys.argv

print(f"--- Initializing Eternal Gloom Patcher ---")
p = Patcher()

# 1. GUARDIAN Protocol
p.inject_guardian(MOD_ROOT, MOD_NAME)

# Atmosphere settings
GLOOMY_TYPES = ["Fogy", "Stormy", "Rainy", "Thundery"]
HAPPY_TYPES = ["Clearly"]

# 2. SELECTION: Gloom Atmosphere
if not is_debug:
    print("Patching Weather Selection for Gloom atmosphere (Calculated)...")
    sel_cfg = load_configuration(WEATHER_SELECTION_PATH)
    for node in sel_cfg.doc.nodes:
        if isinstance(node, StructNode):
            region = NodeWrapper(node)
            for weather in region:
                name = weather.key_or_name
                if not name: continue
                
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
                            weather['BlendWeight'] = "50.0f"
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

    sel_patch = p.generate_patch(WEATHER_SELECTION_PATH, sel_cfg.doc)
    p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=sel_patch, is_prototype=True)
else:
    print("Debug mode: Skipping Weather Selection patch.")

# 3. VISUALS: Prototype Scheme (Subfolders + _patch_)
if is_extreme or is_debug:
    print(f"\n--- Patching Visual Templates (Prototype Scheme) ---")
    base_weather_dir = os.path.join(p.base_path, WEATHER_PROTOTYPES_DIR)
    all_weather_files = [f for f in os.listdir(base_weather_dir) if f.endswith(".cfg")]
    
    for v_filename in all_weather_files:
        v_path = os.path.join(WEATHER_PROTOTYPES_DIR, v_filename)
        v_cfg = load_configuration(v_path)
        if not v_cfg.doc.nodes: continue
        
        modified = False
        for node in v_cfg.doc.nodes:
            if not isinstance(node, StructNode): continue
            root = NodeWrapper(node)
            if 'WeatherParams' in root:
                for params in root['WeatherParams']:
                    modified = True
                    
                    if is_extreme:
                        # Extreme mode: significantly lower intensity
                        if 'SkyLight' in params:
                            params['SkyLight']['Intensity'] = "0.05f"
                        if 'ColorGrading' in params:
                            params['ColorGrading']['ColorSaturation']['W'] = "0.2f"
                    
                    if is_debug:
                        # Debug mode: Neon effects for verification
                        if 'ColorGrading' in params:
                            params['ColorGrading']['ColorSaturation']['W'] = "0.0f"
                        if 'SkyLight' in params:
                            params['SkyLight']['Intensity'] = "0.01f"
                        params['FogInscatteringColor'] = Node("FogInscatteringColor", {
                            "R": "1.0f", "G": "0.0f", "B": "1.0f", "A": "1.0f"
                        }, attributes=BPATCH)

        if modified:
            v_patch = p.generate_patch(v_path, v_cfg.doc)
            p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=v_patch, is_prototype=True)

print(f"\nAll tasks complete. Guardian is in ObjPrototypes/Player.")
