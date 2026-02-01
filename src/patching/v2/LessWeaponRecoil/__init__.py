import os
import sys

# Add the project root to sys.path
# This script is located in src/patching/v2/LessWeaponRecoil/__init__.py
# Root is 4 levels up
file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(file_dir, "../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also ensure v1 directory is in path for patch_config if needed, 
# though we use absolute import via project_root
v1_dir = os.path.join(project_root, "src", "patching", "v1")
if v1_dir not in sys.path:
    sys.path.insert(0, v1_dir)

from src.patching.v2.api import load_configuration, NodeWrapper
from src.patching.v2.patcher import Patcher
from src.patching.v2.ast import StructNode
from src.patching.v1.patch_config import get_mod_root, SOURCE_DUMP

def run():
    WEAPON_RECOIL_RADIUS_MULT = 0.66
    WEAPON_RECOIL_NORMALIZATION_MULT = 0.50
    CAMERA_SHAKE_SCALE_MULT = 0.50

    mod_name = "LessWeaponRecoil"
    # v2 Patcher expects the directory that CONTAINS the 'Stalker2' folder.
    # get_mod_root returns .../Stalker2, so we take the parent.
    mod_root = os.path.dirname(get_mod_root(mod_name))
    
    # v2 Patcher expects path to GameData subdirectory
    v2_base_dump = os.path.join(SOURCE_DUMP, "Content", "GameLite", "GameData")
    
    patcher = Patcher(v2_base_dump)
    
    print(f"--- Running {mod_name} Patching ---")

    # 1. Patch WeaponGeneralSetupPrototypes.cfg
    weapon_rel_path = 'WeaponData/WeaponGeneralSetupPrototypes.cfg'
    print(f"Processing {weapon_rel_path}...")
    try:
        cfg = load_configuration(weapon_rel_path, base_dump_path=v2_base_dump)
    except Exception as e:
        print(f"Error loading {weapon_rel_path}: {e}")
        return

    weapon_count = 0
    weapon_shakes = set()
    for node in cfg.doc.nodes:
        if isinstance(node, StructNode):
            wrapper = NodeWrapper(node)
            
            # Track camera shakes
            if 'ShootCameraShakePrototypeSID' in wrapper:
                try:
                    cs_sid = str(wrapper['ShootCameraShakePrototypeSID'].nodes[0].value)
                    if cs_sid and cs_sid.lower() != 'empty':
                        weapon_shakes.add(cs_sid)
                except (AttributeError, IndexError):
                    pass

            # Check if it has RecoilParams
            if 'RecoilParams' in wrapper:
                recoil_params = wrapper['RecoilParams']
                
                # Patch RecoilRadius
                if 'RecoilRadius' in recoil_params:
                    recoil_params['RecoilRadius'].scale(WEAPON_RECOIL_RADIUS_MULT)
                
                # Patch RadiusNormalizationInterval
                if 'ShootingStateParams' in recoil_params:
                    shooting_params = recoil_params['ShootingStateParams']
                    if 'RadiusNormalizationModifiers' in shooting_params:
                        norm_mods = shooting_params['RadiusNormalizationModifiers']
                        if 'RadiusNormalizationInterval' in norm_mods:
                            norm_mods['RadiusNormalizationInterval'].scale(WEAPON_RECOIL_NORMALIZATION_MULT)
                
                weapon_count += 1
    
    print(f"Modified {weapon_count} weapon structures.")
    print(f"Found {len(weapon_shakes)} unique weapon camera shakes.")
    
    weapon_patch = patcher.generate_patch(weapon_rel_path, cfg.doc)
    patcher.save_patch(mod_root, mod_name, patch_doc=weapon_patch)

    # 2. Patch CameraShakePrototypes.cfg
    camera_shake_rel_path = 'CameraShakePrototypes.cfg'
    print(f"Processing {camera_shake_rel_path}...")
    try:
        cfg_cs = load_configuration(camera_shake_rel_path, base_dump_path=v2_base_dump)
        # Load a clean copy for resolving inheritance to avoid cascading modified values
        clean_cfg_cs = load_configuration(camera_shake_rel_path, base_dump_path=v2_base_dump)
    except Exception as e:
        print(f"Error loading {camera_shake_rel_path}: {e}")
        return
    
    cs_count = 0
    for node in cfg_cs.doc.nodes:
        if isinstance(node, StructNode):
            wrapper = NodeWrapper(node, cfg_cs.doc)
            sid = node.name
            sid_prop = ""
            if 'SID' in node:
                try:
                    sid_prop = str(node['SID'].value)
                except AttributeError:
                    pass

            if sid in weapon_shakes or sid_prop in weapon_shakes or "Shoot" in sid or "Shoot" in sid_prop:
                # Use the clean doc for inheritance resolution
                effective_scale_wrapper = wrapper.get_effective_node('Scale', resolve_doc=clean_cfg_cs.doc)
                
                if effective_scale_wrapper:
                    base_val = effective_scale_wrapper.to_float()
                    if base_val is not None:
                        new_val = base_val * CAMERA_SHAKE_SCALE_MULT
                        # Use set_effective_property to inherit the format (float vs float_f)
                        wrapper.set_effective_property('Scale', new_val, original_node=effective_scale_wrapper)
                        cs_count += 1
                else:
                    new_val = 1.0 * CAMERA_SHAKE_SCALE_MULT
                    # Fallback to standard float if no effective source found
                    wrapper['Scale'] = new_val
                    cs_count += 1

    print(f"Modified {cs_count} camera shake structures.")
    cs_patch = patcher.generate_patch(camera_shake_rel_path, cfg_cs.doc)
    patcher.save_patch(mod_root, mod_name, patch_doc=cs_patch)

    print(f"--- {mod_name} Patching Complete ---")

if __name__ == "__main__":
    run()
