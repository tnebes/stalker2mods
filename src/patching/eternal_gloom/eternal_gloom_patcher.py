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
OBJ_PROTOTYPES_PATH = "ObjPrototypes.cfg"

# --- GUARDIAN VALUES ---
GUARDIAN_SPRINT_SPEED = "3000.0f"

is_extreme = "extreme" in sys.argv
is_debug = "debug" in sys.argv

print(f"--- Initializing Eternal Gloom Patcher ---")
p = Patcher()

# 1. GUARDIAN: ObjPrototypes.cfg (Prototype)
print("Injecting Guardian into ObjPrototypes (Player SID)...")
obj_cfg = load_configuration(OBJ_PROTOTYPES_PATH)
player = obj_cfg.getNodeByName("Player")
if player:
    player['MovementParams']['SprintSpeed'] = GUARDIAN_SPRINT_SPEED
    obj_patch = p.generate_patch(OBJ_PROTOTYPES_PATH, obj_cfg.doc)
    p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=obj_patch, is_prototype=True)

# 2. SELECTION: Eternal Blowout
print("Patching Weather Selection...")
sel_cfg = load_configuration(WEATHER_SELECTION_PATH)
for node in sel_cfg.doc.nodes:
    if isinstance(node, StructNode):
        region = NodeWrapper(node)
        for weather in region:
            name = weather.key_or_name
            if name == "Clearly":
                weather['BlendWeight'] = "0.0f"
            elif name == "Emission":
                weather['BlendWeight'] = "1000.0f"

sel_patch = p.generate_patch(WEATHER_SELECTION_PATH, sel_cfg.doc)
p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=sel_patch, is_prototype=True, flatten=True)

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
                    if is_debug:
                        if 'ColorGrading' in params:
                            params['ColorGrading']['ColorSaturation']['W'] = "0.0f"
                        if 'SkyLight' in params:
                            params['SkyLight']['Intensity'] = "0.01f"
                        params['FogInscatteringColor'] = Node("FogInscatteringColor", {
                            "R": "1.0f", "G": "0.0f", "B": "1.0f", "A": "1.0f"
                        }, attributes=BPATCH)

        if modified:
            v_patch = p.generate_patch(v_path, v_cfg.doc)
            p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=v_patch, is_prototype=True, flatten=True)

print(f"\nAll tasks complete. Guardian is in ObjPrototypes/Player.")
