"""
The DISHES (breakfasts, mains, sides, salads, desserts): one table that feeds both the items (tools/make_dishes_more.py: manifests and the icons cut from Gemini sheets) and the meals
(tools/make_meals.py). Every ingredient is an item the game already has. A dish with bowl=True is served in a Soup Bowl (kitchen_bowl is an ingredient, and the food leaves the bowl when eaten).

    id, name, description, group (the Meals List heading), appliance tag (None = put together on the counter), servings (the result quantity), ingredients, bowl,
    kg, price, hunger, stamina, happiness
"""
S, O = '#appliance_stovetop', '#appliance_oven'


def D(id, name, desc, group, appliance, servings, ingredients, bowl=False, kg=0.4, price=8, hunger=26, stamina=20, happy=10):
    return dict(id=id, name=name, desc=desc, group=group, appliance=appliance, servings=servings, ingredients=ingredients, bowl=bowl, kg=kg, price=price, hunger=hunger, stamina=stamina, happy=happy)


DISHES = [
    # breakfast
    D('food_oatmeal', 'Oatmeal', 'A warm bowl of rolled oats with a spoon of sugar.', 'Breakfast', S, 2,
      [('ingredient_rolled_oats', 2), ('#sugar', 1), ('ingredient_salt', 1)], bowl=True, kg=0.4, price=4, hunger=18, stamina=18, happy=6),
    D('food_grits', 'Grits', 'A bowl of creamy corn grits with butter.', 'Breakfast', S, 2,
      [('ingredient_grits', 2), ('ingredient_butter', 1), ('ingredient_salt', 1)], bowl=True, kg=0.4, price=4, hunger=18, stamina=18, happy=6),
    D('food_pancakes', 'Pancakes', 'A short stack of golden pancakes with butter.', 'Breakfast', S, 4,
      [('#flour', 2), ('ingredient_egg', 1), ('#sugar', 1), ('ingredient_baking_powder', 1), ('ingredient_butter', 1)], kg=0.3, price=5, hunger=20, stamina=18, happy=11),
    D('food_scrambled_eggs', 'Scrambled Eggs', 'Soft scrambled eggs.', 'Breakfast', S, 2,
      [('ingredient_egg', 3), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.25, price=4, hunger=16, stamina=16, happy=7),
    D('food_bacon_and_eggs', 'Bacon and Eggs', 'Fried eggs with crisp strips of bacon.', 'Breakfast', S, 2,
      [('ingredient_egg', 2), ('ingredient_bacon', 2), ('ingredient_butter', 1)], kg=0.3, price=7, hunger=26, stamina=22, happy=12),
    D('food_french_toast', 'French Toast', 'Slices of bread soaked in egg and fried golden.', 'Breakfast', S, 2,
      [('food_bread', 2), ('ingredient_egg', 1), ('#sugar', 1), ('ingredient_butter', 1)], kg=0.3, price=5, hunger=20, stamina=18, happy=11),
    # mains
    D('food_beef_stew', 'Beef Stew', 'A thick stew of beef, potato, carrot and onion.', 'Mains', S, 2,
      [('ingredient_beef', 1), ('food_potato', 2), ('food_carrot', 1), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=11, hunger=34, stamina=28, happy=12),
    D('food_chicken_stew', 'Chicken Stew', 'A creamy stew of chicken, potato, peas and carrot.', 'Mains', S, 2,
      [('ingredient_chicken', 1), ('food_potato', 1), ('food_peas', 1), ('food_carrot', 1), ('ingredient_butter', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=10, hunger=32, stamina=26, happy=12),
    D('food_lamb_stew', 'Lamb Stew', 'A rich stew of lamb, potato, carrot and onion.', 'Mains', S, 2,
      [('ingredient_lamb_chop', 1), ('food_potato', 2), ('food_carrot', 1), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=12, hunger=34, stamina=28, happy=12),
    D('food_goat_stew', 'Goat Stew', 'A spiced stew of goat meat, potato, carrot and tomato.', 'Mains', S, 2,
      [('ingredient_goat_meat', 1), ('food_potato', 1), ('food_carrot', 1), ('food_tomato', 1), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=11, hunger=33, stamina=27, happy=12),
    D('food_pork_stew', 'Pork Stew', 'A hearty stew of pork, potato, green beans and onion.', 'Mains', S, 2,
      [('ingredient_pork', 1), ('food_potato', 2), ('food_green_beans', 1), ('food_onion', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=10, hunger=32, stamina=26, happy=11),
    D('food_sausage_stew', 'Sausage Stew', 'Sliced sausage stewed with potato, pepper and tomato.', 'Mains', S, 2,
      [('ingredient_sausage', 1), ('food_potato', 1), ('food_pepper', 1), ('food_tomato', 1), ('food_onion', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=10, hunger=32, stamina=26, happy=12),
    D('food_fish_stew', 'Fish Stew', 'A tomato broth stew of catfish, potato and onion.', 'Mains', S, 2,
      [('ingredient_fillet_catfish', 1), ('food_potato', 1), ('food_tomato', 1), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=11, hunger=30, stamina=24, happy=11),
    D('food_vegetable_stew', 'Vegetable Stew', 'A thick stew of potato, carrot, peas and tomato.', 'Mains', S, 2,
      [('food_potato', 2), ('food_carrot', 1), ('food_peas', 1), ('food_tomato', 1), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], bowl=True, kg=0.55, price=8, hunger=26, stamina=22, happy=9),
    D('food_meatloaf', 'Meatloaf', 'A baked loaf of ground beef with onion, egg and bread.', 'Mains', O, 4,
      [('ingredient_ground_beef', 2), ('food_bread', 1), ('ingredient_egg', 1), ('food_onion', 1), ('ingredient_salt', 1)], kg=0.45, price=10, hunger=34, stamina=28, happy=11),
    D('food_shepherds_pie', "Shepherd's Pie", 'Ground beef and peas under a golden crust of mashed potato.', 'Mains', O, 4,
      [('ingredient_ground_beef', 2), ('food_potato', 3), ('food_peas', 1), ('food_carrot', 1), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.5, price=11, hunger=36, stamina=30, happy=13),
    D('food_roast_chicken', 'Roast Chicken', 'A whole chicken roasted with herbs until golden.', 'Mains', O, 4,
      [('ingredient_chicken', 2), ('ingredient_herbs', 1), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.5, price=12, hunger=38, stamina=30, happy=13),
    D('food_pot_roast', 'Pot Roast', 'Slow roasted beef with potato, carrot and onion.', 'Mains', O, 4,
      [('ingredient_beef', 2), ('food_potato', 2), ('food_carrot', 2), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], kg=0.55, price=13, hunger=40, stamina=32, happy=14),
    # sides and salads
    D('food_mashed_potatoes', 'Mashed Potatoes', 'Creamy mashed potatoes with butter.', 'Sides', S, 4,
      [('food_potato', 3), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.3, price=4, hunger=18, stamina=16, happy=8),
    D('food_baked_potato', 'Baked Potato', 'A fluffy baked potato with butter.', 'Sides', O, 4,
      [('food_potato', 4), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.3, price=4, hunger=18, stamina=16, happy=7),
    D('food_roasted_vegetables', 'Roasted Vegetables', 'Carrot, zucchini, onion and pepper roasted until browned.', 'Sides', O, 4,
      [('food_carrot', 1), ('food_zucchini', 1), ('food_onion', 1), ('food_pepper', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], kg=0.3, price=5, hunger=14, stamina=14, happy=7),
    D('food_garden_salad', 'Garden Salad', 'Crisp lettuce with tomato, cucumber, carrot and radish.', 'Salads', None, 2,
      [('food_lettuce', 1), ('food_tomato', 1), ('food_cucumber', 1), ('food_carrot', 1), ('food_radish', 1)], bowl=True, kg=0.3, price=5, hunger=12, stamina=12, happy=7),
    D('food_coleslaw', 'Coleslaw', 'Shredded cabbage and carrot in a creamy dressing.', 'Salads', None, 2,
      [('food_cabbage', 1), ('food_carrot', 1), ('#sugar', 1), ('ingredient_salt', 1)], bowl=True, kg=0.25, price=4, hunger=10, stamina=10, happy=6),
    D('food_spinach_salad', 'Spinach Salad', 'Fresh spinach with sliced egg, bacon and onion.', 'Salads', None, 2,
      [('food_spinach', 1), ('ingredient_egg', 1), ('ingredient_bacon', 1), ('food_onion', 1)], bowl=True, kg=0.25, price=6, hunger=14, stamina=14, happy=8),
    # pasta and breads
    D('food_spaghetti_meat_sauce', 'Spaghetti with Meat Sauce', 'Spaghetti in a tomato sauce with browned ground beef.', 'Pasta', S, 2,
      [('ingredient_pasta', 2), ('ingredient_pasta_sauce', 1), ('ingredient_ground_beef', 1)], kg=0.45, price=10, hunger=36, stamina=28, happy=12),
    D('food_spaghetti_alfredo', 'Spaghetti Alfredo', 'Spaghetti in a creamy cheese Alfredo sauce.', 'Pasta', S, 2,
      [('ingredient_pasta', 2), ('ingredient_alfredo_sauce', 1)], kg=0.4, price=9, hunger=32, stamina=24, happy=13),
    D('food_cacio_e_pepe', 'Cacio e Pepe', 'Spaghetti tossed in melted cheese and cracked black pepper.', 'Pasta', S, 2,
      [('ingredient_pasta', 2), ('food_cheese', 2), ('ingredient_butter', 2), ('ingredient_pepper_ground', 2), ('ingredient_salt', 1)], kg=0.35, price=8, hunger=30, stamina=22, happy=12),
    D('food_breadsticks', 'Breadsticks', 'Soft baked breadsticks brushed with butter and salt.', 'Sides', O, 4,
      [('#flour', 2), ('ingredient_yeast', 1), ('ingredient_salt', 1), ('ingredient_butter', 1)], kg=0.08, price=2, hunger=8, stamina=8, happy=8),
    D('food_garlic_bread', 'Garlic Bread', 'Sliced bread baked with garlic butter and herbs.', 'Sides', O, 4,
      [('food_bread', 2), ('ingredient_butter', 1), ('food_garlic', 1), ('ingredient_herbs', 1)], kg=0.1, price=3, hunger=10, stamina=10, happy=10),
    # desserts
    D('food_apple_pie', 'Apple Pie', 'A golden pie of cinnamon apples under a flaky crust.', 'Desserts', O, 4,
      [('#flour', 2), ('ingredient_butter', 1), ('food_apple', 3), ('#sugar', 1), ('ingredient_salt', 1)], kg=0.4, price=9, hunger=22, stamina=20, happy=16),
    D('food_cherry_pie', 'Cherry Pie', 'A pie of tart red cherries under a lattice crust.', 'Desserts', O, 4,
      [('#flour', 2), ('ingredient_butter', 1), ('food_cherry', 3), ('#sugar', 1), ('ingredient_salt', 1)], kg=0.4, price=9, hunger=22, stamina=20, happy=16),
    D('food_blueberry_pie', 'Blueberry Pie', 'A deep blue pie of baked blueberries.', 'Desserts', O, 4,
      [('#flour', 2), ('ingredient_butter', 1), ('food_blueberry', 3), ('#sugar', 1), ('ingredient_salt', 1)], kg=0.4, price=9, hunger=22, stamina=20, happy=16),
    D('food_pumpkin_pie', 'Pumpkin Pie', 'A smooth spiced pumpkin pie.', 'Desserts', O, 4,
      [('#flour', 2), ('ingredient_butter', 1), ('food_pumpkin', 1), ('ingredient_egg', 1), ('#sugar', 1), ('ingredient_salt', 1)], kg=0.4, price=9, hunger=22, stamina=20, happy=16),
    D('food_cake', 'Yellow Cake', 'A tall yellow layer cake with frosting.', 'Desserts', O, 6,
      [('#flour', 3), ('#sugar', 2), ('ingredient_egg', 2), ('ingredient_butter', 1), ('ingredient_baking_powder', 1), ('ingredient_salt', 1)], kg=0.4, price=10, hunger=20, stamina=20, happy=18),
    D('food_sugar_cookies', 'Sugar Cookies', 'A batch of round sugar cookies.', 'Desserts', O, 8,
      [('#flour', 2), ('#sugar', 1), ('ingredient_butter', 1), ('ingredient_egg', 1), ('ingredient_baking_powder', 1)], kg=0.08, price=2, hunger=6, stamina=8, happy=9),
]

import dish_extra  # noqa: E402  (the eggs, sandwiches, roasts, breakfasts, sides, salads, chili and cobblers)
DISHES += dish_extra.build(D, S, O)

# the icon sheets, in reading order (tools/extract_icon_sheet.py cuts them into assets/_scratch/dishes/out1 ... out4; the extra stews are painted by tools/make_stew_icons.py into out5)
SHEETS = [
    ['food_oatmeal', 'food_grits', 'food_pancakes', 'food_scrambled_eggs', 'food_bacon_and_eggs', 'food_french_toast'],
    ['food_beef_stew', 'food_chicken_stew', 'food_meatloaf', 'food_shepherds_pie', 'food_roast_chicken', 'food_pot_roast'],
    ['food_mashed_potatoes', 'food_baked_potato', 'food_roasted_vegetables', 'food_garden_salad', 'food_coleslaw', 'food_spinach_salad'],
    ['food_apple_pie', 'food_cherry_pie', 'food_blueberry_pie', 'food_pumpkin_pie', 'food_cake', 'food_sugar_cookies'],
]
