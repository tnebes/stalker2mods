# Preamble

SINCE the Zone is quite large,
SINCE Skif used to be an army man,
SINCE anomalies break laws of physics anyhow,

this mod makes running around the Zone more manageable.

# Description

Stamina has been reworked.

1. Being hydrated decreases stamina use
2. Being hydrated lasts longer
3. Drinking energy drinks increases stamina regen
4. Drinking energy drinks extends stamina regen time.
5. Drinking energy drinks does not decrease stamina use.

Normal scenario: No water and no energy drinks means you stop often to catch your breath.
No water but energy drinks: you will have to stop often but for a shorter time to catch your breath.
Water but no energy drinks: you will be able to sprint for longer, but you will spend more time recuperating.
Water and energy drinks: you will be able to sprint for longer, you will have to take breaks less often, and you will spend less time recuperating.

# Todo

1. Energy drinks aid with aiming and reload speeds.
> This cannot be implemented as currently, there exist no examples of consumables that affect aiming or reload speed. That is, none of them use `EffectPrototypeSIDs` with a struct whose `EEffectType` is `AimingTime` or `ReloadingTime` (similar to what is seen in `AimingTimeDecBy50` and `ReloadingTimeDecBy25`).
2. There should be a visible indicator in the frontend when the player's thirst is to be quenched.
> Will require adding a new icon, as well as the logic to show it when the effect `WaterStaminaPerAction1` runs out.

