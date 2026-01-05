# LessSway Mod for S.T.A.L.K.E.R. 2

**LessSway** is a quality-of-life mod designed to improve aiming stability by significantly reducing weapon sway and enabling breath-holding mechanics for a wider range of attachments.

## Features

- **Reduced Weapon Sway**: Reduces `IdleSwayX`, `IdleSwayY`, and `IdleSwayTime` triggers by **50%**, making aiming smoother and less jittery.
- **Universal Breath Holding**: Enables the `CanHoldBreath` property on relevant scope and sight attachments that previously might not have supported it.
- **Compatibility First**: Uses the modern `{bpatch}` method to inject changes, ensuring high compatibility with other mods that modify attachment or weapon prototypes.

## How It Works

The mod utilizes a custom Python patching system (`patch_attach.py` and `patch_weapons.py`) to scan the game's original configuration files. It intelligently identifies:

1.  All attachments that have scope or aiming capabilities.
2.  The inheritance chain of these items.

It then generates a `_patch` configuration file that:

- Appends the `LessSway` effect modifiers to the `PlayerOnlyEffects` array.
- Sets `CanHoldBreath = true`.

This automated approach ensures that even if the base game updates or if you use other mods that alter weapon inheritance, LessSway can simply be re-run to target the correct nodes without overwriting entire files.

## Installation

1.  Copy the `LessSway_P.pak` file to your `Stalker2/GameData/GameLite/Content/Paks/~mods/` directory.
    - _Note: If `~mods` does not exist, create it._

## Development

If you wish to modify the sway values or logic:

1.  Edit `patch_attach.py` or the `LessSway` effect definitions in `EffectPrototypes_patch_LessSway.cfg`.
2.  Run the python scripts to regenerate the patch files.
