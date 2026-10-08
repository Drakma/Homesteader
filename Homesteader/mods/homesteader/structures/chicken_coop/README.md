# Chicken Coop (`chicken_coop`)

![Chicken Coop Icon](chicken_coop.png)

## Overview
- **Category**: `structures`
- **Item Identifier**: `chicken_coop`
- **Max Stack Size**: 1
- **Weight**: 0 kg
- **Base Economic Value**: $150
- **Consumable**: False

## Description
A percent lifecycle growing through 4 stages (foundation -> framing -> walls -> complete) over 100 percent. This group is the authoritative owner of the chicken_coop scheme.

## Properties
- **Is buyable**: `True`
- **Is blueprint**: `True`
- **Stores**: `depot`
- **Sale unit**: `blueprint`
- **Store category**: `Structures & Kits`

## Growth
- **Type**: `percent`
- **Species**: `chicken_coop`
- **Full age**: 100 percent

| Stage | Name | Age range |
| :--- | :--- | :--- |
| 1 | foundation | 0 to 33 |
| 2 | framing | 33 to 66 |
| 3 | walls | 66 to 99 |
| 4 | complete | 99 to 100 |

## Asset Files
- **Plugin Manifest (JSON)**: [chicken_coop.json](chicken_coop.json)
- **Icon (PNG)**: [chicken_coop.png](chicken_coop.png)
