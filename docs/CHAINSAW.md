# Chainsaw

A chainsaw (any item in `#tool_chainsaw`) fells trees and cuts stumps out with a right click. It is swept, not chopped (an axe still chops):

- Clip `Saw_Sideways` (peds_farmer_winter_saw_anims.glb, built by `tools/make_saw_clip.py`): both hands hold the saw at waist height, the bar level, and it moves cleanly from side to side (1.25 s per left-right-left sweep). The hands are IK-posed on moving targets and baked to the bones. Registered in `HudSceneBootstrap`; copy of the GLB in `StreamingAssets/Peds/peds_farmer_winter`.
- The held item (`HeldItemDisplay`) is tipped 90 degrees onto its side while the clip plays: its top faces the character's right, the bar points away from the body.
- Felling a tree with a chainsaw plays the same clip (`ForestTrees.FellClip`; a cut registers `SawImpact` into each sweep). The stump is cut after `ForestTrees.SawSeconds` (2.5 s, two sweeps), then the chips pile appears (`ForestTrees.ChainsawStump`). Axes still use the chop clip.
