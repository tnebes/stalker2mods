# LongRangeCombat Mod

This mod rebalances long-range combat to feel more realistic and tactical. It limits NPC vision range, increases weapon spread at distance, and enhances player stealth.

## Key Changes

### 1. NPC Vision & Detection

- **Detection Range**: Reduced `EnemyCouldBeVisibleMaxDistance` by **15%**. NPCs will no longer spot or acquire you at extreme ranges.
- **Acquisition Delay**: Increased `CheckEnemyTime` by **50%**. NPCs take longer to react when they first see you.
- **Visibility Persistence**: Decreased `LoseEnemyVisibilityTime` by **50%**. NPCs "forget" your position faster once you break line of sight, making it easier to "ghost" them.

### 2. Combat Accuracy

- **NPC Accuracy**: Increased `DispersionRadius` and `DispersionRadiusZombieAddend` by **20%**. This makes NPC fire significantly less accurate at longer distances.

### 3. Player Stealth

- **Movement Noise**: Decreased `BaseComfort` by **15%** (85% of original). You make less noise while moving with a weapon.
- **Firing Noise**: Decreased `FireLoudness` by **10%** (90% of original). Your gunshots are slightly quieter for the AI detection system.
