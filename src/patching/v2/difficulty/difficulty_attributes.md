# S.T.A.L.K.E.R. 2 Difficulty Attributes Documentation

This document describes the various attributes found in `DifficultyPrototypes.cfg` and used by the BetterDifficulty mod.

## General Combat & Health

| Attribute                         | Description                                                           | Impact                                                    |
| --------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------- |
| `NPC_HP`                          | Multiplier for the maximum health of NPCs.                            | Lower values make enemies easier to kill.                 |
| `Weapon_BaseDamage`               | Damage multiplier for weapons fired by the player.                    | Higher values increase player lethality.                  |
| `NPC_Weapon_BaseDamage`           | Damage multiplier for weapons fired by NPCs.                          | Lower values reduce damage taken by the player.           |
| `Mutant_BaseDamage`               | Multiplier for damage dealt by mutants.                               | Lower values reduce mutant lethality.                     |
| `Explosion_BaseDamage`            | Multiplier for damage from grenades, barrels, and other explosives.   | Lower values improve survival against explosives.         |
| `PlayerWeapon_HeadshotMultiplier` | Additional damage multiplier applied when the player hits a headshot. | Higher values reward precision more significantly.        |
| `Regen_HP`                        | Multiplier for the player's natural health regeneration.              | Higher values mean faster passive healing.                |
| `Effect_Bleeding`                 | Multiplier for the severity/intensity of the bleeding effect.         | Lower values mean less HP loss per second while bleeding. |
| `Effect_Degen_Bleeding`           | Speed at which bleeding naturally decreases (heals).                  | Higher values mean bleeding stops faster on its own.      |
| `Radiation_AccumulationSpeed`     | Rate at which the player character collects radiation in zones.       | Lower values make irradiated areas less dangerous.        |
| `Anomaly_Damage`                  | Multiplier for damage received from all environmental anomalies.      | Lower values make anomalies less lethal.                  |

## Damage Reduction (Accumulated)

These attributes control a mechanic that scales damage reduction based on distance and history.

| Attribute                                          | Description                                                                                      |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `AccumulatedDamageReductionCurveWeightMax`         | Maximum weight/multiplier for the damage reduction curve.                                        |
| `AccumulatedDamageReductionCurveWeightMin`         | Minimum weight/multiplier for the damage reduction curve.                                        |
| `AccumulatedDamageReductionCurveWeightMaxDistance` | The distance (likely in centimeters) where the maximum reduction weight is applied.              |
| `AccumulatedDamageReductionIncludesHealedHealth`   | If true, health that was lost and then healed still counts towards "accumulated" damage history. |

## Weapons & Accuracy

| Attribute                  | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| `HipAccuracyMultiplier`    | Multiplier for weapon dispersion when firing from the hip (not aiming).  |
| `Weapon_Durability`        | Baseline multiplier for weapon condition stability.                      |
| `Weapon_DurabilityDamage`  | How much durability a weapon loses with each shot fired.                 |
| `Weapon_JammingMultiplier` | Multiplier for the probability of a weapon jam as condition decreases.   |
| `Weapon_Rank_Add`          | Bonus damage or effectiveness added based on the weapon's internal rank. |
| `NPC_Weapon_Rank_Add`      | Bonus damage NPCs receive based on their internal rank.                  |

## Economy & Trading

| Attribute                 | Description                                                                      |
| ------------------------- | -------------------------------------------------------------------------------- |
| `Consumable_Cost`         | Cost multiplier for food and medical items at traders.                           |
| `Ammo_Cost`               | Cost multiplier for ammunition at traders.                                       |
| `Armor_Cost`              | Cost multiplier for buying suits/armor.                                          |
| `Weapon_Cost`             | Cost multiplier for buying weapons.                                              |
| `Artifact_Cost`           | Multiplier for the value/price of artifacts (both buying and selling).           |
| `NightVisionGoggles_Cost` | Cost multiplier for NVG items.                                                   |
| `Repair_Cost`             | Multiplier for the cost of repairing equipment at technicians.                   |
| `Upgrade_Cost`            | Multiplier for the cost of upgrading equipment at technicians.                   |
| `Reward_MainLine_Money`   | Multiplier for money rewarded from main story missions.                          |
| `Reward_SideLine_Money`   | Multiplier for money rewarded from side/optional missions.                       |
| `BuyCondition`            | Affects the quality/condition of items available for purchase from traders.      |
| `SellCondition`           | The minimum condition an item must be in for a trader to buy it from the player. |

## Survival & Environmental

| Attribute                 | Description                                                                       |
| ------------------------- | --------------------------------------------------------------------------------- |
| `Effect_Satiety`          | Rate at which the player loses satiety (gets hungry). Higher = faster starvation. |
| `Effect_Sleepiness`       | Rate at which the player character gets tired. Higher = faster fatigue buildup.   |
| `Weather_Storm_Weight`    | Multiplier for the likelihood/intensity of storm weather events.                  |
| `Weather_Emission_Weight` | Multiplier for the likelihood/frequency of Blowouts (Emissions).                  |
| `NPC_AttackCooldown`      | Modifier for the delay between NPC firing bursts or attacks.                      |
| `Mutant_AttackCooldown`   | Modifier for the delay between mutant attack patterns.                            |

## UI & Saving (Hardcore Toggles)

| Attribute                       | Description                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| `bShouldDisableCrosshair`       | If true, the aiming crosshair is hidden from the HUD.                               |
| `bShouldDisableCompass`         | If true, the compass/mini-map navigation is disabled.                               |
| `bShouldDisableStashMarkers`    | If true, discovered stashes are not marked on the map.                              |
| `bShouldDisableDeadBodyMarkers` | If true, killed enemies are not marked on the HUD/Compass.                          |
| `ShowWarningPopup`              | Whether to show a warning when changing to this difficulty level.                   |
| `BlockSettings`                 | If true, gameplay settings related to difficulty are locked during play.            |
| `TotalSaveLimits`               | Specifies the maximum number of manual/auto/quick saves allowed for the difficulty. |
| `AllowedSaveTypes`              | Defines which save methods are available (Manual, Auto, Quick, Hub, etc.).          |

## Advanced Mechanics

| Attribute                                         | Description                                                                                |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `AdditionalMechanicsEffects`                      | List of negative mechanics applied at higher difficulties (e.g., HungerNegativeMechanics). |
| `AgentCooldownMultipliers`                        | Detailed overrides for specific mutant ability cooldowns (Bloodsucker, Chimera, etc.).     |
| `PsyPhantomNPCOverrides`                          | Configuration for how Psy-phantoms behave (spawn delay, count, bleeding application).      |
| `NPC_Armor_Strike_Add`                            | Flat resistance bonus added to NPC armor against physical impacts.                         |
| `Armor_Strike_Add`                                | Flat resistance bonus added to player armor against physical impacts.                      |
| `Armor_Anomaly` / `Armor_Radiation` / `Armor_PSY` | Multipliers for protection effectiveness against specific damage types.                    |
