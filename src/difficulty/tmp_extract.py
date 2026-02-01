import os
import re
from typing import Dict, Any, List

DEFAULT_CFG_PATH = r"C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\DifficultyPrototypes.cfg"
DIFFICULTIES = ["Easy", "Medium", "Hard", "Stalker"]

def parse_cfg_for_foundation(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    prototypes = {}
    current_proto = None
    stack = []

    struct_start_re = re.compile(r'^(\w+)\s*:\s*struct\.begin(?:\s*\{refkey=(\w+)\})?')
    kv_re = re.compile(r'^\s*(\w+)\s*=\s*(.*)$')
    struct_end_re = re.compile(r'^\s*struct\.end')

    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue

        match = struct_start_re.match(line)
        if match:
            proto_name = match.group(1)
            ref_key = match.group(2)
            if not stack:
                current_proto = {"name": proto_name, "refkey": ref_key, "values": {}}
                prototypes[proto_name] = current_proto
            stack.append(proto_name)
            continue

        if struct_end_re.match(line):
            if stack: stack.pop()
            if not stack: current_proto = None
            continue

        if current_proto and len(stack) == 1:
            kv_match = kv_re.match(line)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip().rstrip(',')
                try:
                    if '.' in value: prototypes[current_proto["name"]]["values"][key] = float(value)
                    else: prototypes[current_proto["name"]]["values"][key] = int(value)
                except ValueError:
                    if value.lower() == 'true': prototypes[current_proto["name"]]["values"][key] = True
                    elif value.lower() == 'false': prototypes[current_proto["name"]]["values"][key] = False
                    else: prototypes[current_proto["name"]]["values"][key] = value

    def get_resolved(name, visited=None):
        if visited is None: visited = set()
        if name in visited or name not in prototypes: return {}
        visited.add(name)
        merged = get_resolved(prototypes[name]["refkey"], visited).copy()
        merged.update(prototypes[name]["values"])
        return merged

    all_keys = set()
    resolved = {}
    for diff in DIFFICULTIES:
        resolved[diff] = get_resolved(diff)
        all_keys.update(resolved[diff].keys())

    # We only care about keys that have numeric values or booleans
    # Ignore IDs and Strings that shouldn't be patched globally
    ignore = {"SID", "TitleSID", "DescriptionSID", "DefaultAimAssistPresetType"}
    
    foundation = {}
    for key in sorted(all_keys):
        if key in ignore: continue
        
        vals = []
        for diff in DIFFICULTIES:
            vals.append(resolved[diff].get(key))
        
        # Only keep if it has some values
        if any(v is not None for v in vals):
            foundation[key] = vals

    return foundation

if __name__ == "__main__":
    foundation = parse_cfg_for_foundation(DEFAULT_CFG_PATH)
    
    with open("src/difficulty/difficulty_values.py", "w") as f:
        f.write("# Foundation file for BetterDifficulty\n")
        f.write("# Format: { key : [Easy, Medium, Hard, Stalker] }\n")
        f.write("DIFFICULTY_VALUES = {\n")
        for key, vals in foundation.items():
            f.write(f"    {repr(key)}: {repr(vals)},\n")
        f.write("}\n")
    print("Foundation file generated at src/difficulty/difficulty_values.py")
