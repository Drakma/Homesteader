# Cooking: the Meals List

A right click on a placed CUTTING BOARD (`kitchen_cutting_board_*`; no other object opens it; Shift + right click picks the board up), with no wrench in hand, opens the **Meals List**: every meal the
kitchen can make right now, and only those. "Make" takes the ingredients out of the kitchen and puts the result in the toolbar. Esc closes the list. A right click with a wrench still
takes a bolted-down piece up.

## What counts as the kitchen

From the object that was clicked: the same room of a finished building (`RoomMap`), or, when the object is outside a finished building (or in a wall cell with no room), everything within
6 m (`KitchenScan.Radius`). Reach is checked like a container (placement reach); the list closes when the player walks away.

- **Appliances** are every placed or mounted object in the kitchen. A meal asks for them by tag, so any member of the tag will do.
- **Ingredients** are everything stocked in the kitchen's placed containers (fridges, freezers, base cabinets, pantry, island, cart: they carry a `container` block, 36 kitchen items, take
  `food` and `ingredients`, stocked with the C key like any container) and on its shelves (the open shelf). The toolbar is NOT searched: stock the kitchen first.

## Meals are mod data

Content type `meal`: `assets/_meals/*.json`, packaged to `meals/*.json` by `tools/package_catalog_as_mods.py`, loaded by `ModLoader.LoadMeals` into `MealRegistry`. Format and checker:
`tools/meal_format.py` (run it: `python tools/meal_format.py`). Schema: `assets/_schemas/meal.schema.json`.

```json
{ "meals": [ {
    "id": "meal_bake_bread", "name": "Bake Bread", "group": "Baking",
    "result": { "item_id": "food_bread", "quantity": 4 },
    "ingredients": [ { "item_id": "ingredient_flour", "quantity": 1 }, { "item_id": "ingredient_yeast", "quantity": 1 } ],
    "appliances": [ { "tools": ["#appliance_oven"] } ]
} ] }
```

- `ingredients` is the **recipe tree** (lines `{item_id (item | #tag | ~equivalency), quantity}`, sections `{section, mode: all|any, if: {uses|not_uses}, items}`; `tools/recipe_format.py`).
  An item with `properties.uses_per_item` (flour 10, sugar 10, salt 150 (5 g a use), yeast 8, baking powder 12, butter 32 (a tablespoon a use), ground pepper 60, herbs 40: the same field a seed packet uses; 1 in a recipe is ONE use, a pinch or a spoon, never the whole carton) is used a bit at a time: the quantity of a line is
  in USES, the opened bag is used up first and a new one opened when it runs out (`ContainerStack.Used`, `Shelf.Held.WireUsed`, saved). Any other item is consumed whole.
  An opened bag keeps its uses when it goes into or out of a container (out: when it is the only stack of that item in the toolbar).
- `appliances` is a list of groups; the kitchen needs ANY ONE tool (item id or `#tag`) of EACH group. Not consumed.
- Appliance tags (in `assets/_schemas/material_tags.json`): `#appliance_oven`, `#appliance_stovetop`, `#appliance_grill`, `#appliance_grain_mill`; `#kitchen_appliance` marks the household
  appliances (fridge, sink, microwave ...) that also open the list.

## The starter meals (`python tools/make_meals.py`)

- `milling.json`: every grain is milled at the grain mill into a sack (3 grain) or a BULK sack (15 grain): wheat to All-Purpose Flour, corn to Corn Flour, oats to Oat Flour, barley to Barley Flour, soybeans to Soy Flour, flax to Flax Meal. The sacks are 1 kg (10 uses) and a bulk 5 kg sack of each (`..._5kg`, 50 uses, `stacking_limit` 4 so identical sacks stack on a pallet). The `#flour` tag holds every flour (not flax meal, which is a meal, not a flour); the planner cooks a missing `#flour` from the first member it can mill.
- `baking.json` (hand-written): Bake Bread, Burger Buns and Hot Dog Buns (any `#flour` 3 uses, yeast, salt, oven) and the hamburger / hot dog assembly.
- `cooking.json` (derived): every ingredient whose manifest says `processing_method` grill / bake / cook with a `next_item_id` becomes a raw -> cooked meal. Grill: grill or stovetop; bake: oven;
  cook: stovetop or oven. Add a new ingredient with a `next_item_id`, rerun `make_meals.py`, repackage.

## Juices, jams and nut butters: meals that fill a container

