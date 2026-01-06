import os
import re
import patching_script_general as psg

# Constants
BASE_DIR = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2\Content\GameLite\GameData'
MOD_ROOT = r'C:\dev\stalker2\mods\mods\RewardingHeadshots\RewardingHeadshots_P\Stalker2\Content\GameLite\GameData'

V1_HEAD = 8.0
V1_BODY = 2.0
V1_LIMBS = 1.0

def get_original_coefs(struct_data):
    def find_coef(bone_name):
        pattern = rf'DamageBone\s*=\s*EDamageBone::{bone_name}\s+DamageCoef\s*=\s*([\d\.]+)'
        match = re.search(pattern, struct_data, re.IGNORECASE)
        return float(match.group(1)) if match else 1.0
    return {'Head': find_coef('Head'), 'Body': find_coef('Body'), 'Limbs': find_coef('Limbs')}

def calculate_coefs(original, is_zombie=False, is_special=False):
    if is_zombie:
        # Head: 30%, Body: 30%, Limbs: 25%
        return {
            'Head': psg.round_to_nearest(original['Head'] * 1.3, 0.5),
            'Body': psg.round_to_nearest(original['Body'] * 1.3, 0.5),
            'Limbs': psg.round_to_nearest(original['Limbs'] * 1.25, 0.5)
        }
    elif is_special:
        rules = {'Head': (4.0, 3.0), 'Body': (2.0, 2.0), 'Limbs': (0.5, 1.2)}
        res = {}
        for bone, (inc, mul) in rules.items():
            orig = original[bone]
            val = orig + inc if orig <= 1.0 else orig * mul
            res[bone] = psg.round_to_nearest(val, 0.5)
        return res
    else:
        # Head: 50%, Body: 30%, Limbs: 20%
        return {
            'Head': psg.round_to_nearest(original['Head'] * 1.5, 0.5),
            'Body': psg.round_to_nearest(original['Body'] * 1.3, 0.5),
            'Limbs': psg.round_to_nearest(original['Limbs'] * 1.2, 0.5)
        }

def is_zombie_check(struct_name, patcher):
    current = struct_name
    visited = set()
    while current and current not in visited:
        if "zombie" in current.lower(): return True
        visited.add(current)
        mapping = patcher.struct_to_file.get(current)
        if mapping:
            data = psg.get_struct_content(patcher.file_contents[mapping[0]], current)
            if data and re.search(r'^\s*IsZombie\s*=\s*true', data, re.MULTILINE | re.IGNORECASE):
                return True
        current = patcher.global_tree.get(current)
    return False

def find_defining_parent(struct_name, patcher):
    current = struct_name
    visited = set()
    while current and current not in visited:
        visited.add(current)
        mapping = patcher.struct_to_file.get(current)
        if mapping:
            data = psg.get_struct_content(patcher.file_contents[mapping[0]], current)
            if data and "BoneDamageCoefficients" in data:
                return data
        current = patcher.global_tree.get(current)
    return None

def main():
    patcher = psg.ModPatcher(BASE_DIR, MOD_ROOT)
    
    # We need all ObjPrototypes for inheritance
    obj_proto_dir = os.path.join(BASE_DIR, 'ObjPrototypes')
    files = [os.path.join('ObjPrototypes', f) for f in os.listdir(obj_proto_dir) if f.endswith('.cfg')]
    patcher.load_files(files)
    
    target_structs = patcher.get_all_inheritors("NPCBase")
    
    for s in target_structs:
        filename_info = patcher.struct_to_file.get(s)
        if not filename_info: continue
        filename, _ = filename_info
        
        content = patcher.file_contents[filename]
        data = psg.get_struct_content(content, s)
        
        is_z = is_zombie_check(s, patcher)
        has_local = data and "BoneDamageCoefficients" in data
        
        defining_data = data if has_local else find_defining_parent(s, patcher)
        orig_coefs = get_original_coefs(defining_data) if defining_data else {'Head': V1_HEAD, 'Body': V1_BODY, 'Limbs': V1_LIMBS}
        
        final = calculate_coefs(orig_coefs, is_zombie=is_z, is_special=has_local and not is_z)
        
        # Format BoneDamageCoefficients
        bdc = [
            f"[*] : struct.begin\n         DamageBone = EDamageBone::Head\n         DamageCoef = {final['Head']:.1f}\n      struct.end",
            f"[*] : struct.begin\n         DamageBone = EDamageBone::Body\n         DamageCoef = {final['Body']:.1f}\n      struct.end",
            f"[*] : struct.begin\n         DamageBone = EDamageBone::Limbs\n         DamageCoef = {final['Limbs']:.1f}\n      struct.end"
        ]
        
        # Use full struct.begin to avoid auto-adding {bpatch} to BoneDamageCoefficients
        patch_text = psg.generate_bpatch(s, ["BoneDamageCoefficients : struct.begin"], bdc)
        patcher.add_patch(filename, patch_text)
        
    patcher.save_all("RewardingHeadshots")

if __name__ == "__main__":
    main()
