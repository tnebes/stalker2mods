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

# Additional Notes
Modding is a community effort. Feel free to contribute to the modding community by sharing your knowledge and experiences to this guide. You can do so by opening an issue or a pull request this repository.