A meal can FILL a container instead of making an item: `"result": {"container": "<empty liquid container item>", "liquid": "<liquid item>", "liters": L?}`. It needs an empty one in the kitchen
(stocked in a container or on a shelf). The container is NOT used up and is not a one-use item: it comes back FULL in the toolbar (the liquid kept in it, `ToolbarSlotData.LiquidId` and
`WireUsed`), and what a jar holds is kept wherever it goes: into a kitchen cabinet or fridge (`ContainerStack.Liquid` / `Stored`, a stack of its own per filled jar, saved), onto a shelf
(`Shelf.Held.LiquidId`), back out. Plain empties still stack. Stocking a kitchen container with `#canning_container` items is allowed (the kitchen storage `accepts` it).

- **Containers** (kitchen category, `tools/make_canning_assets.py`, `liquid_container` block, sold empty at the grocer): Juice Bottle (1 L), Large Juice Bottle (2 L), a Butter Jar (450 g, 0.41 L) and a Large Butter Jar (900 g, 0.82 L) each for peanut, walnut, pecan and hazelnut butter (each takes only its own butter), Jam Jar (350 ml), Large Jam Jar (900 ml).
  The juice bottles take the `#juice` tag, the jam jars `#jam`.
- **Liquids** (`tools/make_liquid_assets.py`): 12 juices (`liquid_juice_<fruit>`), 13 jams (`liquid_jam_<fruit>`) and 4 nut butters (`liquid_<nut>_butter`). The old single-size `food_jam_*` items were removed.
- **Appliances** (tags): the Countertop Juicer (`kitchen_juicer_*`, `#appliance_juicer`), the blender (`kitchen_blender_*`, `#appliance_blender`), the stove (`#appliance_stovetop`).
- **Meals** (`assets/_meals/canning.json`, from `tools/make_meals.py`): a juice takes the fruit (4 apples a litre) and 1 use of sugar a litre at the juicer; a jam takes the fruit, sugar and Unflavored
  Gelatin (a pantry item, 8 uses) on the stove; a nut butter takes the nuts (peanuts, walnuts, pecans, hazelnuts) and salt in the blender. Each comes in the small and the large container (58 meals).

## Oils: the Countertop Oil Press

The **Countertop Oil Press** (`kitchen_oil_press_*`, `#appliance_oil_press`) squeezes seeds into oil, one bottle at a time (`assets/_meals/oils.json`, `tools/make_meals.py`). There is an oil bottle for each oil in two sizes, 750 mL and 2 L
(`kitchen_oil_bottle_<oil>_750ml` / `_2l`, liquid containers that take only their own oil, `tools/make_canning_assets.py`; stored like the jars, `#canning_container`): sunflower, soybean, corn, cottonseed, peanut, flaxseed and canola oil (the liquids
`liquid_<oil>_oil`), and **vegetable oil**.

- **Pressing:** seeds in an empty bottle at the press: sunflower seeds, soybeans, corn, cotton, peanuts or flax (4 to 7 seeds for a 750 mL bottle, 10 to 18 for 2 L), see `PRESS` in `tools/make_meals.py`.
- **Vegetable oil is a BLEND**, poured from bottles of the pressed oils you already have (a meal with `liquids` instead of ingredients: `MealDef.Liquids`, no appliance; the bottles keep what is left). There is no standard formula: a "vegetable oil blend"
  label names the oils in it (soybean, canola, sunflower, corn, cottonseed), and the proportions are the maker's. The game's blend is **40% soybean oil, 30% canola oil, 15% corn oil, 10% sunflower oil, 5% cottonseed oil** (`BLEND`), poured into an empty vegetable
  oil bottle (soybean being the usual main oil). Sources: https://seedoilfreecertified.com/seed-oils-guide/what-vegetable-oil-blend-means
- **Canola** is a crop (`assets/farming/canola`, seed `seed_canola`, harvest `ingredient_canola`, a burlap sack; built in code in `ProceduralCrops.cs` with a cloud of yellow flowers while it matures, pods when ripe; kit stages from
  `tools/build_crop_groups.py` after Homesteader / Export Crop Models). Planted in spring, ripe in 95 days; 5 seeds press a 750 mL bottle of canola oil, 13 a 2 L bottle.
