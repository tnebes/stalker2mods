# S.T.A.L.K.E.R. 2 Config Modding Guide

This guide aggregates essential rules, naming conventions, and best practices for modding S.T.A.L.K.E.R. 2 configuration files (`.cfg`), based on community findings and documentation.

## 1. Naming Conventions & Files

There are two main types of configuration files you will encounter, each requiring a specific naming pattern for patches.

### A. Prototype CFGs (SIDs)

Files that define objects using String IDs (SIDs), such as `ItemPrototypes.cfg`, `ObjectPrototypes.cfg`, `EffectPrototypes.cfg`.

- **Rule**: Patches must be placed in a **sub-folder** named exactly matching the target file (minus extension).
- **Filename**: `[OriginalFileName]_patch_[YourModName].cfg`
- **Folder Path**: `Content/GameLite/GameData/[OriginalFileName]/`
- **Example**:
  - Target: `ObjectPrototypes.cfg`
  - Path: `.../GameData/ObjectPrototypes/ObjectPrototypes_patch_SkipRunFast.cfg`

### B. Standard/Global CFGs

Files that contain global settings or non-SID structures, like `CoreVariables.cfg` or `AIGlobals.cfg`.

- **Rule**: Placed directly in the same directory as the original.
- **Filename**: `[OriginalFileName].cfg_patch_[YourModName]` (Note: `_patch` comes _after_ `.cfg`)
- **Path**: `Content/GameLite/GameData/CoreVariables.cfg_patch_FasterClimb`

> **Note**: As of patch 1.8.1, default configs are `cfg.bin`. You cannot read these directly. Use the uncompiled raw text files from the SDK (or "cfg dump") as your reference "Source of Truth".

## 2. Core Examples (Source: LessSway Mod)

The following examples demonstrate the core operations you can perform on config nodes.

### 1. Adding Nodes (New Definitions)

To add a completely new object or definition, simply define the struct with a unique SID. This is commonly done for adding new effects, items, or abilities.

_Example (from `EffectPrototypes_patch_LessSway.cfg`):_

```ini
LessSwayX : struct.begin {refkey=AbstractSwayTemplate}
    SID = LessSwayX
    Type = EEffectType::IdleSwayXModifier
struct.end
```

_Here, `LessSwayX` is a new node added to the game, inheriting properties from `AbstractSwayTemplate`._

### 2. Adding Abstract Nodes (Templates)

You can define abstract "template" nodes that are not used directly by the game logic but serve as a base for other nodes to inherit from. This reduces code duplication.

_Example (from `EffectPrototypes_patch_LessSway.cfg`):_

```ini
AbstractSwayTemplate : struct.begin {refurl=../EffectPrototypes.cfg; refkey=[0]}
    SID = AbstractSwayTemplate
    Type = EEffectType::None
    bIsPermanent = true
    ValueMin = -50%
    ValueMax = -50%
struct.end
```

_Here, `AbstractSwayTemplate` inherits from the root of `EffectPrototypes.cfg` (refkey=[0]) but overrides specific values. Other nodes like `LessSwayX` then inherit from this template._

### 3. Modifying Nodes (Replacing)

By default, if you define a node that already exists without `{bpatch}`, you **replace** it entirely. This is rarely what you want for compatibility, but useful if you need to redefine an object from scratch.

_Example:_

```ini
// Use a unique SID to avoid replacing, but if you used an existing SID:
ExistingScope : struct.begin
   // This would wipe all original properties of ExistingScope and only keep what is written here
   NewProperty = 1.0
struct.end
```

### 4. Patching Nodes (`{bpatch}`)

The `{bpatch}` keyword allows you to modify specific properties of an existing node while keeping everything else intact. You must use `{bpatch}` at _every_ level of nesting you traverse.

_Example (from `AttachPrototypes_patch_LessSway.cfg`):_

```ini
TemplateScope : struct.begin {bpatch}
   CanHoldBreath = true
   Scope : struct.begin {bpatch}
      AimingEffects : struct.begin {bpatch}
         PlayerOnlyEffects : struct.begin {bpatch}
            [*] = LessSwayX
            [*] = LessSwayY
         struct.end
      struct.end
   struct.end
struct.end
```

