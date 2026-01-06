# LongRangeCombat Mod

This mod extends NPC engagement distances while nerfing their "magical" accuracy and tracking.

## Key Features

### 1. Extended Engagement Ranges

NPCs now attempt to engage from much further away (up to **1.5x** original range), creating more opportunities for sniping and tactical positioning.

### 2. Rank-Based Accuracy (Guaranteed Hits)

Replaced unfair "perfect" hits with a granular, rank-specific accuracy grid. These are valid for a single burst of fire:

- **Newbie/Zombie**: 50% chance for 1 guaranteed hit at **Short** range.
- **Experienced**: 1 guaranteed hit at **Short** range.
- **Veteran**: 1 guaranteed hit at **Short**, 50% chance for 1 guaranteed hit at **Medium**.
- **Master**: 1 guaranteed hit at **Short/Medium**, 50% chance for 1 guaranteed hit at **Long**.

### 3. Specialized Weapon Rules

- **Snipers & Bolt-Actions**: Low-shot weapons have **zero** guaranteed hits for most ranks. Master rank retains a 50% chance for 1 guaranteed hit at Short/Medium range only.
- **Shotguns**: Entirely excluded from the guaranteed hit system to maintain intended close-range behavior.

### 4. Tracking & Reaction Nerf

- **Reaction Time**: Increased by **50%**. NPCs are slower to acquire and re-evaluate targets at distance.
- **Visibility Persistence**: NPCs lose track of the player **25% faster** once line of sight is broken.

### 5. Increased Dispersion

Global **2.0x** increase to NPC `DispersionRadius`. NPCs must rely on volume of fire rather than perfect precision.

### 6. Stealth Buffs

- **Movement Noise**: Noise comfort increased by **15%**.
- **Firing Noise**: Weapon loudness reduced by **10%**.
