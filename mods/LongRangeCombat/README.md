# LongRangeCombat Mod

Extends NPC engagement distances while transitioning from "magical" tracking to a rank-based accuracy model.

## Key Features

### 1. Vision & Detection

- **Detection Distance**: Reduced by **10%** of original to reward stealthy approaches and avoid issues with NPCs spotting the player at unreasonable distances unreasonably fast.
- **Reaction Speed**: Acquisition and re-evaluation time increased by **50%**, making NPCs slower to react to new threats.
- **Visibility Persistence**: NPCs track last-known positions **2x longer**, allowing them to suppress or maneuver around cover more effectively.

### 2. Combat Engagement

- **Engagement Ranges**: NPCs engage at much longer distances where appropriate:
  - **Newbie**: 0.8x (Reduced)
  - **Experienced / Veteran**: 1.5x (Significantly Increased)
  - **Master**: 1.1x
  - **Zombie**: 1.0x

### 3. Accuracy System (Guaranteed Hits)

- **Dynamic Scaling**: Replaced fixed guaranteed hits with a **sigmoid-based scaling model**. Accuracy now scales dynamically with NPC rank, distance bracket (Short/Medium/Long), and weapon burst size.
- **Rank Lethality**: Master rank NPCs are significantly more lethal at short and medium ranges.
- **Specialized Weapons**:
  - **Snipers & Bolt-Actions**: Strictly limited guaranteed hits (typically zero for lower ranks).
  - **Shotguns**: Entirely excluded from the guaranteed hit system to maintain intended close-range behavior.

### 4. Weapon Balancing

- **Dispersion**: NPC weapon dispersion radius reduced to focus lethality through the rank-based accuracy system.
- **Bleeding**: NPC weapon bleeding normalized:
  - `BaseBleeding`: Adjusted via standard normalization curve.
  - `ChanceBleedingPerShot`: Reduced by **25%** (minimum 1%).

### 5. Stealth Buffs

- **Movement Noise**: Noise comfort increased by **20%**.
- **Firing Noise**: Weapon loudness reduced by **20%**.

## TODO

1. Update logic so that more experienced stalkers at longer ranges fire shorter bursts which are more effective. Update python script to account for this.