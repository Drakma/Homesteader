# Homesteader - Unreal Engine 5 3D Model & Texture Integration Guide

This guide details how to import, configure, and assign the 3D low-poly Static Meshes and Master Color Palette Atlas into **Unreal Engine 5**.

---

## 1. Directory Structure in Content Browser

All 3D assets and textures are synchronized directly inside your Unreal project at:

```
Content/Homesteader/
├── Assets/
│   ├── Meshes/
│   │   ├── tools/hand_tools/       (SM_Tool_Axe, Pickaxe, Hoe, Shovel, Hammer, Wrench)
│   │   ├── tools/equipment/        (SM_Tool_Chainsaw)
│   │   ├── fishing/tackle/         (SM_Tool_FishingRod)
│   │   ├── farming/crops/          (SM_Crop_Corn, Tomato, Pumpkin)
│   │   ├── logging/wood/           (SM_Resource_WoodLogs)
│   │   ├── building/materials/     (SM_Resource_LumberPlank, StoneBlock)
│   │   ├── building/hardware/      (SM_Resource_NailsBox)
│   │   ├── electricity/generation/ (SM_Electric_SolarPanel, WindTurbine, Generator)
│   │   ├── water/sources/          (SM_Water_WellPump)
│   │   ├── water/treatment/        (SM_Water_FilterCanister)
│   │   ├── water/piping/           (SM_Water_PipeValve)
│   │   ├── sewage/drainage/        (SM_Sewage_SepticTank)
│   │   ├── sewage/treatment/       (SM_Sewage_CompostBin)
│   │   ├── internet/satellite_antennas/ (SM_Internet_SatelliteDish)
│   │   └── internet/routers_networking/ (SM_Internet_Router)
│   ├── Textures/
│   │   └── T_Homesteader_Palette.png   (512x512 Master Color Palette Atlas)
│   └── Materials/
│       └── M_Homesteader_Palette       (Master Material)
└── UI/
    └── Icons/                         (Categorized 128x128 UI Icons)
```

---

## 2. Step 1: Palette Texture Setup (`T_Homesteader_Palette`)

1. In the Content Browser, navigate to `/Game/Homesteader/Assets/Textures/`.
2. Right-click or drag-and-drop `T_Homesteader_Palette.png`.
3. Open `T_Homesteader_Palette` and set:
   - **Compression Settings**: `Default (DXT1/5, BC1/3 on DX11)` or `UserInterface2D (RGBA)`.
   - **Mip Gen Settings**: `NoMipmaps` (or `Sharpen0` with point/bilinear filtering).
   - **Texture Filter**: `Nearest` or `Bilinear` (Nearest guarantees zero color bleeding at edges).
   - **sRGB**: `Enabled` (Checked).

---

## 3. Step 2: Master Material Setup (`M_Homesteader_Palette`)

1. In `/Game/Homesteader/Assets/Materials/`, create a new Material named **`M_Homesteader_Palette`**.
2. Double-click to open the Material Graph:
   - Add a **Texture Sample** node selecting `T_Homesteader_Palette`.
   - Connect **RGB** output to the **Base Color** input of the Main Material Node.
   - Add a **Constant** scalar `0.6` and connect to **Roughness**.
   - Add a **Constant** scalar `0.4` and connect to **Specular**.
   - Add a **Constant** scalar `0.0` and connect to **Metallic**.
3. Click **Save** and **Apply**.

---

## 4. Step 3: Importing 3D Static Meshes (`.obj`)

1. In the Content Browser, navigate to the target subfolder under `/Game/Homesteader/Assets/Meshes/`.
2. Click **Import** (or drag and drop the `.obj` and `.mtl` files).
3. In the **FBX/OBJ Import Options** dialog:
   - **Mesh**:
     - **Vertex Color Import Option**: `Ignore`
     - **Transform**: Rotation `(0, 0, 0)`, Uniform Scale `1.0` (all models are pre-scaled in centimeters).
   - **Normal Generation**:
     - **Normal Import Method**: `Import Normals`
   - **Collision**:
     - **Generate Missing Collision**: `Enabled` (Auto Convex Collision).
   - **Material**:
     - **Material Search Location**: `Under Parent` or `Local`
     - **Base Material Name**: Select `M_Homesteader_Palette` (or assign after import).
