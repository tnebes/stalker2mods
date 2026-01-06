# Burst Accuracy Projections
Logic: `max(Floor, int(MinShots * Chance))`

## Scenario: MinShots=3, MaxShots=6
| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |
| :--- | :--- | :--- | :--- |
| **Newbie** | 0 / 1 | 0 / 1 | 0 / 0 |
| **Experienced** | 1 / 2 | 0 / 2 | 0 / 0 |
| **Veteran** | 1 / 2 | 1 / 2 | 0 / 1 |
| **Master** | 1 / 2 | 1 / 2 | 1 / 2 |
| **Zombie** | 0 / 2 | 0 / 1 | 0 / 0 |

## Scenario: MinShots=4, MaxShots=14
| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |
| :--- | :--- | :--- | :--- |
| **Newbie** | 0 / 1 | 0 / 1 | 0 / 0 |
| **Experienced** | 1 / 3 | 1 / 2 | 0 / 1 |
| **Veteran** | 2 / 3 | 1 / 3 | 1 / 2 |
| **Master** | 2 / 3 | 2 / 3 | 1 / 3 |
| **Zombie** | 1 / 2 | 0 / 1 | 0 / 0 |

## Scenario: MinShots=8, MaxShots=16
| Rank | Short (Min/Max) | Medium (Min/Max) | Long (Min/Max) |
| :--- | :--- | :--- | :--- |
| **Newbie** | 0 / 2 | 0 / 1 | 0 / 0 |
| **Experienced** | 3 / 6 | 2 / 5 | 0 / 2 |
| **Veteran** | 4 / 7 | 3 / 6 | 2 / 5 |
| **Master** | 4 / 7 | 4 / 7 | 3 / 6 |
| **Zombie** | 2 / 5 | 0 / 2 | 0 / 0 |
