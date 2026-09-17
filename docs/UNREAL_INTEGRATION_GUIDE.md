# Homesteader - Unreal Engine 5 UI & Icon Integration Guide

Complete step-by-step guide for integrating the modern low-poly HUD, 10-slot hotbar, and 57 transparent item icons into the **Homesteader** Unreal Engine 5 project.

---

## 1. Asset Overview & File Structure

All transparent 32-bit RGBA PNG icons have been installed directly into your project:

```
C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\UI\Icons\
├── crop_corn.png
├── crop_tomato.png
├── crop_carrot.png
... (57 transparent item icons)
├── tool_axe.png
├── tool_pickaxe.png
├── tool_shovel.png
├── tool_watering_can.png
├── food_bread.png
├── meat_beef.png
└── Framed/
    └── *.png (optional framed slot tiles)
```

---

## 2. Importing Icons into Unreal Engine 5

When you open Unreal Editor or Drag & Drop the `Icons` folder into the Content Browser:

### Recommended Texture Settings for UI Icons

1. In the Content Browser, navigate to `/Game/Homesteader/UI/Icons/`.
2. Select all icons, right-click -> **Asset Actions** -> **Bulk Edit via Property Matrix**.
3. Set the following texture properties:
   - **Compression Settings**: `UserInterface2D (RGBA)`
   - **LOD Group (Texture Group)**: `UI`
   - **Mip Gen Settings**: `NoMipmaps`
   - **sRGB**: `True` (Checked)
   - **Filter**: `Default` or `Bilinear`
4. Click **Save All**.

> [!TIP]
> Setting `Compression Settings` to `UserInterface2D (RGBA)` preserves crisp alpha transparency with zero compression artifacts around low-poly edges.

---

## 3. Linking Icons to `DT_Items` DataTable

In `HomesteaderTypes.h`, the `FItemData` row struct already declares:

```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Item|Assets")
TSoftObjectPtr<UTexture2D> Icon;
```

To auto-populate the `Icon` column in `DT_Items.csv`, add the column `Icon` with the soft object path:

```csv
---Name,ItemID,DisplayName,Description,Category,MaxStackSize,Weight,BaseValue,bIsConsumable,HungerRestore,EnergyRestore,Icon
seed_corn,seed_corn,Corn Seeds,Seeds for planting corn.,Seed,99,0.1,2.0,false,0.0,0.0,"/Game/Homesteader/UI/Icons/seed_corn.seed_corn"
crop_corn,crop_corn,Corn,Fresh ear of corn.,Crop,50,0.3,5.0,true,15.0,0.0,"/Game/Homesteader/UI/Icons/crop_corn.crop_corn"
tool_axe,tool_axe,Axe,Chops wood and trees.,Tool,1,3.5,35.0,false,0.0,0.0,"/Game/Homesteader/UI/Icons/tool_axe.tool_axe"
meat_beef,meat_beef,Raw Beef,Raw beef steak.,AnimalProduct,30,0.5,15.0,true,25.0,5.0,"/Game/Homesteader/UI/Icons/meat_beef.meat_beef"
```

In Blueprints or C++, you can retrieve the icon texture:

```cpp
if (ItemData.Icon.IsValid())
{
    UTexture2D* IconTex = ItemData.Icon.Get();
    SlotImage->SetBrushFromTexture(IconTex);
}
else
{
    // Async load or load synchronous
    UTexture2D* IconTex = ItemData.Icon.LoadSynchronous();
    if (IconTex)
    {
        SlotImage->SetBrushFromTexture(IconTex);
    }
}
```

---

## 4. Expanding the Hotbar to 10 Slots

In `AHomesteaderPlayerController` (`Source/Homesteader/Private/Player/HomesteaderPlayerController.cpp`):

### A. Updating C++ Header (`HomesteaderPlayerController.h`)

Add input action handlers for slots 9 and 10:

```cpp
// Existing slots 1-8:
void OnHotbarSlot1(const FInputActionValue& Value);
...
void OnHotbarSlot8(const FInputActionValue& Value);

// Add slots 9 and 10:
void OnHotbarSlot9(const FInputActionValue& Value);
void OnHotbarSlot10(const FInputActionValue& Value);
```

