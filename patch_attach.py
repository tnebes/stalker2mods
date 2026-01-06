import os
import re
import patching_script_general as psg

# Constants
BASE_DIR = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\LessSway\LessSway_P\Stalker2\Content\GameLite\GameData'

EFFECTS = ["LessSwayX", "LessSwayY", "LessSwayTime"]
NESTED_PATH = ["Scope", "AimingEffects", "PlayerOnlyEffects"]

def main():
    patcher = psg.ModPatcher(BASE_DIR, MOD_ROOT)
    attach_file = 'ItemPrototypes/AttachPrototypes.cfg'
    patcher.load_files([attach_file])
    
    filename = os.path.basename(attach_file)
    content = patcher.file_contents[filename]
    
    structs = re.findall(r'^\s*(\w+)\s*:\s*struct\.begin', content, re.MULTILINE)
    
    for s in structs:
        # Check properties in chain
        current = s
        has_breath = False
        has_scope = False
        visited = set()
        while current and current not in visited:
            visited.add(current)
            data = psg.get_struct_content(content, current)
            if data:
                if not has_breath and "CanHoldBreath" in data:
                    has_breath = True
                if not has_scope and psg.has_nested_node(data, current, NESTED_PATH):
                    has_scope = True
            current = patcher.global_tree.get(current)
            
        if not (has_breath or has_scope):
            continue
            
        patch_props = {"CanHoldBreath": "true"} if has_breath else None
        patch_nested_path = NESTED_PATH if has_scope else None
        patch_values = EFFECTS if has_scope else None
        
        patch_text = psg.generate_bpatch(s, patch_nested_path, patch_values, root_properties=patch_props)
        patcher.add_patch(filename, patch_text)

    patcher.save_all("LessSway")

if __name__ == "__main__":
    main()
