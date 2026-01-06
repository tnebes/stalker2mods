import os
import re
import math
import patching_script_general as psg

# Constants
# Base paths
BASE_DIR = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData\ObjPrototypes'
PATCH_ROOT = r'C:\dev\stalker2\mods\mods\RewardingHeadshots\RewardingHeadshots_P\Stalker2\Content\GameLite\GameData\ObjPrototypes'

# Target Values v1 (Default inheritors)
V1_HEAD = 50.0 # 8.0
V1_BODY = 50.0 # 2.0
V1_LIMBS = 50.0 # 1.0

def round_up_05(val):
    """Rounds up to the nearest 0.5."""
    return math.ceil(val * 2) / 2.0

def get_original_coefs(struct_data):
    """Extracts Head, Body, Limbs coefficients from a struct's content."""
    # Find the BoneDamageCoefficients block start to limit range if possible, 
    # but for NPCs these values usually only appear in that block anyway.
    
    # Helper to find coef for a bone
    def find_coef(bone_name):
        # Match pattern within BoneDamageCoefficients context
        pattern = rf'DamageBone\s*=\s*EDamageBone::{bone_name}\s+DamageCoef\s*=\s*([\d\.]+)'
        match = re.search(pattern, struct_data, re.IGNORECASE)
        return float(match.group(1)) if match else 1.0

    return {
        'Head': find_coef('Head'),
        'Body': find_coef('Body'),
        'Limbs': find_coef('Limbs')
    }

def calculate_special_coefs(original_coefs):
    """Applies dynamic calculation for special NPCs."""
    results = {}
    
    rules = {
        'Head': {'inc': 4.0, 'mul': 3.0},
        'Body': {'inc': 2.0, 'mul': 2.0},
        'Limbs': {'inc': 0.5, 'mul': 1.2}
    }
    
    for bone, rule in rules.items():
        orig = original_coefs[bone]
        if orig <= 1.0:
            val = orig + rule['inc']
        else:
            val = orig * rule['mul']
        results[bone] = round_up_05(val)
        
    return results

def generate_bone_damage_coefficients(head, body, limbs):
    return (
        "   BoneDamageCoefficients : struct.begin\n"
        "      [*] : struct.begin\n"
        f"         DamageBone = EDamageBone::Head\n"
        f"         DamageCoef = {head}\n"
        "      struct.end\n"
        "      [*] : struct.begin\n"
        f"         DamageBone = EDamageBone::Body\n"
        f"         DamageCoef = {body}\n"
        "      struct.end\n"
        "      [*] : struct.begin\n"
        f"         DamageBone = EDamageBone::Limbs\n"
        f"         DamageCoef = {limbs}\n"
        "      struct.end\n"
        "   struct.end"
    )

def main():
    if not os.path.exists(BASE_DIR):
        print(f"Base directory not found: {BASE_DIR}")
        return

    print(f"Analyzing directory {BASE_DIR}...")
    
    # We need to build a global inheritance tree first by reading all files
    global_tree = {}
    file_contents = {}
    struct_to_file = {}
    
    cfg_files = [f for f in os.listdir(BASE_DIR) if f.endswith(".cfg")]
    for filename in cfg_files:
        file_path = os.path.join(BASE_DIR, filename)
        tree = psg.get_inheritance_tree(file_path)
        global_tree.update(tree)
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            file_contents[filename] = content
            
            # Record which file each struct belongs to
            for struct_name in tree.keys():
                struct_to_file[struct_name] = filename

    # Find all inheritors of NPCBase
    target_structs = psg.find_all_inheritors(global_tree, "NPCBase")
    target_structs.add("NPCBase")

    print(f"Found {len(target_structs)} structs inheriting from NPCBase.")

    # Group patches by file
    patches_by_file = {}

    for struct_name in sorted(target_structs):
        filename = struct_to_file.get(struct_name)
        if not filename:
            # Struct might be defined in the global tree but not found in the files we just read
            # This can happen if it's in a file we skipped or a base file
            continue

        content = file_contents[filename]
        struct_data = psg.get_struct_content(content, struct_name)
        if not struct_data:
            continue
            
        # Check if this specific struct has its own BoneDamageCoefficients
        has_local_oob = re.search(r'^\s*BoneDamageCoefficients\s*:\s*struct\.begin', struct_data, re.MULTILINE | re.IGNORECASE)
        
        if has_local_oob:
            orig_coefs = get_original_coefs(struct_data)
            if orig_coefs:
                special_coefs = calculate_special_coefs(orig_coefs)
                h, b, l = special_coefs['Head'], special_coefs['Body'], special_coefs['Limbs']
            else:
                # Fallback if parsing fails
                h, b, l = 12.0, 3.0, 1.5
            coefs = generate_bone_damage_coefficients(h, b, l)
        else:
            coefs = generate_bone_damage_coefficients(V1_HEAD, V1_BODY, V1_LIMBS)

        patch = f"{struct_name} : struct.begin {{bpatch}}\n{coefs}\nstruct.end"
        
        if filename not in patches_by_file:
            patches_by_file[filename] = []
        patches_by_file[filename].append(patch)

    # Write patches using the Folder Technique
    for filename, patches in patches_by_file.items():
        base_name = os.path.splitext(filename)[0]
        # Folder Technique: ObjPrototypes/FileName/FileName_patch_ModName.cfg
        patch_dir = os.path.join(PATCH_ROOT, base_name)
        patch_file = os.path.join(patch_dir, f"{base_name}_patch_RewardingHeadshots.cfg")
        
        os.makedirs(patch_dir, exist_ok=True)
        print(f"Writing {len(patches)} patches to {patch_file}...")
        with open(patch_file, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(patches))

    print("Done.")

if __name__ == "__main__":
    main()
