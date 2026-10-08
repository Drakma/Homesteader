# Barley Plant (`barley`)

![Barley Plant Icon](barley.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `barley`

## Description
A barley lifecycle growing through 5 stages (sprout -> small -> medium -> mature -> ripe) over 90 days, with withered and dead versions. The models are procedural (built in the game), the originals are kept in assets/_originals/crops_old.

## Growth
- **Type**: `crop`
- **Species**: `barley`
- **Full age**: 90 days
- **Yield**: 2 to 2 `ingredient_barley` at stage 5
- **Planting**: spring; seed `seed_barley`

| Stage | Name | Age range |
| :--- | :--- | :--- |
| 1 | sprout | 0 to 10 |
| 2 | small | 10 to 30 |
| 3 | medium | 30 to 54 |
| 4 | mature | 54 to 75 |
| 5 | ripe | 75 to 90 |

## Asset Files
- **Plugin Manifest (JSON)**: [barley.json](barley.json)
- **Icon (PNG)**: [barley.png](barley.png)
