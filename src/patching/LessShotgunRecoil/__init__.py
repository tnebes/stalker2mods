import os
import re
import sys

# Add src to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import patching_script_general as psg
from patch_config import SOURCE_DUMP, get_mod_root

def run():
    SHOTGUN_RECOIL_MULTIPLIER = 0.25
    SHOTGUN_RECOIL_NORMALIZATION_MULTIPLIER = 0.35
    SHOTGUN_CAMERA_SHAKE_SCALE = 0.35

    print("--- Running LessShotgunRecoil Patching ---")
    mod_name = "LessShotgunRecoil"
    mod_root = get_mod_root(mod_name)
    patcher = psg.ModPatcher(SOURCE_DUMP, mod_root)
    
    weapon_rel_path = 'Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg'
    camera_shake_rel_path = 'Content/GameLite/GameData/CameraShakePrototypes.cfg'
    patcher.load_files([weapon_rel_path, camera_shake_rel_path])
    
    weapon_filename = os.path.basename(weapon_rel_path)
    camera_shake_filename = os.path.basename(camera_shake_rel_path)
    
    # Identify all weapons inheriting from TemplateShotgun
    inheritors = patcher.get_all_inheritors('TemplateShotgun')
    
    shotgun_camera_shakes = set()
    
    for s in inheritors:
        # 1. Patch Recoil and Normalization in WeaponGeneralSetupPrototypes.cfg
        # Get the effective RecoilRadius and RadiusNormalizationInterval for this struct
        recoil_val = patcher.get_property_value(s, 'RecoilRadius', weapon_filename)
        normalization_val = patcher.get_property_value(s, 'RadiusNormalizationInterval', weapon_filename)
        
        # Track camera shakes for patching in the separate file
        camera_shake_sid = patcher.get_property_value(s, 'ShootCameraShakePrototypeSID', weapon_filename)
        if camera_shake_sid:
            print(f"Shotgun {s} uses camera shake: {camera_shake_sid}")
            shotgun_camera_shakes.add(camera_shake_sid)

        patches_applied = []
        
        # Build a combined patch if we have values to patch
        if (recoil_val is not None and isinstance(recoil_val, (int, float)) and recoil_val > 0) or \
           (normalization_val is not None and isinstance(normalization_val, (int, float)) and normalization_val > 0):
            
            # Start building the patch manually
            patch_lines = [f"{s} : struct.begin {{bpatch}}"]
            patch_lines.append("   RecoilParams : struct.begin {bpatch}")
            
            # Add RecoilRadius if applicable
            if recoil_val is not None and isinstance(recoil_val, (int, float)) and recoil_val > 0:
                new_recoil = recoil_val * SHOTGUN_RECOIL_MULTIPLIER
                patch_lines.append(f"      RecoilRadius = {new_recoil:.1f}")
                patches_applied.append(f"RecoilRadius: {recoil_val} -> {new_recoil:.1f}")
            
            # Add nested RadiusNormalizationInterval if applicable
            if normalization_val is not None and isinstance(normalization_val, (int, float)) and normalization_val > 0:
                new_normalization = normalization_val * SHOTGUN_RECOIL_NORMALIZATION_MULTIPLIER
                patch_lines.append("      ShootingStateParams : struct.begin {bpatch}")
                patch_lines.append("         RadiusNormalizationModifiers : struct.begin {bpatch}")
                patch_lines.append(f"            RadiusNormalizationInterval = {new_normalization:.2f}")
                patch_lines.append("         struct.end")
                patch_lines.append("      struct.end")
                patches_applied.append(f"RadiusNormalizationInterval: {normalization_val} -> {new_normalization:.2f}")
            
            # Close RecoilParams and main struct
            patch_lines.append("   struct.end")
            patch_lines.append("struct.end")
            
            # Add the combined patch
            patcher.add_patch(weapon_filename, "\n".join(patch_lines))
            print(f"Patched {s}: {', '.join(patches_applied)}")
            
    # 2. Patch CameraShakePrototypes.cfg
    print(f"--- Patching {len(shotgun_camera_shakes)} unique Shotgun Camera Shakes ---")
    for cs_sid in sorted(list(shotgun_camera_shakes)):
        if cs_sid == 'Empty' or not cs_sid:
            continue
            
        # Patch each camera shake SID with the new Scale
        patch_lines = [f"{cs_sid} : struct.begin {{bpatch}}"]
        patch_lines.append(f"   Scale = {SHOTGUN_CAMERA_SHAKE_SCALE}")
        patch_lines.append("struct.end")
        
        patcher.add_patch(camera_shake_filename, "\n".join(patch_lines))
        print(f"Patched CameraShake {cs_sid} with Scale = {SHOTGUN_CAMERA_SHAKE_SCALE}")
            
    patcher.save_all(mod_name)

if __name__ == "__main__":
    run()