4. Click **Import All**.

---

## 5. Step 4: Verification & Collision Inspection

1. Open any imported Static Mesh (e.g. `SM_Tool_Axe` or `SM_Electric_Generator`).
2. Click the **Collision** button in the toolbar to view the generated wireframe collision bounds.
3. Verify that the Material slot is assigned to `M_Homesteader_Palette`.
4. The model will display with faceted low-poly colors matching the HUD icon identically.

---

## 6. Real-World Metric Scaling Reference

| Mesh Asset                  | Bounding Box Dimensions (cm)                | Usage                          |
| :-------------------------- | :------------------------------------------ | :----------------------------- |
| `SM_Tool_Axe`               | $4.2 \times 21.5 \times 66.5\text{ cm}$     | Handheld wood-chopping axe     |
| `SM_Tool_Pickaxe`           | $4.5 \times 46.0 \times 82.0\text{ cm}$     | Handheld mining pickaxe        |
| `SM_Tool_Hoe`               | $14.0 \times 9.3 \times 120.0\text{ cm}$    | Handheld farming hoe           |
| `SM_Tool_Shovel`            | $18.0 \times 3.5 \times 98.5\text{ cm}$     | Handheld digging spade         |
| `SM_Tool_Chainsaw`          | $19.5 \times 80.5 \times 20.5\text{ cm}$    | Motorized logging tool         |
| `SM_Tool_FishingRod`        | $6.4 \times 10.5 \times 189.0\text{ cm}$    | Handheld fishing tackle        |
| `SM_Crop_Corn`              | $6.9 \times 7.0 \times 23.5\text{ cm}$      | Ground pickup / harvest item   |
| `SM_Crop_Pumpkin`           | $36.0 \times 34.2 \times 27.0\text{ cm}$    | Large farm crop pickup         |
| `SM_Crop_Tomato`            | $9.0 \times 9.0 \times 8.9\text{ cm}$       | Handheld fruit pickup          |
| `SM_Resource_WoodLogs`      | $50.0 \times 90.0 \times 44.5\text{ cm}$    | Ground timber resource         |
| `SM_Resource_LumberPlank`   | $20.0 \times 120.0 \times 13.0\text{ cm}$   | Construction lumber bundle     |
| `SM_Resource_StoneBlock`    | $40.0 \times 40.0 \times 27.0\text{ cm}$    | Quarried masonry block         |
| `SM_Electric_SolarPanel`    | $130.0 \times 85.0 \times 68.0\text{ cm}$   | Placeable electrical generator |
| `SM_Electric_WindTurbine`   | $165.8 \times 41.0 \times 382.5\text{ cm}$  | Placeable tall wind turbine    |
| `SM_Electric_Generator`     | $56.0 \times 44.0 \times 54.0\text{ cm}$    | Placeable combustion inverter  |
| `SM_Water_WellPump`         | $30.0 \times 49.0 \times 42.0\text{ cm}$    | Placeable utility pump         |
| `SM_Water_FilterCanister`   | $34.0 \times 18.0 \times 48.2\text{ cm}$    | Wall-mounted water purifier    |
| `SM_Water_PipeValve`        | $36.0 \times 11.0 \times 18.5\text{ cm}$    | Plumbing connector             |
| `SM_Sewage_SepticTank`      | $110.0 \times 200.0 \times 116.3\text{ cm}$ | In-ground septic tank          |
| `SM_Sewage_CompostBin`      | $85.0 \times 85.0 \times 75.0\text{ cm}$    | Backyard compost converter     |
| `SM_Internet_SatelliteDish` | $69.5 \times 54.5 \times 79.0\text{ cm}$    | Ground tripod receiver         |
| `SM_Internet_Router`        | $26.0 \times 19.2 \times 26.0\text{ cm}$    | Indoor network distributor     |
