# Burst Accuracy Projections
Logic: `max(Floor, int(MinShots * Chance))`

## Scenario: MinShots=3, MaxShots=6
| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |
| :--- | :--- | :--- | :--- |
| **Newbie** | 0 / 1 | 0 / 1 | 0 / 0 |
| **Experienced** | 1 / 1 | 0 / 1 | 0 / 0 |
| **Veteran** | 1 / 2 | 0 / 1 | 0 / 0 |
| **Master** | 1 / 2 | 1 / 2 | 0 / 1 |
| **Zombie** | 0 / 1 | 0 / 0 | 0 / 0 |

## Scenario: MinShots=4, MaxShots=14
| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |
| :--- | :--- | :--- | :--- |
| **Newbie** | 0 / 1 | 0 / 1 | 0 / 0 |
| **Experienced** | 1 / 2 | 0 / 1 | 0 / 0 |
| **Veteran** | 1 / 2 | 0 / 2 | 0 / 0 |
| **Master** | 1 / 2 | 1 / 2 | 0 / 2 |
| **Zombie** | 0 / 1 | 0 / 0 | 0 / 0 |

## Scenario: MinShots=8, MaxShots=16
| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |
| :--- | :--- | :--- | :--- |
| **Newbie** | 0 / 1 | 0 / 1 | 0 / 0 |
| **Experienced** | 1 / 4 | 0 / 1 | 0 / 0 |
| **Veteran** | 3 / 5 | 1 / 4 | 0 / 0 |
| **Master** | 3 / 5 | 3 / 5 | 1 / 4 |
| **Zombie** | 0 / 1 | 0 / 0 | 0 / 0 |
