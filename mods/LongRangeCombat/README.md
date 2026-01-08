# LongRangeCombat Mod

Extends NPC engagement distances while transitioning from "magical" tracking to a rank-based accuracy model.

## Key Features

### 1. Vision & Detection

- **Detection Distance**: Slightly reduced to reward stealthy approaches and avoid issues with NPCs spotting the player at unreasonable distances unreasonably fast.
- **Reaction Speed**: Acquisition and re-evaluation time increased, making NPCs slower to react to new threats.
- **Visibility Persistence**: NPCs track last-known positions longer, allowing them to suppress or maneuver around cover more effectively.

### 2. Combat Engagement

- **Engagement Ranges**: NPCs engage at much longer distances where appropriate:
  - **Newbie**: Reduced
  - **Experienced / Veteran**: Significantly Increased
  - **Master**: Increased
  - **Zombie**: Standard

### 3. Accuracy System (Guaranteed Hits)

- **Dynamic Scaling**: Replaced fixed guaranteed hits with a **sigmoid-based scaling model**. Accuracy now scales dynamically with NPC rank, distance bracket (Short/Medium/Long), and weapon burst size.
- **Rank Lethality**: Master rank NPCs are significantly more lethal at short and medium ranges.
- **Specialized Weapons**:
  - **Snipers & Bolt-Actions**: Strictly limited guaranteed hits (minimal for lower ranks).
  - **Shotguns**: Entirely excluded from the guaranteed hit system to maintain intended close-range behavior.

### 4. Weapon Balancing

- **Dispersion**: NPC weapon dispersion radius reduced to focus lethality through the rank-based accuracy system.
- **Bleeding**: NPC weapon bleeding normalized:
  - `BaseBleeding`: Adjusted via standard normalization curve.
  - `ChanceBleedingPerShot`: Significantly reduced (with a minimum floor).

### 5. Stealth Buffs

- **Movement Noise**: Noise comfort increased.
- **Firing Noise**: Weapon loudness reduced.

# Details

## 8 January 2026 2.0

### Combat Logic

- **Range Normalization**: Implemented asymptotic scaling to keep engagements within render limits.
  - **Caps**: Standard weapons capped at 9000, Snipers at 10000.
  - **Shotguns**: Range reduced to 75% of vanilla to emphasize close-quarters role.
- **Accuracy**:
  - Global NPC dispersion multiplier set to **0.425** (significantly more accurate).
  - **Class Scaling**: Snipers (7.0x), Pistols (2.45x), SMGs (1.65x) dispersion penalty to balance the global buff.

### Vision & Stealth

- **Vision**: Detection distance reduced by 10% (0.9x).
- **Reaction**:
  - Check time increased by 50% (1.5x).
  - Lose target time increased by 100% (2.0x).
- **Player Stealth**: Comfort and Loudness thresholds reduced by 20% (0.8x), making stealth more viable.

### Damage & Health

- **Bleeding**:
  - Chance reduced to 60% of original.
  - Base bleeding damage adjusted (Curve: `0.646 * Original + 1.54`).

## First Version 1.0

Description

A very experimental mod to see how long-range combat can be made more enjoyable by changing configuration files.

What is Done?

    Rework of NPC accuracy. The more experienced the enemy, and the more they shoot, the more accurate they will be.
    Detection distance slightly nerfed, player stealth slightly buffed.
    Bleeding damage and chance reduced.