### B. Updating C++ Implementation (`HomesteaderPlayerController.cpp`)

```cpp
// In SetupInputComponent:
EnhancedInputComponent->BindAction(IA_HotbarSlot9, ETriggerEvent::Started, this, &AHomesteaderPlayerController::OnHotbarSlot9);
EnhancedInputComponent->BindAction(IA_HotbarSlot10, ETriggerEvent::Started, this, &AHomesteaderPlayerController::OnHotbarSlot10);

// In method implementations:
void AHomesteaderPlayerController::OnHotbarSlot9(const FInputActionValue& Value) { OnHotbarSlot(9); }
void AHomesteaderPlayerController::OnHotbarSlot10(const FInputActionValue& Value) { OnHotbarSlot(10); }
```

### C. Mouse Wheel Scrolling for Hotbar

In `SetupInputComponent`:

```cpp
EnhancedInputComponent->BindAction(IA_HotbarScroll, ETriggerEvent::Triggered, this, &AHomesteaderPlayerController::OnHotbarScroll);

void AHomesteaderPlayerController::OnHotbarScroll(const FInputActionValue& Value)
{
    float ScrollDelta = Value.Get<float>();
    if (FMath::IsNearlyZero(ScrollDelta)) return;

    int32 NewSlot = CurrentHotbarSlot + (ScrollDelta > 0 ? -1 : 1);
    if (NewSlot < 1) NewSlot = 10;
    if (NewSlot > 10) NewSlot = 1;

    OnHotbarSlot(NewSlot);
}
```

---

## 5. UMG Layout Setup for `WBP_HUD`

In `WBP_HUD` (`Content/Homesteader/UI/HUD/WBP_HUD`):

```
[Canvas Panel] (Root)
│
├── [Horizontal Box] (Top Left Module - Player Status)
│   ├── Anchors: Top-Left (0, 0)
│   ├── Alignment: (0, 0)
│   ├── Position: (24, 24)
│   ├── Background Image: compact_player_status_kit.png
│   ├── ProgressBar: HungerBar (BindWidget)
│   └── ProgressBar: EnergyBar (BindWidget)
│
├── [Overlay] (Top Center Module - Time & Season)
│   ├── Anchors: Top-Center (0.5, 0)
│   ├── Alignment: (0.5, 0)
│   ├── Position: (0, 20)
│   ├── Background Image: compact_time_season_kit.png
│   ├── Image: SundialIcon (Rotating Image)
│   └── TextBlock: DayTimeText (BindWidget)
│
├── [Horizontal Box] (Top Right Module - Resources & Wallet)
│   ├── Anchors: Top-Right (1, 0)
│   ├── Alignment: (1, 0)
│   ├── Position: (-24, 24)
│   ├── Background Image: compact_resources_kit.png
│   └── TextBlock: MoneyText (BindWidget)
│
└── [Overlay] (Bottom Center Module - 10-Slot Hotbar)
    ├── Anchors: Bottom-Center (0.5, 1)
    ├── Alignment: (0.5, 1)
    ├── Position: (0, -20)
    ├── Background Image: compact_hotbar_tray_kit.png (or modular slots)
    ├── [UniformGridPanel / HorizontalBox]: 10 Slot Widgets
    │   └── Each Slot Widget contains:
    │       ├── Background: compact_hotbar_slot.png
    │       ├── Image: ItemIcon (Transparent 128x128 icon)
    │       ├── TextBlock: StackCountText (e.g. "x16")
    │       └── TextBlock: KeyNumber (1..0)
    └── Image: ActiveSelectionHighlight (compact_selector_active_kit.png)
```

---

## 6. Icon Verification Checklist

- [x] All 57 icons have **100% transparent backgrounds** (Alpha = 0 outside item geometry).
- [x] Anti-aliased edges are de-spilled (no dark halos against light game backgrounds).
- [x] All icons are standardized at **128×128 pixels** with clean inner padding.
- [x] Naming matches exact DataTable row IDs (`crop_corn`, `seed_wheat`, `tool_axe`, `meat_beef`, `mat_lumber`).