_Note how every struct (`TemplateScope`, `Scope`, `AimingEffects`, etc.) has `{bpatch}`._

### 5. Removing Nodes (`removenode`)

You can remove a specific node from a struct using `removenode` inside a `{bpatch}` block.

_Example:_

```ini
SomeUpgrade : struct.begin {bpatch}
   OldBadEffect : struct.begin {bpatch} removenode struct.end
struct.end
```

## 3. Important: The Inheritance/Patching Order (Version 1.8.1+)

There is a critical limitation in how the S.T.A.L.K.E.R. 2 engine (as of 1.8.1) processes configuration files, specifically regarding inheritance and patching.

**The Theory**:
It is believed that the engine constructs all the inheritors of the various prototypes and templates **first**, and then applies patches (like `{bpatch}`).

**The Consequence**:
If you `{bpatch}` a parent/template node (e.g., `TemplateScope`), **the children who inherit from that node will NOT see those changes**. They have already been constructed using the _original_ version of the template.

- **What this means for you**: You cannot simply patch a master template and expect it to propagate to all weapons or attachments.
- **The Solution**: You must patch **each child node directly**.

_Evidence (from `LessSway`)_:
Instead of just patching `TemplateScope` and calling it a day, the `LessSway` mod explicitly patches every single scope that exists in the game data:

```ini
// Patched for safety/completeness
TemplateScope : struct.begin {bpatch} ... struct.end

// BUT ALSO every individual child must be patched:
RU_ColimScope_1 : struct.begin {bpatch} ... struct.end
EN_ColimScope_1 : struct.begin {bpatch} ... struct.end
RU_X2Scope_1 : struct.begin {bpatch} ... struct.end
// ...and so on for dozens of entries
```

If you modify `TemplateScope` only, `RU_ColimScope_1` (which inherits from it) will remain unchanged in the game because it was fully built before your patch to `TemplateScope` was applied.

## 4. Advanced Reference & Replacement Logic

Understanding the difference between creating, replacing, and patching is vital for complex mods.

### Combined `refurl` and `refkey` Example

You can combine these keys to pull a specific node from another file to create a new object based on an existing one.

- `refurl=../path/to/file.cfg`: Specifies the source file (can be a relative path like `../` or `../../`) or `EffectsPrototype.cfg` provided that the patch file will be in the same folder as the original file. This is useful for cases where you are creating multiple `.cfg` files in a directory but still want to reference nodes from other files in that directory.
- `refkey=NodeName`: Specifies the exact node or SID within that file to copy.

```ini
// 1. CREATING A NEW NODE (Inheritance/Copying)
// We create 'MyNewScope' by copying 'TemplateScope' from a file one folder up.
// Because we use refurl/refkey and NO {bpatch}, we are treating the reference as a base template.
// note that we are using ../ to reference a file in the parent directory. This runs under the assumption that the patch file will be one directory down from the original file.
// Since we know that ItemProtypes.cfg resides in Content\GameLite\GameData\ , we assume that this patch file will be located in Content\GameLite\GameData\FolderNameHere
MyNewScope : struct.begin {refurl=../ItemPrototypes.cfg; refkey=TemplateScope}
    SID = MyNewScope
    MarketPrice = 9999
struct.end

// 2. REPLACEMENT (Destructive)
// If we define a node that matches an existing SID WITHOUT any keywords, we DESTROY the old one.
// The original 'MyNewScope' content is wiped, replaced ONLY by what is below.
MyNewScope : struct.begin
    SID = MyNewScope
    // Everything else is gone unless re-defined here
struct.end

// 3. MODIFICATION (Patching)
// We use {bpatch} to safely edit the existing node without destroying unchanged data.
// We can also use removenode here to cleanly excise parts we don't want.
MyNewScope : struct.begin {bpatch}
    MarketPrice = 500
    BadEffect : struct.begin {bpatch} removenode struct.end
struct.end
```

## 5. References (`refurl`, `refkey`)

