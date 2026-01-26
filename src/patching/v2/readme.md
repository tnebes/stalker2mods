# S.T.A.L.K.E.R. 2 Patcher v2 - Developer Guide

The Patcher v2 is a powerful toolset designed to make modification of S.T.A.L.K.E.R. 2 `.cfg` files intuitive, reliable, and compatible with other mods. It provides a high-level API to manipulate the configuration tree and an automated diffing engine to generate optimized `{bpatch}` files.

## Table of Contents

1. [Core Components](#core-components)
2. [Basic Workflow](#basic-workflow)
3. [API Examples](#api-examples)
   - [Loading and Finding Nodes](#loading-and-finding-nodes)
   - [Modifying Properties](#modifying-properties)
   - [Adding/Replacing Structs](#addingreplacing-structs)
   - [Handling Arrays](#handling-arrays)
4. [BPATCH Generation (Diffing)](#bpatch-generation-diffing)

---

## Core Components

- **`ast.py`**: The Abstract Syntax Tree representation. Supports dictionary-like access on structs.
- **`parser.py`**: A robust parser that converts CFG text into an AST.
- **`api.py`**: The primary entry point for developers. Provides `load_configuration` and `Node` factory.
- **`patcher.py`**: The diffing engine that compares your modified AST with original files.

## Basic Workflow

1. **Load** the base configuration file.
2. **Access** the specific struct/property you want to change.
3. **Modify** or **Replace** the node using the fluent API.
4. **Generate** a patch by diffing against the original resource.
5. **Save** the resulting minimal CFG.

---

## API Examples

### Loading and Finding Nodes

```python
from src.patching.v2.api import load_configuration

# Load a configuration file
cfg = load_configuration("WeaponGeneralSetupPrototypes.cfg")

# Find a top-level struct by its SID
gauss_node = cfg.getNodeByName("GunGauss_SP")

if gauss_node:
    # node[0] gives you access to the underlying StructNode
    print(f"Found: {gauss_node.node[0].name}")
```

### Modifying Properties

You can set values directly using dictionary syntax. The system handle floats (`f`), percentages, and strings automatically.

```python
# Change a simple property
gauss_node.node[0]['OtherProp'] = "2.5f"

# Access nested properties
# Note: Currently you drill down using ['Key']
combat_params = gauss_node.node[0]['CombatParameters']
combat_params['Damage'] = "100.0f"
```

### Adding/Replacing Structs

Use the `Node` factory to create new structures.

```python
from src.patching.v2.api import Node, BPATCH

# Replace the 'AimingEffects' struct with a new one
gauss_node.node[0]['AimingEffects'] = Node("AimingEffects", {
    "PlayerOnlyEffects": "MyNewEffect"
}, BPATCH)
```

### Handling Arrays

The `Node` factory automatically detects lists and formats them as STALKER 2 arrays (using `[*]`).

```python
# Create an array of effects
gauss_node.node[0]['AimingEffects'] = Node("AimingEffects", [
    "LessSwayX",
    "LessSwayY"
], BPATCH)

# Resulting CFG:
# AimingEffects : struct.begin {bpatch}
#    [*] = LessSwayX
#    [*] = LessSwayY
# struct.end
```

---

## BPATCH Generation (Diffing)

One of the most powerful features is the ability to generate "clean" patches. Instead of outputting the whole file, you can output only what changed.

```python
from src.patching.v2.patcher import Patcher

# Path to the original game files (dumped)
BASE_DUMP = "C:/dev/stalker2/cfg_dump"

# Initialize the patcher
p = Patcher(BASE_DUMP)

# Generate a minimal patch for 'WeaponGeneralSetupPrototypes.cfg'
# It compares the modified 'cfg.doc' with the file in BASE_DUMP
patch_doc = p.generate_patch("WeaponData/WeaponGeneralSetupPrototypes.cfg", cfg.doc)

# Save the minimal patch
with open("WeaponGeneralSetupPrototypes_patch_MyMod.cfg", "w") as f:
    f.write(patch_doc.to_cfg())
```

The resulting file will automatically contain `{bpatch}` on every modified struct level and only include the properties you actually changed.