- **Meals editor and validation (kit)**: the kit server (`tools/server.py`) serves `GET /api/meals` (files, or `?file=name.json` for one with its problems), `POST /api/validate-meals` and `POST /api/save-meals` (a problem rejects the save), all through `tools/meal_format.py`; the page `assets/meals.html` (open it from the kit server, linked as Meals Editor) lists the files and meals, edits a meal as JSON, validates and saves. Files written by `tools/make_meals.py` are regenerated when it runs, so edit the generator for those; a file of your own (a new `assets/_meals/<name>.json`) is edited only here. After saving run `tools/package_catalog_as_mods.py`.
- **More dishes** (`tools/dish_data.py` is the one table for the items AND the meals; items from `tools/make_dishes_more.py`, icons cut from Gemini sheets by `tools/extract_icon_sheet.py` into `assets/_scratch/dishes`): Breakfast (Oatmeal, Grits, Pancakes, Scrambled Eggs, Bacon and Eggs, French Toast), Mains (Beef Stew, Chicken Stew, Meatloaf, Shepherd's Pie, Roast Chicken, Pot Roast), Sides (Mashed Potatoes, Baked Potato, Roasted Vegetables), Salads (Garden, Coleslaw, Spinach: put together on the counter, no appliance) and Desserts (Apple, Cherry, Blueberry and Pumpkin Pie, Yellow Cake, Sugar Cookies). Stove dishes need `#appliance_stovetop`, baked ones `#appliance_oven`. A dish with `bowl=True` (oatmeal, grits, the stews) takes a Soup Bowl per serving and leaves it when eaten, like the soups, and does not go on a plate in the Meal Builder.
- **Eating and drinking** (`Kitchen/Consumption.cs`): G eats or drinks the held item (see docs/CONTROLS.md). Foods give `category_fields.hunger_restore` and `properties.thirst_restore` / `stamina_restore` / `wellness_modifier` to the vitals (each -100..100, full is 100); a drink gives its liquid's `thirst_restore` (and the others) per 0.25 L sip; a plated meal gives the sum of everything on it. `properties.leaves_item` is what is left (soups: `kitchen_bowl`; the plated meal: `kitchen_plate`), put in the slot or the toolbar. `Metabolism` lowers hunger (empty in 5 game days) and thirst (3 game days) with game time while the game runs; nothing else happens at the bottom of the scale yet. Constants at the top of `Metabolism`.
- **Quick breads** (`baking.json`): Cornbread (4), Corn Muffins (6), Muffins (6) and a fruit muffin (6) for each of 16 fruits (blueberry, strawberry, raspberry, cherry, apple, peach, pear, apricot, plum, fig, huckleberry, elderberry, haskap, lemon, orange, rhubarb), baked in an oven or range (`#appliance_oven`). They use cornmeal, `#flour`, `#sugar`, baking powder, salt, egg, butter and 2 of the fruit (cornmeal and flour are milled first if the kitchen has none). The icons are Gemini sheets cut by `tools/extract_icon_sheet.py`; items from `tools/make_muffin_items.py`.
- **Soups and pasta** (in `baking.json`, made by `tools/make_meals.py`): everything is cooked on a stovetop (`#appliance_stovetop`, which a range counts as). `ingredient_pasta` (Dry Pasta, a box, also in a bulk 5 kg sack) is bought or made at the counter from `#flour` and eggs. Pasta Sauce (`ingredient_pasta_sauce`, a jar of 4 uses) is simmered from 4 tomatoes, herbs and salt. Pasta dishes (Spaghetti with Sauce, Spaghetti and Meatballs, Sausage Pasta, Buttered Noodles, Macaroni and Cheese) are foods that go on a plate. Soups (Tomato, Vegetable, Chicken Noodle, Potato, Beef Barley, Pumpkin) take one **Soup Bowl** (`kitchen_bowl`, in the `#tableware` tag, stored in the same cabinets as plates) per serving: the bowl goes into the soup. Dish icons from `tools/make_dish_items.py`; the bowl from `tools/make_tableware_assets.py`.
- **Milled grains and bulk sacks**: the mill also makes Rolled Oats (oats), Cornmeal and Grits (corn), Pearl Barley (barley) and Cracked Wheat (wheat), each as a 1 kg sack (3 grain) and a bulk 5 kg sack (15 grain); all are in the `#milled_grain` tag. Salt, yeast, baking powder and gelatin also have bulk 5 kg sacks (`..._5kg`, palletizable). Items are defined in `tools/make_pantry_assets.py`, the mill meals in the `MILL` table of `tools/make_meals.py`.
- **Sugar** now has a 1 kg sack and a bulk 5 kg sack (`ingredient_sugar_5kg`, palletizable like the flour sacks); the `#sugar` tag holds both and the jam and juice meals take `#sugar`.

## The Meal Builder

The Meals List has a **Meal Builder** button. It sets up a plate with room for FOUR foods and a glass for ONE drink, all from the kitchen (the same scan as the Meals List):

- **Foods** are the stocked items of category `food`, AND any food the kitchen can COOK from what it has: a food that is not stocked is cooked from its ingredients by the meal that makes it, and what that
  meal needs may itself be cooked (a bread: wheat is milled to flour at the grain mill, then baked with yeast and salt in the oven). Those rows say "(cook it)". Click a food to put its ICON on the plate;
  click a food on the plate to take it off. `MealPlanner` works the whole job out in advance (`MealPlan`: the cookings in order and everything they take from the kitchen), without touching the kitchen.
- **Bowl** (one spot beside the plate): a soup, stew or salad (a food whose `leaves_item` is `kitchen_bowl`; the three salads are bowl dishes too, so cooking one takes a Soup Bowl). It carries its own bowl, so serving takes no extra one. It is served as a **Bowl of Food** (`kitchen_bowl_meal`, a one-food container; eaten it leaves the bowl).
- **How a served dish looks** (`Growth/DishView.cs`, attached to a placed Plated Meal, Bowl of Food or Drinking Glass): the foods' icons lie flat on the plate; the bowl is filled with the middle of the food's icon (its texture); the glass is filled with its liquid (colour, opacity and height from the litres). Foods have no models of their own: they are eaten, never placed, so the asset audit does not ask for one.
- **Drinks** are the filled containers of a `#drink` liquid (juice, milk, water, cider) in the kitchen's cabinets and shelves. Click one to fill the glass; it is poured from a bottle or jug (the bottle keeps what is left).
- **Make** (also for a saved meal, and for any meal of the Meals List) walks the ped to each appliance the plan needs, in order (`KitchenCook`: it walks to about a metre from the appliance, works there with the nearest
  clip it has, then walks on; there are no cooking clips yet: a standing pour at the stove, the grill, the mill, the juicer and the blender, crouching at the oven), then to where the meal is served. Nothing is taken from the
  kitchen until the end, so a movement key stops the cooking at no cost.
- **Serving**: the foods, a clean **Dinner Plate** (`kitchen_plate`) and every cooking's ingredients are taken from the kitchen and an empty **Drinking Glass** (`kitchen_glass`, a 0.3 L liquid container, takes `#drink`) is
  filled. The **Plated Meal** (`kitchen_plated_meal`, a container item holding the foods, up to 4) and the filled glass are put ON THE NEAREST COUNTER (a placed piece that carries things on top: base cabinets, the island,
  the work counter, the cart; `PalletDeck.FindSpot` packs them in the free space, the glass beside the plate). A **right click picks them up** (a plated meal keeps its foods, a glass its drink). With no counter room they go to the
  toolbar, else onto the floor by the clicked object. Plates and glasses are kitchen items sold at the furniture store; stock them in a cabinet or on a shelf (the kitchen storage accepts `#tableware`).
- **Save** keeps the meal under a name (`SavedMeals`, saved in the save file as `GameSave.savedMeals`); a saved meal lists its icons, **Make** cooks and serves it again with one click while the kitchen can supply it (the tooltip
  says what is missing), **Load** puts it back on the plate to change it, X forgets it. Saving the same name again replaces it.

Code: `Kitchen/MealBuilder.cs` (rules, serving), `MealPlanner.cs` (the plan), `KitchenCook.cs` (the walking), `MealBuilderPanel.cs` (window), `SavedMeals.cs`; `KitchenScan.Drinks` / `DrinkSource` / `Counters` / `ApplianceObjects`.
Kitchen furniture is bolted down (a right click opens the Meals List); the portable pieces (plates, glasses, jars, plated meals) are not: a right click picks them up (`MealsPanel.IsKitchenObject`).
Not yet: eating or drinking the result.

Not yet: water (a mixing meal does not ask for `~water`), deep frying (oil), meals with several steps, a recipe editor in the asset kit, greyed-out "missing" meals (only makeable ones are listed on purpose).

Code: `Assets/Scripts/Kitchen/` (`MealRegistry`, `KitchenScan` + `MealMaker`, `MealsPanel`). Hooks: `PlacementController` (placed objects), `AttachedObject.TryPickUpAtRay` (mounted ones), `HudBindings` (Esc).
