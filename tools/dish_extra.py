"""
The EXTRA DISHES (eggs, sandwiches, fried and roasted mains, breakfasts, sides, salads, soups, chili, cobblers, custard ...): the table tools/dish_data.py adds to its DISHES (see the bottom of that file).
Same shape as dish_data.D: id, name, description, group, appliance, servings, ingredients, bowl, kg, price, hunger, stamina, happy. `liquid_*` lines are USES of a liquid (one use is 0.05 L poured out of a filled bottle).
The icons are painted by tools/make_more_dish_icons.py (assets/_scratch/dishes/out5).
"""


def build(D, S, O):
    L = []
    a = L.append
    # eggs
    a(D('food_omelet', 'Omelet', 'A folded omelet of three eggs with melted cheese.', 'Eggs', S, 2,
        [('ingredient_egg', 3), ('food_cheese', 1), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.25, price=6, hunger=20, stamina=18, happy=8))
    a(D('food_quiche', 'Quiche', 'A baked pie of eggs, cheese and bacon in a flaky crust.', 'Eggs', O, 4,
        [('ingredient_egg', 4), ('food_cheese', 2), ('food_bacon_cooked', 2), ('#flour', 2), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.3, price=6, hunger=22, stamina=20, happy=10))
    a(D('food_deviled_eggs', 'Deviled Eggs', 'Boiled egg halves filled with a seasoned yolk.', 'Eggs', S, 4,
        [('ingredient_egg', 4), ('ingredient_pepper_ground', 1), ('ingredient_salt', 1), ('ingredient_herbs', 1)], kg=0.1, price=3, hunger=8, stamina=8, happy=7))
    a(D('food_egg_salad', 'Egg Salad', 'Chopped boiled eggs with onion, salt and pepper.', 'Salads', S, 2,
        [('ingredient_egg', 4), ('food_onion', 1), ('ingredient_salt', 1), ('ingredient_pepper_ground', 1)], bowl=True, kg=0.3, price=5, hunger=16, stamina=14, happy=6))
    # sandwiches
    a(D('food_blt', 'BLT Sandwich', 'Crisp bacon, lettuce and tomato on bread.', 'Sandwiches', None, 2,
        [('food_bread', 4), ('food_bacon_cooked', 4), ('food_lettuce', 1), ('food_tomato', 1)], kg=0.25, price=6, hunger=22, stamina=18, happy=9))
    a(D('food_grilled_cheese', 'Grilled Cheese', 'Bread and melted cheese, toasted golden in butter.', 'Sandwiches', S, 2,
        [('food_bread', 4), ('food_cheese', 2), ('ingredient_butter', 1)], kg=0.2, price=4, hunger=18, stamina=16, happy=9))
    a(D('food_ham_sandwich', 'Ham Sandwich', 'Sliced ham, cheese and lettuce on bread.', 'Sandwiches', None, 2,
        [('food_bread', 4), ('ingredient_ham', 1), ('food_cheese', 1), ('food_lettuce', 1)], kg=0.25, price=5, hunger=20, stamina=16, happy=8))
    a(D('food_fish_sandwich', 'Fish Sandwich', 'A crisp fried fish fillet with lettuce on a bun.', 'Sandwiches', None, 2,
        [('food_burger_bun', 2), ('food_catfish_deepfried', 2), ('food_lettuce', 1)], kg=0.3, price=7, hunger=24, stamina=20, happy=9))
    # mains
    a(D('food_fried_chicken', 'Fried Chicken', 'Chicken pieces breaded and deep fried until crisp.', 'Mains', S, 2,
        [('ingredient_chicken', 2), ('ingredient_bread_crumbs', 2), ('#cooking_oil', 6), ('ingredient_egg', 1), ('ingredient_salt', 1), ('ingredient_pepper_ground', 1)], kg=0.4, price=10, hunger=36, stamina=28, happy=13))
    a(D('food_pork_chops_apples', 'Pork Chops with Apples', 'Pan-seared pork chops with buttered apple slices.', 'Mains', S, 2,
        [('ingredient_pork_chop', 2), ('food_apple', 2), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.4, price=10, hunger=34, stamina=26, happy=11))
    a(D('food_lamb_roast', 'Roast Lamb', 'Lamb roasted with potato, carrot and herbs.', 'Mains', O, 2,
        [('ingredient_lamb_chop', 2), ('food_potato', 2), ('food_carrot', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], kg=0.45, price=12, hunger=38, stamina=30, happy=12))
    a(D('food_goat_roast', 'Roast Goat', 'Goat meat roasted with potato, onion and herbs.', 'Mains', O, 2,
        [('ingredient_goat_meat', 2), ('food_potato', 2), ('food_onion', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], kg=0.45, price=11, hunger=36, stamina=28, happy=11))
    a(D('food_ham_and_beans', 'Ham and Beans', 'Soybeans slow cooked with ham and onion.', 'Mains', S, 2,
        [('ingredient_ham', 1), ('ingredient_soybeans', 2), ('food_onion', 1), ('ingredient_salt', 1)], bowl=True, kg=0.5, price=8, hunger=30, stamina=26, happy=9))
    a(D('food_baked_salmon', 'Baked Salmon', 'A salmon fillet baked with butter, lemon and herbs.', 'Mains', O, 2,
        [('ingredient_fillet_salmon', 2), ('ingredient_butter', 1), ('food_lemon', 1), ('ingredient_herbs', 1)], kg=0.3, price=11, hunger=30, stamina=26, happy=12))
    # breakfast
    a(D('food_biscuits', 'Biscuits', 'Fluffy buttermilk-style biscuits.', 'Breakfast', O, 4,
        [('#flour', 2), ('ingredient_butter', 2), ('ingredient_baking_powder', 1), ('liquid_milk', 4), ('ingredient_salt', 1)], kg=0.08, price=2, hunger=10, stamina=10, happy=8))
    a(D('food_waffles', 'Waffles', 'Golden waffles with butter.', 'Breakfast', S, 4,
        [('#flour', 2), ('ingredient_egg', 1), ('ingredient_butter', 1), ('ingredient_baking_powder', 1), ('liquid_milk', 4), ('#sugar', 1)], kg=0.12, price=3, hunger=14, stamina=14, happy=11))
    a(D('food_hash_browns', 'Hash Browns', 'Shredded potato fried crisp with onion.', 'Breakfast', S, 2,
        [('food_potato', 3), ('ingredient_butter', 1), ('food_onion', 1), ('ingredient_salt', 1)], kg=0.25, price=4, hunger=16, stamina=16, happy=8))
    a(D('food_apple_porridge', 'Apple Oat Porridge', 'Creamy rolled oats cooked in milk with apple and sugar.', 'Breakfast', S, 2,
        [('ingredient_rolled_oats', 2), ('liquid_milk', 6), ('food_apple', 1), ('#sugar', 1)], bowl=True, kg=0.4, price=5, hunger=20, stamina=20, happy=9))
    a(D('food_sausage_and_eggs', 'Sausage and Eggs', 'Browned sausage links with fried eggs.', 'Breakfast', S, 2,
        [('ingredient_sausage', 2), ('ingredient_egg', 2), ('ingredient_butter', 1)], kg=0.3, price=7, hunger=26, stamina=22, happy=10))
    a(D('food_biscuits_gravy', 'Biscuits and Gravy', 'Split biscuits under a peppery sausage gravy.', 'Breakfast', S, 2,
        [('food_biscuits', 2), ('ingredient_sausage', 1), ('#flour', 1), ('liquid_milk', 6), ('ingredient_pepper_ground', 1)], kg=0.35, price=6, hunger=26, stamina=22, happy=11))
    # sides
    a(D('food_french_fries', 'French Fries', 'Potato fries deep fried and salted.', 'Sides', S, 2,
        [('food_potato', 3), ('#cooking_oil', 6), ('ingredient_salt', 1)], kg=0.25, price=4, hunger=16, stamina=14, happy=11))
    a(D('food_corn_on_the_cob', 'Corn on the Cob', 'Corn boiled on the cob with butter and salt.', 'Sides', S, 2,
        [('ingredient_corn', 2), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.25, price=3, hunger=12, stamina=12, happy=8))
    a(D('food_green_bean_casserole', 'Green Bean Casserole', 'Green beans baked in a cheese sauce under a crumb crust.', 'Sides', O, 4,
        [('food_green_beans', 3), ('food_cheese', 1), ('ingredient_bread_crumbs', 1), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.3, price=4, hunger=12, stamina=12, happy=7))
    a(D('food_roasted_beets', 'Roasted Beets', 'Beets roasted with butter and herbs.', 'Sides', O, 4,
        [('food_beet', 3), ('ingredient_butter', 1), ('ingredient_herbs', 1), ('ingredient_salt', 1)], kg=0.25, price=3, hunger=10, stamina=10, happy=5))
    a(D('food_broccoli_and_cheese', 'Broccoli and Cheese', 'Steamed broccoli under melted cheese.', 'Sides', S, 2,
        [('food_broccoli', 2), ('food_cheese', 1), ('ingredient_butter', 1)], kg=0.25, price=4, hunger=12, stamina=12, happy=6))
    a(D('food_cracked_wheat_pilaf', 'Cracked Wheat Pilaf', 'Cracked wheat simmered with onion and butter.', 'Sides', S, 2,
        [('ingredient_cracked_wheat', 2), ('ingredient_butter', 1), ('food_onion', 1), ('ingredient_salt', 1)], kg=0.3, price=4, hunger=14, stamina=14, happy=6))
    # soups, chili
    a(D('food_broccoli_cheese_soup', 'Broccoli Cheese Soup', 'A thick, creamy soup of broccoli and cheddar.', 'Soups', S, 2,
        [('food_broccoli', 2), ('food_cheese', 2), ('ingredient_butter', 1), ('#flour', 1), ('liquid_milk', 6), ('ingredient_salt', 1)], bowl=True, kg=0.5, price=8, hunger=26, stamina=22, happy=10))
    a(D('food_borscht', 'Borscht', 'A deep red soup of beets, cabbage and potato.', 'Soups', S, 2,
        [('food_beet', 3), ('food_potato', 1), ('food_carrot', 1), ('food_onion', 1), ('food_cabbage', 1), ('ingredient_salt', 1)], bowl=True, kg=0.5, price=7, hunger=24, stamina=22, happy=7))
    a(D('food_beef_chili', 'Beef Chili', 'Ground beef, beans and peppers simmered in tomato.', 'Soups', S, 2,
        [('ingredient_ground_beef', 2), ('food_tomato', 3), ('food_pepper', 1), ('food_onion', 1), ('ingredient_soybeans', 2), ('ingredient_salt', 1), ('ingredient_pepper_ground', 1)], bowl=True, kg=0.55, price=10, hunger=34, stamina=28, happy=12))
    a(D('food_veggie_chili', 'Vegetarian Chili', 'Beans and peppers simmered in a spicy tomato broth.', 'Soups', S, 2,
        [('food_tomato', 3), ('food_pepper', 2), ('food_onion', 1), ('ingredient_soybeans', 3), ('ingredient_salt', 1), ('ingredient_pepper_ground', 1)], bowl=True, kg=0.5, price=7, hunger=26, stamina=24, happy=8))
    # salads
    a(D('food_potato_salad', 'Potato Salad', 'Boiled potato and egg with onion in a creamy dressing.', 'Salads', S, 2,
        [('food_potato', 3), ('ingredient_egg', 2), ('food_onion', 1), ('ingredient_salt', 1), ('ingredient_pepper_ground', 1)], bowl=True, kg=0.35, price=5, hunger=18, stamina=16, happy=7))
    a(D('food_cucumber_salad', 'Cucumber Salad', 'Sliced cucumber and onion with salt.', 'Salads', None, 2,
        [('food_cucumber', 2), ('food_onion', 1), ('ingredient_salt', 1)], bowl=True, kg=0.25, price=3, hunger=8, stamina=8, happy=5))
    a(D('food_caesar_salad', 'Caesar Salad', 'Crisp lettuce with cheese, crumb croutons and pepper.', 'Salads', None, 2,
        [('food_lettuce', 2), ('food_cheese', 1), ('ingredient_bread_crumbs', 1), ('ingredient_pepper_ground', 1)], bowl=True, kg=0.25, price=5, hunger=10, stamina=10, happy=7))
    a(D('food_fruit_salad', 'Fruit Salad', 'Melon, apple, orange, strawberry and grape.', 'Salads', None, 2,
        [('food_cantaloupe', 1), ('food_apple', 1), ('food_orange', 1), ('food_strawberry', 1), ('food_grapes', 1)], bowl=True, kg=0.35, price=5, hunger=10, stamina=12, happy=10))
    # desserts
    a(D('food_peach_cobbler', 'Peach Cobbler', 'Baked peaches under a golden biscuit crust.', 'Desserts', O, 4,
        [('food_peach', 3), ('#flour', 2), ('#sugar', 2), ('ingredient_butter', 1), ('ingredient_baking_powder', 1)], kg=0.3, price=5, hunger=14, stamina=14, happy=14))
    a(D('food_apple_cobbler', 'Apple Cobbler', 'Cinnamon apples under a golden biscuit crust.', 'Desserts', O, 4,
        [('food_apple', 3), ('#flour', 2), ('#sugar', 2), ('ingredient_butter', 1), ('ingredient_baking_powder', 1)], kg=0.3, price=5, hunger=14, stamina=14, happy=14))
    a(D('food_custard', 'Custard', 'A smooth, sweet egg and milk custard.', 'Desserts', S, 2,
        [('liquid_milk', 12), ('ingredient_egg', 2), ('#sugar', 2)], bowl=True, kg=0.3, price=4, hunger=10, stamina=10, happy=12))
    a(D('food_strawberry_gelatin', 'Strawberry Gelatin', 'A wobbly strawberry gelatin dessert, set in the refrigerator.', 'Desserts', '#appliance_fridge', 2,
        [('ingredient_gelatin', 1), ('#sugar', 1), ('food_strawberry', 2)], bowl=True, kg=0.25, price=3, hunger=6, stamina=8, happy=10))
    a(D('food_ice_cream', 'Ice Cream', 'Sweet cream ice cream frozen in the freezer.', 'Desserts', '#appliance_freezer', 4,
        [('liquid_cream', 12), ('#sugar', 2), ('ingredient_egg', 1)], bowl=True, kg=0.2, price=4, hunger=8, stamina=10, happy=16))
    a(D('food_brownies', 'Brownies', 'Dense, fudgy chocolate brownies.', 'Desserts', O, 8,
        [('ingredient_cocoa', 3), ('#flour', 2), ('#sugar', 2), ('ingredient_butter', 2), ('ingredient_egg', 2)], kg=0.07, price=2, hunger=7, stamina=10, happy=14))
    a(D('food_chocolate_pudding', 'Chocolate Pudding', 'Rich chocolate pudding thickened on the stove.', 'Desserts', S, 2,
        [('liquid_milk', 12), ('ingredient_cocoa', 2), ('#sugar', 2), ('ingredient_corn_flour', 1)], bowl=True, kg=0.3, price=4, hunger=10, stamina=10, happy=13))
    # the leftovers: flax meal, truffle
    a(D('food_flax_bread', 'Flax Bread', 'A dense seeded loaf baked with flax meal.', 'Baking', O, 4,
        [('#flour', 2), ('ingredient_flax_meal', 1), ('ingredient_yeast', 1), ('ingredient_salt', 1)], kg=0.1, price=3, hunger=10, stamina=12, happy=6))
    a(D('food_truffle_pasta', 'Truffle Pasta', 'Buttered spaghetti shaved with black truffle.', 'Pasta', S, 2,
        [('ingredient_pasta', 2), ('food_truffle', 1), ('ingredient_butter', 1), ('ingredient_salt', 1)], kg=0.35, price=18, hunger=30, stamina=24, happy=16))
    return L
