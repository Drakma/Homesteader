# House wtih Garage (`house_garage`)

![House wtih Garage Icon](house_garage.png)

## Overview
- **Category**: `structures`
- **Item Identifier**: `house_garage`
- **Max Stack Size**: 1
- **Weight**: 0 kg
- **Base Economic Value**: $1500
- **Consumable**: False

## Description
A percent lifecycle growing through 4 stages (foundation -> framing -> walls -> complete) over 100 percent. This group is the authoritative owner of the large_metal_garage scheme.

## Properties
- **Is buyable**: `True`
- **Is blueprint**: `True`
- **Stores**: `depot`
- **Sale unit**: `blueprint`
- **Store category**: `Structures & Kits`

## Growth
- **Type**: `percent`
- **Species**: `house_garage`
- **Full age**: 100 percent

| Stage | Name | Age range |
| :--- | :--- | :--- |
| 1 | foundation | 0 to 12 |
| 2 | framing | 12 to 30 |
| 3 | walls | 30 to 60 |
| 4 | exterior | 60 to 80 |
| 5 | finishings | 80 to 100 |

## Asset Files
- **Plugin Manifest (JSON)**: [house_garage.json](house_garage.json)
- **Icon (PNG)**: [house_garage.png](house_garage.png)
