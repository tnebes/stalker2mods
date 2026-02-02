import os
import re
import patching_script_general as psg
from patch_config import SOURCE_DUMP, get_mod_root

V1_HEAD = 6.0
V1_BODY = 2.0
V1_LIMBS = 1.0

# Calculation Constants
ROUNDING_PRECISION = 0.1

ZOMBIE_HEAD_MUL = 1.3
ZOMBIE_BODY_MUL = 1.1
ZOMBIE_LIMBS_MUL = 0.9

SPECIAL_RULES = {
    'Head': (3.0, 3.0),   # (Increment, Multiplier)
    'Body': (1.75, 2.0),  # (Increment, Multiplier)
    'Limbs': (0.5, 1.2)   # (Increment, Multiplier)
}

DEFAULT_HEAD_MUL = 1.35
DEFAULT_BODY_MUL = 1.2
DEFAULT_LIMBS_MUL = 1.1

# Logic Constants
DEFAULT_BONE_COEF = 1.0
SPECIAL_THRESHOLD = 1.0

# Path and Mod Constants
MOD_NAME = "RewardingHeadshots"
OBJ_PROTO_RELATIVE_DIR = 'Content/GameLite/GameData/ObjPrototypes'
TARGET_BASE_STRUCT = "NPCBase"

def get_original_coefs(struct_data):
    def find_coef(bone_name):
        pattern = rf'DamageBone\s*=\s*EDamageBone::{bone_name}\s+DamageCoef\s*=\s*([\d\.]+)'
        match = re.search(pattern, struct_data, re.IGNORECASE)
        return float(match.group(1)) if match else DEFAULT_BONE_COEF
    return {'Head': find_coef('Head'), 'Body': find_coef('Body'), 'Limbs': find_coef('Limbs')}

def calculate_coefs(original, is_zombie=False, is_special=False):
    if is_zombie:
        return {
            'Head': psg.round_to_nearest(original['Head'] * ZOMBIE_HEAD_MUL, ROUNDING_PRECISION),
            'Body': psg.round_to_nearest(original['Body'] * ZOMBIE_BODY_MUL, ROUNDING_PRECISION),
            'Limbs': psg.round_to_nearest(original['Limbs'] * ZOMBIE_LIMBS_MUL, ROUNDING_PRECISION)
        }
    elif is_special:
        res = {}
        for bone, (inc, mul) in SPECIAL_RULES.items():
            orig = original[bone]
            val = orig + inc if orig <= SPECIAL_THRESHOLD else orig * mul
            res[bone] = psg.round_to_nearest(val, ROUNDING_PRECISION)
        return res
    else:
        return {
            'Head': psg.round_to_nearest(original['Head'] * DEFAULT_HEAD_MUL, ROUNDING_PRECISION),
            'Body': psg.round_to_nearest(original['Body'] * DEFAULT_BODY_MUL, ROUNDING_PRECISION),
            'Limbs': psg.round_to_nearest(original['Limbs'] * DEFAULT_LIMBS_MUL, ROUNDING_PRECISION)
        }

def is_zombie_check(struct_name, patcher):
    current = struct_name
    visited = set()
    while current and current not in visited:
        if "zombie" in current.lower(): return True
        visited.add(current)
        node = patcher.get_struct(current)
        if node:
            prop = node.find_child("IsZombie")
            if prop and isinstance(prop, psg.cfg_ast.PropertyNode) and prop.value.lower() == "true":
                return True
        current = patcher.global_tree.get(current)
    return False

def find_defining_parent(struct_name, patcher):
    current = struct_name
    visited = set()
    while current and current not in visited:
        visited.add(current)
        node = patcher.get_struct(current)
        if node and node.find_child("BoneDamageCoefficients"):
            return node
        current = patcher.global_tree.get(current)
    return None

def extract_coefs_from_ast(node):
    res = {'Head': V1_HEAD, 'Body': V1_BODY, 'Limbs': V1_LIMBS}
    if not node: return res
    bdc = node.find_child("BoneDamageCoefficients")
    found_any = False
    if bdc and isinstance(bdc, psg.cfg_ast.StructNode):
        for child in bdc.children:
            if isinstance(child, psg.cfg_ast.StructNode): # Array element [*]
                bone = child.find_child("DamageBone")
                coef = child.find_child("DamageCoef")
                if bone and coef:
                    bone_name = bone.value.replace("EDamageBone::", "")
                    try:
                        res[bone_name] = float(coef.value)
                        found_any = True
                    except (ValueError, KeyError):
                        pass
    # If the struct exists but holds no coefficients, we return the defaults
    return res

def run():
    print(f"--- Running {MOD_NAME} Patching ---")
    mod_root = get_mod_root(MOD_NAME)
    patcher = psg.ModPatcher(SOURCE_DUMP, mod_root)
    
    obj_proto_abs_dir = os.path.join(SOURCE_DUMP, OBJ_PROTO_RELATIVE_DIR)
    files = [os.path.join(OBJ_PROTO_RELATIVE_DIR, f) for f in os.listdir(obj_proto_abs_dir) if f.endswith('.cfg')]
    patcher.load_files(files)
    
    target_structs = patcher.get_all_inheritors(TARGET_BASE_STRUCT)
    
    for s in target_structs:
        filename_info = patcher.struct_to_file.get(s)
        if not filename_info: continue
        filename, _ = filename_info
        
        is_z = is_zombie_check(s, patcher)
        root_node = patcher.get_struct(s, filename)
        has_local = root_node and root_node.find_child("BoneDamageCoefficients")
        
        defining_node = root_node if has_local else find_defining_parent(s, patcher)
        orig_coefs = extract_coefs_from_ast(defining_node) if defining_node else {'Head': V1_HEAD, 'Body': V1_BODY, 'Limbs': V1_LIMBS}
        
        final = calculate_coefs(orig_coefs, is_zombie=is_z, is_special=has_local and not is_z)
        
        bdc = [
            f"[*] : struct.begin\n         DamageBone = EDamageBone::Head\n         DamageCoef = {final['Head']:.1f}\n      struct.end",
            f"[*] : struct.begin\n         DamageBone = EDamageBone::Body\n         DamageCoef = {final['Body']:.1f}\n      struct.end",
            f"[*] : struct.begin\n         DamageBone = EDamageBone::Limbs\n         DamageCoef = {final['Limbs']:.1f}\n      struct.end"
        ]
        
        # Requirement: nested BoneDamageCoefficients should NOT have {bpatch}
        patch_text = psg.generate_bpatch(s, ["BoneDamageCoefficients"], values=bdc, bpatch_until=1)
        patcher.add_patch(filename, patch_text)
        
    patcher.save_all(MOD_NAME)
