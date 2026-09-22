# RETIRED: 100% Free Stack Pipeline Guide

> **THIS PIPELINE NO LONGER EXISTS. DO NOT FOLLOW THIS GUIDE.**
>
> The **100% Free Stack** (FLUX.1 [schnell] for 2D + Tencent Hunyuan3D-2.0 for 3D) and
> `tools/free_generator.py` are **RETIRED**. **There is no free generation pipeline any
> more - everything costs money.**
>
> The one and only pipeline is **Meshy text-to-3D**, which returns the model **and its
> texture** in a single task. The icon is then **rendered from that model** in Blender.
>
> **See `MESHY_PIPELINE_GUIDE.md` instead.** (docs/MESHY_PIPELINE_GUIDE.md)

Key changes that replaced this document:

| Old (retired) | New (only pipeline) |
| :--- | :--- |
| FLUX.1 [schnell] 2D icon generation | No 2D generation - icon is rendered from the 3D model |
| Tencent Hunyuan3D-2.0 3D mesh | Meshy text-to-3D (tools/meshy_client.py -> create_text_to_3d()) |
| Standardized icon fed into 3D reconstruction | User's PROMPT='...' passed to Meshy as-is |
| tools/free_generator.py helpers | tools/meshy_client.py |
| Creative Claw concept images (paid opt-in) | Retired |
| Any model_type / smart-topology | model_type='lowpoly' ALWAYS, no exceptions |
| $0 cost, no approval needed | Paid - cost confirmation and explicit approval mandatory |

The Unity 6 engine specs, Blender metric/pivot rules and Mixamo/quadruped rigging
sections that used to live here are preserved in docs/MESHY_PIPELINE_GUIDE.md.
