import os
import sys

# Ensure project root is in path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.append(project_root)

from src.patching.v2.api import load_configuration
from src.patching.v2.patcher import Patcher

# CONFIG_REL_PATH is relative to GameData
CONFIG_REL_PATH = "WeatherSelectionPrototypes.cfg"

# Mod Info
MOD_ROOT = r"C:\dev\stalker2\mods\mods\SunnierZone\SunnierZone_P"
MOD_NAME = "SunnierZone"

# 1. Load configuration (uses DEFAULT_DUMP_DIR and tracks relative path internally)
print(f"Loading {CONFIG_REL_PATH}...")
cfg = load_configuration(CONFIG_REL_PATH)

# 2. Modify weather BlendWeights
SUNNY = "Clearly"
OTHERS = ["Cloudy", "Fogy", "Stormy", "LightRainy", "Rainy", "Thundery"]

for node in cfg.doc.nodes:
    if hasattr(node, "children"):
        for weather_node in node:
            name = weather_node.key_or_name
            if name == SUNNY:
                weather_node['BlendWeight'].scale(1.5)
            elif name in OTHERS:
                weather_node['BlendWeight'].scale(0.5)

# 3. Generate minimal patch (automatically uses Patcher's default dump dir)
print("\nGenerating minimal patch...")
p = Patcher()
patch_doc = p.generate_patch(CONFIG_REL_PATH, cfg.doc)

# 4. Save patch with proper hierarchy (automatically resolves target path)
print("\nSaving with proper hierarchy...")
p.save_patch(MOD_ROOT, MOD_NAME, patch_doc=patch_doc)

print("\nSuccess! Mod published to SunnierZone_P folder.")
