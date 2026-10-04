# Animal models from the Downloads sheets: state (2026-10-04)

Source: `Downloads/animals` (28 sheets, 4 animals each: baby, juvenile, adult female, adult male). Split into 112 crops (`assets/_scratch/animals/<sheet>/<stage>.png`).
Pipeline per animal: Meshy image-to-3D (meshy-t2, smart-topology, textured, 15 credits) -> `tools/finish_animal_model.py` (realistic height, grounded, faces -Y = game +z) -> icon (`tools/render_icon_from_model.py`) -> `tools/integrate_animals.py` (stage models, manifests, yearling stage, stage `sexes` 80/20) -> catalog + mods.
Queue / driver / raw and final models: `assets/_scratch/animal_work/` (`run_meshy_batch.py`, `finish_batch.py`, `state.json`, `NOTES.md`).

## Done (64 animals, 16 groups, static models, ~4,200 triangles each)
holstein_cow, highland_cow, jersey_cow, duroc_pig, hampshire_pig, pink_pig, suffolk_sheep, tan_sheep, black_white_goat, brown_goat, white_goat, black_goat (new), red_chicken, white_chicken, welsummer_rooter, quarter_horse.
Each: baby, YEARLING (created where missing), adult = female with `sexes` (female 80 / male 20, both models in the adult folder). Old models are in `assets/_trash/animals_replaced/`.
Sheet names do not match their content: `cows/cow_jersey` = Holstein, `cows/cow_holstein` = Highland, `cows/Gemini...` = Jersey-like.

## Not done / unable
- RIGGING, WALK and RUN: Meshy's rigger is humanoid only (cow pilot: 24 humanoid bones, a "walking_man" clip, the body deforms badly). All animals are STATIC. They need Mesh2Motion (human fitting, docs/MESH2MOTION_SETUP.md) or a custom Blender quadruped rig; then gait_fix.py / loop_fix.py per the project rules (no foot skating, looping clips).
- Not generated (credits: 178 left, reserve kept): the other breeds of the sheets (48 animals): donkey, ox, alpaca, black cat, white cat, 3 dogs (australian shepherd, border collie, great pyrenees), painted / arabian / draft horse, american turkey. Their crops are ready; they need new growth groups (`NEW_GROUPS` in `tools/integrate_animals.py`) and about 720 credits.
- Old separate male items (animal_bull_holstein, black_white_billy_goat ...) and old standalone animal items are untouched (not folded or removed).
- Nothing has been checked in Unity yet: restart Play and check the console for `[Mods]` warnings about the animal groups.
- The Meshy models of babies/juveniles and some Highland ones have small texture/geometry artifacts (spiky fur bits); the sheets' wide horns are shorter in the models.
