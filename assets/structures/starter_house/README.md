# Starter House (`starter_house`)

![Starter House Icon](starter_house.png)

## Overview
- **Category**: `structures`
- **Item Identifier**: `starter_house`
- **Max Stack Size**: 1
- **Weight**: 0 kg
- **Base Economic Value**: $1000
- **Consumable**: False

## Description
A percent lifecycle growing through 4 stages (foundation -> framing -> walls -> complete) over 100 percent. This group is the authoritative owner of the starter_house scheme.

## Properties
- **Is buyable**: `True`
- **Is blueprint**: `True`
- **Stores**: `depot`
- **Sale unit**: `blueprint`
- **Store category**: `Structures & Kits`

## Growth
- **Type**: `percent`
- **Species**: `starter_house`
- **Full age**: 100 percent

| Stage | Name | Age range |
| :--- | :--- | :--- |
| 1 | foundation | 0 to 20 |
| 2 | framing | 20 to 40 |
| 3 | walls | 40 to 60 |
| 4 | exterior | 60 to 80 |
| 5 | finishings | 80 to 100 |

## Asset Files
- **Plugin Manifest (JSON)**: [starter_house.json](starter_house.json)
- **Icon (PNG)**: [starter_house.png](starter_house.png)
