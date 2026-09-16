import glob, os, csv

true_quarantined_items = [
    # Replaced duplicates
    'icon_axe', 'icon_bread', 'icon_pickaxe', 'icon_seeds', 'icon_shovel',
    'icon_watering_can', 'icon_wheat', 'icon_wood_log', 'animal_meat',
    # Legacy generic items superseded by specific catalog models
    'item_generator', 'item_solar_panel', 'item_wind_turbine', 'tool_chainsaw', 'tool_fishing_rod',
    'hardware_nails', 'wood_logs_stack', 'water_filter', 'water_pipe',
    'internet_cable', 'internet_router', 'internet_satellite_dish', 'tree_sapling'
]

data_dir = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Content\Homesteader\Data"
csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

total_issues = 0
for cf in sorted(csv_files):
    lines = open(cf, "r", encoding="utf-8", errors="ignore").readlines()
    for line_idx, line in enumerate(lines, 1):
        tokens = [t.strip().replace('"', '') for t in line.replace(',', ' ').replace(';', ' ').replace('=', ' ').split()]
        for q in true_quarantined_items:
            if q in tokens:
                print(f"ISSUE in {os.path.basename(cf)} L{line_idx}: quarantined item '{q}' referenced!")
                total_issues += 1

print(f"Verification finished with {total_issues} issues found across CSVs.")
