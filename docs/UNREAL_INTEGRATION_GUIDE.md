# RETIRED: Unreal Engine 5 UI & Icon Integration Guide

> **THIS GUIDE IS RETIRED. DO NOT FOLLOW IT.**
>
> The project has officially switched from Unreal Engine 5 to **Unity 6 (`6000.6.0f1`)**.
> This document's icon import settings, DataTable linking, hotbar C++ code, and UMG
> layout instructions all reference Unreal Engine 5 and are no longer accurate.
>
> **See `docs/UNITY_INTEGRATION_GUIDE.md` instead.** It covers:
> - Icon import settings for Unity 6 (Sprite 2D and UI, no mip maps, RGBA 32 bit)
> - ScriptableObject `ItemDefinition.cs` (replacing UE5 `FItemData` struct + `DT_Items.csv`)
> - The full Meshy text-to-3D pipeline
>
> Key differences from the retired UE5 guide:
>
> | Old (UE5) | New (Unity 6) |
> | :--- | :--- |
> | `Content/Homesteader/UI/Icons/` | `Assets/Homesteader/UI/Icons/` |
> | `DT_Items.csv` DataTable | `ItemDefinition` ScriptableObject |
> | `FItemData` C++ struct with `TSoftObjectPtr<UTexture2D>` | C# class with `Sprite icon` field |
> | UMG `WBP_HUD` Canvas Panel | UI Toolkit UXML / Canvas |
> | C++ `AHomesteaderPlayerController` hotbar bindings | C# input system actions |
> | 57 icons | 70+ icons (and growing) |
>
> The icon count has grown from the 57 referenced in this retired guide to 70+,
> and the naming/folder conventions are now documented in
> `docs/ITEM_ICON_STYLE_GUIDE.md` §6 and `docs/ITEM_ORGANIZATION_GUIDE.md`.
