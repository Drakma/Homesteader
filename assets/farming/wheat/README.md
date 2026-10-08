# Wheat Plant (`wheat`)

![Wheat Plant Icon](wheat.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `wheat`

## Description
A wheat lifecycle growing through 5 stages (sprout -> small -> medium -> mature -> ripe) over 180 days, with withered and dead versions. The models are procedural (built in the game), the originals are kept in assets/_originals/crops_old.

## Growth
- **Type**: `crop`
- **Species**: `wheat`
- **Full age**: 180 days
- **Yield**: 2 to 2 `ingredient_wheat` at stage 5
- **Planting**: summer; seed `seed_wheat`

| Stage | Name | Age range |
| :--- | :--- | :--- |
| 1 | sprout | 0 to 20 |
| 2 | small | 20 to 59 |
| 3 | medium | 59 to 108 |
| 4 | mature | 108 to 149 |
| 5 | ripe | 149 to 180 |

## Asset Files
- **Plugin Manifest (JSON)**: [wheat.json](wheat.json)
- **Icon (PNG)**: [wheat.png](wheat.png)