- **`refkey=[SID]`**: Reference a node within the same file or a previously loaded context.
- **`refurl=../File.cfg`**: Reference a node in another file.
  - _Note_: When referencing a `.cfg` file that doesn't exist (because the game uses `.cfg.bin`), the system automatically redirects to the `.cfg.bin` version.

## 6. Arrays

- **Append**: `[*] = Value` adds to the end of an array.
- **Overwrite**: Use `{bskipref}` on the array container to wipe the old array and start fresh.

```ini
AllowedSaveTypes : struct.begin {bskipref}
    [0] = ESaveType::Manual
    [1] = ESaveType::Auto
struct.end
```

# Explanation of Keys

## `PlayerWeaponSettingsPrototypes.cfg`

### Identity & Durability

- **SID**: Struct ID. The unique identifier used by the game engine to reference this specific weapon configuration (e.g., `GunPM_HG_Player` for the Makarov).
- **DurabilityDamagePerShot**: The amount of condition/durability lost with every trigger pull.
  - _Deduction_: Snipers like the Gauss (12.5) or SVU (11.0) degrade much faster than SMGs like the Viper (0.69).

### Damage & Status Effects

- **BaseDamage**: The raw health damage dealt per projectile.
  - _Deduction_: Shotguns have high values (140-160) because they represent multiple pellets, while the Gauss rifle has a massive 500.0.
- **ArmorPiercing**: A value representing how effectively the bullet ignores or bypasses armor protection.
  - _Deduction_: Standard pistols are 1.0, while specialized armor-piercing weapons like the Vintar or PKP machine gun are 3.0+.
- **CoverPiercing**: Works like ArmorPiercing but specifically for shooting through environmental objects like wood or thin metal.
- **ArmorDamage**: Damage dealt specifically to the target's armor durability. Most are set to 0.0, suggesting armor damage is likely derived from BaseDamage and ArmorPiercing elsewhere.
- **BaseBleeding**: The intensity of the bleeding effect applied to a target.
- **ChanceBleedingPerShot**: The percentage chance (e.g., 10%) that a hit will trigger the bleeding status.

### Ballistics & Range

- **EffectiveFireDistanceMin / Max**: The range "sweet spot" where the weapon performs as intended.
  - _Deduction_: A comment in the file suggests keeping these equal avoids buggy recoil behavior. Snipers have values up to 5000+, while pistols are around 1000.
- **FireDistanceDropOff**: The distance (in game units) at which projectiles start losing damage.
- **MinBulletDistanceDamageModifier**: The "floor" for damage at long range.
  - _Deduction_: A value of 0.2 means the gun will never deal less than 20% of its BaseDamage, no matter how far the bullet travels.
- **BulletDropLength**: The horizontal distance a bullet travels before gravity starts pulling it down aggressively.
- **DistanceDropOffLength**: The total distance over which the damage transition from "Full" to "MinModifier" occurs.

### Accuracy & AI Interaction

- **DispersionRadius**: The functional accuracy of the weapon.
  - _Deduction_: Lower is better. The Gauss is 83.0 (extremely precise), while the Obrez sawed-off is 758.0 (wild spread).
- **BaseComfort**: A multiplier for how much noise the player makes while moving with this weapon.
  - _Deduction_: Used by AI to detect you. Larger weapons like Rifles (0.55) are "less comfortable" (noisier) than Pistols (0.25).
- **FireLoudness**: A multiplier for the sound of the gunshot for AI detection.
  - _Deduction_: Suppressed weapons like the Vintar/Gvintar have a very low 0.1, while shotguns are 0.8.

### User Interface (UI)

These values are normalized (usually 0.0 to 1.0) and are used exclusively to draw the stat bars you see in the inventory/trade screens:

- **AccuracyUI**: Fills the "Accuracy" bar.
- **RateOfFireUI**: Fills the "Rate of Fire" bar.
- **HandlingUI**: Fills the "Handling" (Ergonomics) bar.
- **DamageUI**: Fills the "Damage" bar.
- **RangeUI**: Fills the "Range" bar.

## `NpcWeaponSettingsPrototypes.cfg`

