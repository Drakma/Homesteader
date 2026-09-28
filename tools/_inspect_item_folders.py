import os

root = r"C:\Users\casey\Desktop\Homesteader"
app_item = os.path.join(root, "assets", "appliances", "app_dryer")
print("Files in app_dryer:", os.listdir(app_item))

tools_item = os.path.join(root, "assets", "tools", "tool_axe")
if os.path.exists(tools_item):
    print("Files in tool_axe:", os.listdir(tools_item))

food_item = os.path.join(root, "assets", "food", "food_apple")
if os.path.exists(food_item):
    print("Files in food_apple:", os.listdir(food_item))
