import os

# Base paths
SOURCE_DUMP = r'C:\dev\stalker2\cfg_dump_1-8-1\Stalker2'
MODS_DATA_ROOT = r'C:\dev\stalker2\mods\mods'

def get_mod_root(mod_name):
    """Returns the absolute path to the Stalker2 GameData root for a specific mod."""
    # Note: Traditional folder structure: <ModName>/<ModName>_P/Stalker2
    return os.path.join(MODS_DATA_ROOT, mod_name, f"{mod_name}_P", "Stalker2")

# Common file lists
LRC_FILES = [
    'Content/GameLite/GameData/ObjPrototypes/GeneralNPCObjPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/CharacterWeaponSettingsPrototypes/NPCWeaponSettingsPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/CharacterWeaponSettingsPrototypes/PlayerWeaponSettingsPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/CharacterWeaponSettingsPrototypes.cfg',
    'Content/GameLite/GameData/AIPrototypes/VisionScannerPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/WeaponAttributesPrototypes/NPCWeaponAttributesPrototypes.cfg',
    'Content/GameLite/GameData/WeaponData/WeaponGeneralSetupPrototypes.cfg'
]
