"""
Writes the starter MEALS (assets/_meals/*.json, format: tools/meal_format.py, docs/COOKING.md):

  baking.json   hand-written: milling flour and baking bread.
  cooking.json  derived from the item manifests: every ingredient whose category_fields say processing_method grill / bake / cook and whose
                next_item_id exists becomes a meal (raw -> cooked), cooked on the right appliance.

    python tools/make_meals.py ; python tools/meal_format.py
Afterwards: python tools/package_catalog_as_mods.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meal_format as MF

ROOT = MF.ROOT
OUT = MF.MEALS_DIR
HAND_WRITTEN = {'ingredient_flour', 'ingredient_corn_flour', 'ingredient_oat_flour', 'ingredient_barley_flour', 'ingredient_soy_flour', 'ingredient_flax_meal'}                  # ingredients whose meals are in BAKING (more than a straight raw -> cooked step)
METHOD_APPLIANCES = {                                # processing_method -> the appliance groups it needs (any one of each group)
    'grill': [{'tools': ['#appliance_grill', '#appliance_stovetop']}],
    'bake': [{'tools': ['#appliance_oven']}],
    'cook': [{'tools': ['#appliance_stovetop', '#appliance_oven']}],
}
GROUP = {'grill': 'Grilling', 'bake': 'Baking', 'cook': 'Cooking'}

BAKING = [
    {'id': 'meal_bake_bread', 'name': 'Bake Bread', 'group': 'Baking', 'result': {'item_id': 'food_bread', 'quantity': 4},
     'ingredients': [{'item_id': '#flour', 'quantity': 3}, {'item_id': 'ingredient_yeast', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_bake_burger_buns', 'name': 'Bake Burger Buns', 'group': 'Baking', 'result': {'item_id': 'food_burger_bun', 'quantity': 6},
     'ingredients': [{'item_id': '#flour', 'quantity': 3}, {'item_id': 'ingredient_yeast', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': '#sugar', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_bake_hot_dog_buns', 'name': 'Bake Hot Dog Buns', 'group': 'Baking', 'result': {'item_id': 'food_hot_dog_bun', 'quantity': 6},
     'ingredients': [{'item_id': '#flour', 'quantity': 3}, {'item_id': 'ingredient_yeast', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': '#sugar', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    # quick breads: an oven or a range (the #appliance_oven tag holds both). Cornmeal and flour are milled first if the kitchen has none
    {'id': 'meal_bake_cornbread', 'name': 'Bake Cornbread', 'group': 'Baking', 'result': {'item_id': 'food_cornbread', 'quantity': 4},
     'ingredients': [{'item_id': 'ingredient_cornmeal', 'quantity': 2}, {'item_id': '#flour', 'quantity': 1}, {'item_id': '#sugar', 'quantity': 1}, {'item_id': 'ingredient_baking_powder', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'ingredient_egg', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_bake_corn_muffins', 'name': 'Bake Corn Muffins', 'group': 'Baking', 'result': {'item_id': 'food_corn_muffin', 'quantity': 6},
     'ingredients': [{'item_id': 'ingredient_cornmeal', 'quantity': 2}, {'item_id': '#flour', 'quantity': 1}, {'item_id': '#sugar', 'quantity': 1}, {'item_id': 'ingredient_baking_powder', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'ingredient_egg', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_bake_muffins', 'name': 'Bake Muffins', 'group': 'Baking', 'result': {'item_id': 'food_muffin', 'quantity': 6},
     'ingredients': [{'item_id': '#flour', 'quantity': 3}, {'item_id': '#sugar', 'quantity': 1}, {'item_id': 'ingredient_baking_powder', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'ingredient_egg', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    # pasta, sauce and soups: on the stove (a pot). A soup takes a Soup Bowl for each serving.
    {'id': 'meal_cook_pasta_sauce', 'name': 'Simmer Pasta Sauce', 'group': 'Cooking', 'result': {'item_id': 'ingredient_pasta_sauce', 'quantity': 1},
     'ingredients': [{'item_id': 'food_tomato', 'quantity': 4}, {'item_id': 'ingredient_herbs', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_alfredo_sauce', 'name': 'Simmer Alfredo Sauce', 'group': 'Cooking', 'result': {'item_id': 'ingredient_alfredo_sauce', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_butter', 'quantity': 4}, {'item_id': 'food_cheese', 'quantity': 2}, {'item_id': 'ingredient_pepper_ground', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_spaghetti', 'name': 'Cook Spaghetti Marinara', 'group': 'Pasta', 'result': {'item_id': 'food_spaghetti', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_pasta', 'quantity': 2}, {'item_id': 'ingredient_pasta_sauce', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_spaghetti_meatballs', 'name': 'Cook Spaghetti and Meatballs', 'group': 'Pasta', 'result': {'item_id': 'food_spaghetti_meatballs', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_pasta', 'quantity': 2}, {'item_id': 'ingredient_pasta_sauce', 'quantity': 1}, {'item_id': 'ingredient_ground_beef', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_sausage_pasta', 'name': 'Cook Sausage Pasta', 'group': 'Pasta', 'result': {'item_id': 'food_sausage_pasta', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_pasta', 'quantity': 2}, {'item_id': 'ingredient_pasta_sauce', 'quantity': 1}, {'item_id': 'ingredient_sausage', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_buttered_noodles', 'name': 'Cook Buttered Noodles', 'group': 'Pasta', 'result': {'item_id': 'food_buttered_noodles', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_pasta', 'quantity': 2}, {'item_id': 'ingredient_butter', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_mac_and_cheese', 'name': 'Cook Macaroni and Cheese', 'group': 'Pasta', 'result': {'item_id': 'food_mac_and_cheese', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_pasta', 'quantity': 2}, {'item_id': 'food_cheese', 'quantity': 2}, {'item_id': 'ingredient_butter', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_tomato_soup', 'name': 'Cook Tomato Soup', 'group': 'Soups', 'result': {'item_id': 'food_tomato_soup', 'quantity': 2},
     'ingredients': [{'item_id': 'food_tomato', 'quantity': 3}, {'item_id': 'ingredient_herbs', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'kitchen_bowl', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_vegetable_soup', 'name': 'Cook Vegetable Soup', 'group': 'Soups', 'result': {'item_id': 'food_vegetable_soup', 'quantity': 2},
     'ingredients': [{'item_id': 'food_potato', 'quantity': 1}, {'item_id': 'food_carrot', 'quantity': 1}, {'item_id': 'food_onion', 'quantity': 1}, {'item_id': 'food_green_beans', 'quantity': 1}, {'item_id': 'food_tomato', 'quantity': 1}, {'item_id': 'ingredient_herbs', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'kitchen_bowl', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_chicken_noodle_soup', 'name': 'Cook Chicken Noodle Soup', 'group': 'Soups', 'result': {'item_id': 'food_chicken_noodle_soup', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_chicken', 'quantity': 1}, {'item_id': 'ingredient_pasta', 'quantity': 1}, {'item_id': 'food_carrot', 'quantity': 1}, {'item_id': 'food_onion', 'quantity': 1}, {'item_id': 'ingredient_herbs', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'kitchen_bowl', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_potato_soup', 'name': 'Cook Potato Soup', 'group': 'Soups', 'result': {'item_id': 'food_potato_soup', 'quantity': 2},
     'ingredients': [{'item_id': 'food_potato', 'quantity': 3}, {'item_id': 'food_onion', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}, {'item_id': 'ingredient_bacon', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'kitchen_bowl', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_beef_barley_soup', 'name': 'Cook Beef Barley Soup', 'group': 'Soups', 'result': {'item_id': 'food_beef_barley_soup', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_beef', 'quantity': 1}, {'item_id': 'ingredient_pearl_barley', 'quantity': 1}, {'item_id': 'food_carrot', 'quantity': 1}, {'item_id': 'food_onion', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'kitchen_bowl', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_cook_pumpkin_soup', 'name': 'Cook Pumpkin Soup', 'group': 'Soups', 'result': {'item_id': 'food_pumpkin_soup', 'quantity': 2},
     'ingredients': [{'item_id': 'food_pumpkin', 'quantity': 1}, {'item_id': 'food_onion', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'kitchen_bowl', 'quantity': 2}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_toast_bread', 'name': 'Toast Bread', 'group': 'Baking', 'result': {'item_id': 'ingredient_bread_toasted', 'quantity': 2},
     'ingredients': [{'item_id': 'food_bread', 'quantity': 2}], 'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_make_bread_crumbs', 'name': 'Smash Bread Crumbs', 'group': 'Assembly', 'result': {'item_id': 'ingredient_bread_crumbs', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_bread_toasted', 'quantity': 4}], 'appliances': []},
    {'id': 'meal_deepfry_bass', 'name': 'Deep Fry Bass', 'group': 'Frying', 'result': {'item_id': 'food_bass_deepfried', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_fillet_bass', 'quantity': 1}, {'item_id': 'ingredient_bread_crumbs', 'quantity': 1}, {'item_id': '#cooking_oil', 'quantity': 4}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_deepfry_catfish', 'name': 'Deep Fry Catfish', 'group': 'Frying', 'result': {'item_id': 'food_catfish_deepfried', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_fillet_catfish', 'quantity': 1}, {'item_id': 'ingredient_bread_crumbs', 'quantity': 1}, {'item_id': '#cooking_oil', 'quantity': 4}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_deepfry_crappie', 'name': 'Deep Fry Crappie', 'group': 'Frying', 'result': {'item_id': 'food_crappie_deepfried', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_fillet_crappie', 'quantity': 1}, {'item_id': 'ingredient_bread_crumbs', 'quantity': 1}, {'item_id': '#cooking_oil', 'quantity': 4}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_deepfry_trout', 'name': 'Deep Fry Trout', 'group': 'Frying', 'result': {'item_id': 'food_trout_deepfried', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_fillet_trout', 'quantity': 1}, {'item_id': 'ingredient_bread_crumbs', 'quantity': 1}, {'item_id': '#cooking_oil', 'quantity': 4}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_deepfry_walleye', 'name': 'Deep Fry Walleye', 'group': 'Frying', 'result': {'item_id': 'food_walleye_deepfried', 'quantity': 1},
     'ingredients': [{'item_id': 'ingredient_fillet_walleye', 'quantity': 1}, {'item_id': 'ingredient_bread_crumbs', 'quantity': 1}, {'item_id': '#cooking_oil', 'quantity': 4}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    # made from what the farm gives: dairy, cured pork, ground meat, sugar and yeast
    {'id': 'meal_make_cheese', 'name': 'Make Cheese', 'group': 'Dairy', 'result': {'item_id': 'food_cheese', 'quantity': 2},
     'ingredients': [{'item_id': 'liquid_milk', 'quantity': 20}, {'item_id': 'food_lemon', 'quantity': 1}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_churn_butter', 'name': 'Churn Butter', 'group': 'Dairy', 'result': {'item_id': 'ingredient_butter', 'quantity': 1},
     'ingredients': [{'item_id': 'liquid_cream', 'quantity': 20}, {'item_id': 'ingredient_salt', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_blender']}]},
    {'id': 'meal_grind_beef', 'name': 'Grind Beef', 'group': 'Butchering', 'result': {'item_id': 'ingredient_ground_beef', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_beef', 'quantity': 1}], 'appliances': [{'tools': ['#appliance_blender']}]},
    {'id': 'meal_make_sausage', 'name': 'Make Sausage', 'group': 'Butchering', 'result': {'item_id': 'ingredient_sausage', 'quantity': 4},
     'ingredients': [{'item_id': 'ingredient_pork', 'quantity': 2}, {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'ingredient_herbs', 'quantity': 1}, {'item_id': 'ingredient_pepper_ground', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_blender']}]},
    {'id': 'meal_cure_bacon', 'name': 'Cure Bacon', 'group': 'Butchering', 'result': {'item_id': 'ingredient_bacon', 'quantity': 4},
     'ingredients': [{'item_id': 'ingredient_pork', 'quantity': 2}, {'item_id': 'ingredient_salt', 'quantity': 2}, {'item_id': '#sugar', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_cure_ham', 'name': 'Cure Ham', 'group': 'Butchering', 'result': {'item_id': 'ingredient_ham', 'quantity': 2},
     'ingredients': [{'item_id': 'ingredient_pork', 'quantity': 3}, {'item_id': 'ingredient_salt', 'quantity': 3}, {'item_id': '#sugar', 'quantity': 1}],
     'appliances': [{'tools': ['#appliance_oven']}]},
    {'id': 'meal_boil_maple_sugar', 'name': 'Boil Maple Sugar', 'group': 'Preserving', 'result': {'item_id': 'ingredient_sugar', 'quantity': 1},
     'ingredients': [{'item_id': 'liquid_maple_syrup', 'quantity': 20}], 'appliances': [{'tools': ['#appliance_stovetop']}]},
    {'id': 'meal_start_yeast', 'name': 'Start Yeast', 'group': 'Baking', 'result': {'item_id': 'ingredient_yeast', 'quantity': 1},
     'ingredients': [{'item_id': '#flour', 'quantity': 1}, {'item_id': '#sugar', 'quantity': 1}, {'item_id': 'liquid_water', 'quantity': 6}], 'appliances': []},
    {'id': 'meal_make_pasta', 'name': 'Make Pasta', 'group': 'Assembly', 'result': {'item_id': 'ingredient_pasta', 'quantity': 1},
     'ingredients': [{'item_id': '#flour', 'quantity': 3}, {'item_id': 'ingredient_egg', 'quantity': 2}], 'appliances': []},
    # put together on the counter: no appliance. The buns and the grilled patty / sausage are cooked first if the kitchen has none (the Meal Builder plans that)
    {'id': 'meal_assemble_burger', 'name': 'Make a Hamburger', 'group': 'Assembly', 'result': {'item_id': 'food_burger', 'quantity': 1},
     'ingredients': [{'item_id': 'food_burger_bun', 'quantity': 1}, {'item_id': 'food_ground_beef_grilled', 'quantity': 1}], 'appliances': []},
    {'id': 'meal_assemble_hot_dog', 'name': 'Make Hot Dogs', 'group': 'Assembly', 'result': {'item_id': 'food_hot_dog', 'quantity': 3},
     'ingredients': [{'item_id': 'food_hot_dog_bun', 'quantity': 3}, {'item_id': 'food_sausage_grilled', 'quantity': 1}], 'appliances': []},
]


# a fruit muffin: the plain muffin dough plus two of the fruit (every fruit food the game has)
FRUIT_MUFFINS = ('blueberry', 'strawberry', 'raspberry', 'cherry', 'apple', 'peach', 'pear', 'apricot', 'plum', 'fig', 'huckleberry', 'elderberry', 'haskap', 'lemon', 'orange', 'rhubarb')
for _f in FRUIT_MUFFINS:
    BAKING.append({'id': 'meal_bake_%s_muffins' % _f, 'name': 'Bake %s Muffins' % _f.capitalize(), 'group': 'Baking', 'result': {'item_id': 'food_%s_muffin' % _f, 'quantity': 6},
                   'ingredients': [{'item_id': '#flour', 'quantity': 3}, {'item_id': 'food_%s' % _f, 'quantity': 2}, {'item_id': '#sugar', 'quantity': 1}, {'item_id': 'ingredient_baking_powder', 'quantity': 1},
                                   {'item_id': 'ingredient_salt', 'quantity': 1}, {'item_id': 'ingredient_egg', 'quantity': 1}, {'item_id': 'ingredient_butter', 'quantity': 1}],
                   'appliances': [{'tools': ['#appliance_oven']}]})


# the dishes (tools/dish_data.py): cooked on the stove or in the oven, or put together on the counter; a bowl dish takes a Soup Bowl for each serving
import dish_data  # noqa: E402
for _d in dish_data.DISHES:
    _ing = [{'item_id': i, 'quantity': q} for i, q in _d['ingredients']]
    if _d['bowl']:
        _ing.append({'item_id': 'kitchen_bowl', 'quantity': _d['servings']})
    BAKING.append({'id': 'meal_make_%s' % _d['id'][5:], 'name': ('Make ' if _d['appliance'] is None else 'Cook ' if _d['appliance'] == dish_data.S else 'Chill ' if _d['appliance'] == '#appliance_fridge' else 'Freeze ' if _d['appliance'] == '#appliance_freezer' else 'Bake ') + _d['name'], 'group': _d['group'],
                   'result': {'item_id': _d['id'], 'quantity': _d['servings']}, 'ingredients': _ing, 'appliances': [{'tools': [_d['appliance']]}] if _d['appliance'] else []})


def manifests():
    out = {}
    for path in glob.glob(os.path.join(MF.ASSETS, '*', '*', '*.json')):
        folder = os.path.basename(os.path.dirname(path))
        if os.path.basename(path) != folder + '.json':
            continue
        try:
            with open(path, encoding='utf-8') as f:
                m = json.load(f)
        except Exception:
            continue
        if isinstance(m, dict):
            out[folder] = m
    return out


def derived():
    items = manifests()
    meals = []
    for iid in sorted(items):
        m = items[iid]
        cf = m.get('category_fields') or {}
        method, nxt = cf.get('processing_method'), cf.get('next_item_id')
        if iid in HAND_WRITTEN or m.get('category') != 'ingredients' or method not in METHOD_APPLIANCES or not nxt or nxt not in items:
            continue
        meals.append({'id': 'meal_' + nxt.replace('food_', '').replace('ingredient_', ''), 'name': items[nxt]['name'], 'group': GROUP[method],
                      'result': {'item_id': nxt, 'quantity': 1}, 'ingredients': [{'item_id': iid, 'quantity': 1}],
                      'appliances': METHOD_APPLIANCES[method]})
    return meals


# ------------------------------------------------------------------ juices, jams, nut butters: they FILL a jar or bottle (the container is kept, with what is in it)

# fruit -> (fruit item, fruits for a 1 L juice)
JUICE = {'apple': ('food_apple', 4), 'orange': ('food_orange', 5), 'lemon': ('food_lemon', 6), 'pear': ('food_pear', 4), 'peach': ('food_peach', 4), 'cherry': ('food_cherry', 10),
         'plum': ('food_plum', 6), 'apricot': ('food_apricot', 8), 'grape': ('food_grapes', 4), 'watermelon': ('food_watermelon', 1), 'strawberry': ('food_strawberry', 8),
         'tomato': ('food_tomato', 5)}
# fruit -> (fruit item, fruits for the small jar, for the large one)
JAM = {'blueberry': ('food_blueberry', 6, 15), 'elderberry': ('food_elderberry', 6, 15), 'haskap': ('food_haskap', 6, 15), 'huckleberry': ('food_huckleberry', 6, 15),
       'raspberry': ('food_raspberry', 6, 15), 'strawberry': ('food_strawberry', 6, 15), 'pear': ('food_pear', 3, 8), 'peach': ('food_peach', 3, 8), 'cherry': ('food_cherry', 6, 15),
       'plum': ('food_plum', 4, 10), 'apricot': ('food_apricot', 5, 12), 'fig': ('food_fig', 4, 10), 'grape': ('food_grapes', 3, 8)}
BOTTLES = (('kitchen_juice_bottle_1l', '', 1), ('kitchen_juice_bottle_2l', ', Large Bottle', 2))
JAM_JARS = (('kitchen_jar_jam_350ml', '', 0), ('kitchen_jar_jam_900ml', ', Large Jar', 1))
# nut -> (nut item, the jar names)
NUT_BUTTER = {'peanut': 'food_peanuts', 'walnut': 'food_walnut', 'pecan': 'food_pecan', 'hazelnut': 'food_hazelnut'}


def canning():
    meals = []
    for fruit, (item, n) in JUICE.items():
        for bottle, suffix, k in BOTTLES:
            meals.append({'id': 'meal_juice_%s_%dl' % (fruit, k), 'name': '%s Juice%s' % (fruit.capitalize(), suffix), 'group': 'Juicing',
                          'result': {'container': bottle, 'liquid': 'liquid_juice_' + fruit},
                          'ingredients': [{'item_id': item, 'quantity': n * k}, {'item_id': '#sugar', 'quantity': k}],
                          'appliances': [{'tools': ['#appliance_juicer']}]})
    for bottle, suffix, k in BOTTLES:   # apple cider: pressed apples, no sugar
        meals.append({'id': 'meal_cider_apple_%dl' % k, 'name': 'Press Apple Cider%s' % suffix, 'group': 'Juicing',
                      'result': {'container': bottle, 'liquid': 'liquid_apple_cider'},
                      'ingredients': [{'item_id': 'food_apple', 'quantity': 6 * k}], 'appliances': [{'tools': ['#appliance_juicer']}]})
    # cream skimmed from milk, maple syrup boiled down from sap (liquid lines are uses of 0.05 L)
    meals.append({'id': 'meal_skim_cream', 'name': 'Skim Cream', 'group': 'Dairy', 'result': {'container': 'kitchen_cream_bottle_500ml', 'liquid': 'liquid_cream'},
                  'ingredients': [{'item_id': 'liquid_milk', 'quantity': 20}], 'appliances': [{'tools': ['#appliance_blender']}]})
    meals.append({'id': 'meal_boil_maple_syrup', 'name': 'Boil Maple Syrup', 'group': 'Preserving', 'result': {'container': 'kitchen_syrup_bottle_500ml', 'liquid': 'liquid_maple_syrup'},
                  'ingredients': [{'item_id': 'liquid_maple_sap', 'quantity': 80}], 'appliances': [{'tools': ['#appliance_stovetop']}]})
    for fruit, (item, small, large) in JAM.items():
        for jar, suffix, k in JAM_JARS:
            meals.append({'id': 'meal_jam_%s_%s' % (fruit, 'large' if k else 'small'), 'name': '%s Jam%s' % (fruit.capitalize(), suffix), 'group': 'Jams',
                          'result': {'container': jar, 'liquid': 'liquid_jam_' + fruit},
                          'ingredients': [{'item_id': item, 'quantity': large if k else small}, {'item_id': '#sugar', 'quantity': 6 if k else 3},
                                          {'item_id': 'ingredient_gelatin', 'quantity': 2 if k else 1}],
                          'appliances': [{'tools': ['#appliance_stovetop']}]})
    for nut, item in NUT_BUTTER.items():
        for g, suffix, k in (('450g', '', 0), ('900g', ', Large Jar', 1)):
            meals.append({'id': 'meal_%s_butter_%s' % (nut, 'large' if k else 'small'), 'name': '%s Butter%s' % (nut.capitalize(), suffix), 'group': 'Nut Butters',
                          'result': {'container': 'kitchen_jar_%s_butter_%s' % (nut, g), 'liquid': 'liquid_%s_butter' % nut},
                          'ingredients': [{'item_id': item, 'quantity': 9 if k else 4}, {'item_id': 'ingredient_salt', 'quantity': 2 if k else 1}],
                          'appliances': [{'tools': ['#appliance_blender']}]})
    return meals


# grain -> (small sack, name). The grain is milled at the grain mill into a sack (3 grain) or a bulk sack (15 grain: the sack's id + "_5kg").
MILL = [('ingredient_wheat', 'ingredient_flour', 'Flour'), ('ingredient_corn', 'ingredient_corn_flour', 'Corn Flour'), ('ingredient_oats', 'ingredient_oat_flour', 'Oat Flour'),
        ('ingredient_barley', 'ingredient_barley_flour', 'Barley Flour'), ('ingredient_soybeans', 'ingredient_soy_flour', 'Soy Flour'), ('ingredient_flax', 'ingredient_flax_meal', 'Flax Meal'),
        ('ingredient_oats', 'ingredient_rolled_oats', 'Rolled Oats'), ('ingredient_corn', 'ingredient_cornmeal', 'Cornmeal'), ('ingredient_corn', 'ingredient_grits', 'Grits'),
        ('ingredient_barley', 'ingredient_pearl_barley', 'Pearl Barley'), ('ingredient_wheat', 'ingredient_cracked_wheat', 'Cracked Wheat')]


def milling():
    meals = []
    for grain, sack, name in MILL:
        for suffix, rid, label, n in (('', sack, '', 3), ('_5kg', sack + '_5kg', ', Bulk Sack', 15)):
            meals.append({'id': 'meal_mill_%s%s' % (sack.replace('ingredient_', ''), suffix), 'name': 'Mill %s%s' % (name, label), 'group': 'Milling',
                          'result': {'item_id': rid, 'quantity': 1}, 'ingredients': [{'item_id': grain, 'quantity': n}], 'appliances': [{'tools': ['#appliance_grain_mill']}]})
    return meals


# ------------------------------------------------------------------ oils: pressed from seeds at the oil press, and the vegetable oil BLEND

# oil -> (seed item, seeds for the 750 mL bottle, for the 2 L bottle)
PRESS = {'sunflower': ('ingredient_sunflower', 4, 10), 'soybean': ('ingredient_soybeans', 6, 16), 'corn': ('ingredient_corn', 7, 18),
         'cottonseed': ('ingredient_cotton', 6, 16), 'peanut': ('food_peanuts', 4, 10), 'flax': ('ingredient_flax', 5, 13), 'canola': ('ingredient_canola', 5, 13)}
OIL_BOTTLES = (('750ml', '', 0), ('2l', ', Large Bottle', 1))
# What a "vegetable oil" blend is made of. There is no standard formula: a label names the oils in it (soybean, canola, sunflower, corn, cottonseed ...). This game's blend is 40% soybean oil (the usual main oil), 30% canola oil, 15% corn, 10% sunflower and 5% cottonseed. The shares add up to 1.
BLEND = (('soybean', 0.40), ('canola', 0.30), ('corn', 0.15), ('sunflower', 0.10), ('cottonseed', 0.05))


def oils():
    meals = []
    names = {'sunflower': 'Sunflower Oil', 'soybean': 'Soybean Oil', 'corn': 'Corn Oil', 'cottonseed': 'Cottonseed Oil', 'peanut': 'Peanut Oil', 'flax': 'Flaxseed Oil', 'canola': 'Canola Oil'}
    for oil, (seed, small, large) in PRESS.items():
        for size, suffix, k in OIL_BOTTLES:
            meals.append({'id': 'meal_press_%s_%s' % (oil, size), 'name': 'Press %s%s' % (names[oil], suffix), 'group': 'Oil Pressing',
                          'result': {'container': 'kitchen_oil_bottle_%s_%s' % (oil, size), 'liquid': 'liquid_%s_oil' % oil},
                          'ingredients': [{'item_id': seed, 'quantity': large if k else small}], 'appliances': [{'tools': ['#appliance_oil_press']}]})
    for size, suffix, k in OIL_BOTTLES:
        meals.append({'id': 'meal_blend_vegetable_oil_%s' % size, 'name': 'Blend Vegetable Oil%s' % suffix, 'group': 'Oil Pressing',
                      'result': {'container': 'kitchen_oil_bottle_vegetable_%s' % size, 'liquid': 'liquid_vegetable_oil'},
                      'ingredients': [], 'liquids': [{'liquid': 'liquid_%s_oil' % o, 'share': share} for o, share in BLEND], 'appliances': []})
    return meals


def write(name, meals):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline=chr(10)) as f:
        json.dump({'meals': meals}, f, indent=2, ensure_ascii=False)
        f.write(chr(10))
    print('wrote', name, len(meals), 'meal(s)')


if __name__ == '__main__':
    write('baking.json', BAKING)
    write('milling.json', milling())
    write('cooking.json', derived())
    write('canning.json', canning())
    write('oils.json', oils())
