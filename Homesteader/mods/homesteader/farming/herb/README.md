# Herb Plant (`herb`)

![Herb Plant Icon](herb.png)

## Overview
- **Category**: `farming`
- **Item Identifier**: `herb`

## Description
A herb lifecycle growing through 5 stages (sprout -> small -> medium -> mature -> ripe) over 30 days, with withered and dead versions. The models are procedural (built in the game), the originals are kept in assets/_originals/crops_old.

## Growth
- **Type**: `crop`
- **Species**: `herb`
- **Full age**: 30 days
- **Yield**: 1 to 3 `ingredient_herbs` at stage 5
- **Planting**: spring, summer, fall; seed `seed_herb`

| Stage | Name | Age range |
| :--- | :--- | :--- |
| 1 | sprout | 0 to 3 |
| 2 | small | 3 to 10 |
| 3 | medium | 10 to 18 |
| 4 | mature | 18 to 25 |
| 5 | ripe | 25 to 30 |

## Asset Files
- **Plugin Manifest (JSON)**: [herb.json](herb.json)
- **Icon (PNG)**: [herb.png](herb.png)
