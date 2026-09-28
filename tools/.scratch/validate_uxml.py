"""Validate UXML with xml.etree.ElementTree."""
import xml.etree.ElementTree as ET

p = r"C:\Users\casey\Desktop\Homesteader\Homesteader\Assets\Resources\HUDTree\HudUI.uxml"
tree = ET.parse(p)
root = tree.getroot()
print("root tag:", root.tag)
print("root attrs:", root.attrib)
print("root children:")
def walk(node, depth=0):
    indent = "  " * depth
    cls = node.attrib.get('class', '?')
    name = node.attrib.get('name', '')
    print(indent + "<" + node.tag.split('}')[-1] + " name=\"" + name + "\" class=\"" + cls + "\">")
    for c in node:
        walk(c, depth + 1)
walk(root)
