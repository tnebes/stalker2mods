import sys
import os

# Add current dir and src to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.patching.v2.api import load_configuration, NodeWrapper

DEFAULT_CFG_PATH = r"C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\DifficultyPrototypes.cfg"
DIFFICULTIES = ["Easy", "Medium", "Hard", "Stalker"]

def extract():
    cfg = load_configuration(DEFAULT_CFG_PATH)
    
    all_keys = set()
    diff_nodes = {}
    for diff in DIFFICULTIES:
        n = cfg.getNodeByName(diff)
        if n:
            diff_nodes[diff] = n
    
    # Also get keys from Empty as baseline
    empty_node = cfg.getNodeByName("Empty")
    if empty_node:
        for child in empty_node:
            all_keys.add(child.key_or_name)

    for n in diff_nodes.values():
        for child in n:
             all_keys.add(child.key_or_name)

    foundation = {}
    # Filter out complex structs or metadata
    ignore = {"SID", "TitleSID", "DescriptionSID", "DefaultAimAssistPresetType", "TotalSaveLimits", "AllowedSaveTypes", "AutosaveAfterQuests", "CorpseSmartLoot", "AdditionalMechanicsEffects", "PsyPhantomNPCOverrides", "AgentCooldownMultipliers"}
    
    # Filter and sort keys
    clean_keys = sorted([k for k in all_keys if k and isinstance(k, str)])

    for key in clean_keys:
        if key in ignore: continue
        
        vals = []
        for diff in DIFFICULTIES:
            node = diff_nodes.get(diff)
            if node:
                effective = node.get_effective_node(key)
                if effective:
                    # Try to get value
                    n = effective.nodes[0]
                    if hasattr(n, 'value'):
                        c = str(n.value.raw)
                        # Try numeric
                        try:
                            if '.' in c: val = float(c)
                            else: val = int(c)
                        except:
                            if c.lower() == 'true': val = True
                            elif c.lower() == 'false': val = False
                            else: val = c
                        vals.append(val)
                    else:
                        vals.append(None)
                else:
                    vals.append(None)
            else:
                vals.append(None)
        
        if any(v is not None for v in vals):
            foundation[key] = vals
            
    return foundation

if __name__ == "__main__":
    foundation = extract()
    
    output_path = "src/difficulty/difficulty_values.py"
    with open(output_path, "w", encoding='utf-8') as f:
        f.write("# Foundation file for BetterDifficulty\n")
        f.write("# Format: { key : [Easy, Medium, Hard, Stalker] }\n")
        f.write("DIFFICULTY_VALUES = {\n")
        # Ensure keys are sorted for stability
        for key in sorted(foundation.keys()):
            vals = foundation[key]
            f.write(f"    {repr(key)}: {repr(vals)},\n")
        f.write("}\n")
    print(f"Foundation file updated at {output_path}")
