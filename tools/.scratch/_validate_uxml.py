import xml.etree.ElementTree as ET
try:
    tree = ET.parse(r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\HudUI.uxml")
    print("XML is valid")
    print("root:", tree.getroot().tag)
    print("children:", len(list(tree.getroot())))
except ET.ParseError as e:
    print("PARSE ERROR:", e)