### Combat Balance & Difficulty

- **BaseDamage**: Generally much lower than player values (e.g., standard Rifles deal ~9.5 instead of ~23.0). This allows the player to survive multiple hits from a group of enemies.
- **ArmorDamage**: Usually set to 1.0 for common NPCs. It controls how quickly enemy fire degrades the player's suit.
- **StaggerEffectPrototypeSID**: References a "flinch" or stagger effect (e.g., NPCWeaponMediumStagger). This determines the visual and mechanical "kick" the player feels when suppressed or hit by NPC fire.
- **DurabilityDamagePerShot**: Set to 0.0 for nearly all NPCs. Enemies do not suffer from weapon degradation.

### AI Accuracy & Range

- **DispersionRadius**: Functional accuracy for NPCs. Interestingly, many are set to 100.0 or 200.0, which might seem "inaccurate" compared to the player's base values, but it is modified by curves.
- **DispersionRadiusZombieAddend**: A penalty to accuracy (usually +30.0) applied if the NPC is a Zombie. This simulates their uncoordinated, "shuffling" shooting style.
- **DispersionRadiusMultiplierByDistanceCurve**: References an external data curve (e.g., PistolDispersionDefault). This scales the NPC's inaccuracy based on distance—NPCs are typically more "clumsy" at extreme ranges and more precise medium-close.
- **BulletDropHeight**: Usually 0.0 for NPCs to simplify AI calculations, ensuring their shots fly flatter toward the player.

### AI Tactics & Behavior

- **CombatSynchronizationScore**: This is a behavioral weight system.
  - _Deduction_: It tells the AI whether a weapon is suitable for certain actions. For example, a -1.0 on SuppressiveFire for a specialized rifle means the AI will not try to suppression-fire with it, while a 1.0 on ThrowGrenade encourages them to use explosives during that weapon's combat state.

### Special Archetypes

- **GuardGun... (SIDs like GuardGunAK74_ST_NPC)**:
  - **BaseDamage**: 500.0
  - **DispersionRadius**: 1.0 to 10.0 (Perfect accuracy)
  - _Deduction_: These are "Executioner" weapons for scripted or boundary guards (like the "Border Guards"). They are designed to kill the player instantly with 100% accuracy if they enter a forbidden zone.
- **Scar_GunGauss_SP_NPC**: This Gauss variant has unique behavioral scores (like 0.8 for Advance.Action), suggesting it’s tuned for a specific boss or elite NPC (like Scar) to be highly aggressive.

## `GeneralNPCObjPrototypes.cfg`

Unlike the previous weapon files, this file dictates how NPCs move, react to the player, and utilize specialized combat tactics.

### Core Identity & Stats

- **SID**: The Unique Identifier for the NPC archetype (e.g., GeneralNPC_Duty_Stormtrooper).
- **Faction**: Determines the NPC's social group (Duty, Freedom, Monolith, etc.), affecting who they fight or assist.
- **Mass**: The physical weight of the NPC (usually 50.0), used for physics calculations like pushback or falling.
- **OfflineCombatWeight**: A value used for simulating combat between AI squads when the player is not nearby.
- _Deduction_: Guards (25) are much stronger "simulated" fighters than standard NPCs (10).
- **VitalParams**: Defines health (MaxHP), stamina (MaxSP), and degradation rates for bleeding, radiation, and hunger.
- **Damage & Vulnerabilities**:
  - **BoneDamageCoefficients**: Multipliers for damage based on where the NPC is hit.
  - _Deduction_: Headshots deal 6.0x damage, while limb shots deal only 0.7x, making accuracy critical for the player.
  - **ArmorDifferenceCoef...**: Multipliers that determine how much protection armor provides against projectiles (2.0) vs. melee (1.0).
  - **Protection**: Elemental and anomalous resistances (Burn, Shock, PSY, Radiation, etc.). The GuardBase has a massive 90.0 in all categories, making them nearly immune to the environment.
- **AI Combat Tactics**:
  - **Abilities**: Lists specific actions the AI can perform, such as Human_PhantomAttack, Human_MeleeAttack, or Human_ThrowGrenade.
  - **FlankParameters**: Controls how enemies try to get around the player.
  - _Deduction_: They won't start a flank until they've detected the player for 15s (ActivationDelaySeconds) or have taken enough damage (MaxAccumulatedDamage = 30).
  - **EvadeParameters**: Controls "dodging" behaviors (Side-stepping or backing away).
  - **SuppressiveFireParameters**: How the AI "pins" the player down, aiming at a specific bone (jnt_spine_03) to keep you in cover.
  - **CamperFeatureData**: A system to punish "camping" NPCs, forcing them to move if they stay in a 500.f radius for more than 10s.
- **Movement & Locomotion**:
  - **MovementParams**: Defines the raw speeds for various states:
  - **WalkSpeed**: 115
  - **RunSpeed**: 300
  - **SprintSpeed**: 300
  - **ClimbSpeedCoef / LimpSpeedCoef**: Multipliers that slow the NPC down when climbing or when injured (Limping is 50% speed).
  - **DoorTransitionSettings**: Determines which animation an NPC uses to open doors.
  - _Deduction_: If they are in combat with a weapon, they use a "Kick" animation (MG_tp_ar_combat_melee_kick) instead of a normal open.
- **NPC Roles (NPCType)**
  - **ItemGeneratorPrototypeSID**: Points to a loot table. A Sniper archetype will have a different generator than a CloseCombat archetype.
  - **TradePrototypeSID / NPCType**: Defines if the NPC is a merchant, technician, or guide, granting them specific interaction menus.
  - **MeshGenerator...**: Controls the visual appearance and randomized clothing/equipment for that specific faction and role.

## `NPCWeaponAttributesPrototypes.cfg`

While the `Settings` files (above) handle the "math" of a shot (damage, dispersion), the `Attributes` files handle the **behavioral logic**. This file specifically dictates how the AI utilizes its arsenal.

### AI Burst Logic (`Long`, `Medium`, `Short`)

The AI changes its firing pattern based on its distance to the target. Each distance bracket contains:

- **MinShots / MaxShots**: The number of bullets the AI will fire in a single burst.
  - _Ex_: A Sniper might have `1 / 1`, while an AK74 Newbie has `8 / 16` at short range.
- **IgnoreDispersionMinShots / MaxShots**: **CRITICAL FOR DIFFICULTY**. This defines how many bullets at the start of a burst have "perfect" accuracy, ignoring the weapon's natural dispersion.
  - _Deduction_: Elite NPCs typically have higher `IgnoreDispersion` values, making their initial shots extremely lethal.

### Engagement Ranges

- **CombatEffectiveFireDistanceMin**: The minimum range an NPC will consider this weapon "useful."
- **CombatEffectiveFireDistanceMax**: The maximum engagement range. If a player is beyond this, the NPC will typically stop firing and try to close the distance or seek better positioning.

### Weapon Links

- **CharacterWeaponSettingsSID**: This is the "Glue" property. It points to the entry in `NPCWeaponSettingsPrototypes.cfg` that contains the actual damage and dispersion stats for the NPC's version of the gun.

### Animation & VFX

- **AnimBlueprint**: Points to the Third-Person (TP) animation blueprint for the weapon (e.g., `AnimBP_pm_tp`).
- **ParticlesBasedOnHeating**: Defines the muzzle flash and heat haze VFX that play when the NPC fires.

## `PlayerWeaponAttributesPrototypes.cfg`

This file is the "visual" counterpart to the NPC version, but specifically for the First-Person (FP) experience.

- **AnimBlueprint**: Points to the First-Person (FP) animation blueprints.
- **MuzzleSocketName**: Usually `MuzzleFOV`, specifically for the player's camera-aligned muzzle flashes.
- **DefaultWeaponSettingsSID**: Links to the player's damage and dispersion settings in `PlayerWeaponSettingsPrototypes.cfg`.

# Additional Notes

Modding is a community effort. Feel free to contribute to the modding community by sharing your knowledge and experiences to this guide. You can do so by opening an issue or a pull request this repository.
