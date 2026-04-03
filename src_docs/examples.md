# Examples

## Inspect a .lines file

```python
from vexy_lines import parse

doc = parse("artwork.lines")
print(f"Project: {doc.caption}")
print(f"Created with Vexy Lines {doc.version}")
print(f"Canvas: {doc.props.width_mm:.0f} x {doc.props.height_mm:.0f} mm @ {doc.dpi} dpi")
print(f"Source image: {'yes' if doc.source_image_data else 'no'}")
print(f"Preview image: {'yes' if doc.preview_image_data else 'no'}")
```

## Count layers and fills

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")

groups = 0
layers = 0
fills = 0

def count(nodes):
    global groups, layers, fills
    for node in nodes:
        if isinstance(node, GroupInfo):
            groups += 1
            count(node.children)
        elif isinstance(node, LayerInfo):
            layers += 1
            fills += len(node.fills)

count(doc.groups)
print(f"{groups} groups, {layers} layers, {fills} fills")
```

## Walk all fills (reusable generator)

A generator that yields every `FillNode` in the tree. Useful as a building block for the examples below.

```python
from vexy_lines import parse, GroupInfo, LayerInfo, FillNode

def walk_fills(nodes):
    """Yield every FillNode in the layer tree."""
    for node in nodes:
        if isinstance(node, GroupInfo):
            yield from walk_fills(node.children)
        elif isinstance(node, LayerInfo):
            yield from node.fills

doc = parse("artwork.lines")
for fill in walk_fills(doc.groups):
    p = fill.params
    print(f"{fill.caption}: {p.fill_type}, color={p.color}, "
          f"interval={p.interval}, angle={p.angle}")
```

## Filter fills by type

Find all halftone fills across the project:

```python
from vexy_lines import parse, GroupInfo, LayerInfo

def walk_fills(nodes):
    for node in nodes:
        if isinstance(node, GroupInfo):
            yield from walk_fills(node.children)
        elif isinstance(node, LayerInfo):
            yield from node.fills

doc = parse("artwork.lines")
halftones = [f for f in walk_fills(doc.groups) if f.params.fill_type == "halftone"]

for h in halftones:
    p = h.params
    cell_size = p.raw.get("cell_size", "?")
    morphing = p.raw.get("morphing_mode", "?")
    print(f"{h.caption}: cell_size={cell_size}, morphing_mode={morphing}, "
          f"color={p.color}, interval={p.interval}")
```

## List all fill types and colours

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")

def walk_fills(nodes):
    for node in nodes:
        if isinstance(node, GroupInfo):
            yield from walk_fills(node.children)
        elif isinstance(node, LayerInfo):
            for fill in node.fills:
                yield fill

for fill in walk_fills(doc.groups):
    p = fill.params
    print(f"{fill.caption}: {p.fill_type}, color={p.color}, "
          f"interval={p.interval}, angle={p.angle}")
```

## Extract the source image

```python
from vexy_lines import extract_source_image

path = extract_source_image("artwork.lines", "source.jpg")
print(f"Saved source image to {path}")
```

## Extract the preview image

```python
from vexy_lines import extract_preview_image

path = extract_preview_image("artwork.lines", "preview.png")
print(f"Saved preview to {path}")
```

## Batch extract previews from a directory

```python
from pathlib import Path
from vexy_lines import parse

input_dir = Path("./artwork")
output_dir = Path("./thumbnails")
output_dir.mkdir(exist_ok=True)

for lines_file in sorted(input_dir.glob("*.lines")):
    doc = parse(lines_file)
    if doc.preview_image_data:
        out = output_dir / f"{lines_file.stem}.png"
        out.write_bytes(doc.preview_image_data)
        print(f"{lines_file.name} -> {out.name}")
    else:
        print(f"{lines_file.name}: no preview embedded")
```

## Access raw XML attributes

Every `FillParams` object carries a `raw` dict with all original XML attributes, including algorithm-specific keys that don't have dedicated fields:

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")

for node in doc.groups:
    if isinstance(node, LayerInfo):
        for fill in node.fills:
            # Algorithm-specific attributes live in raw
            vert_disp = fill.params.raw.get("vert_disp", "0")
            enbl_dotted = fill.params.raw.get("enbl_dotted", "0")
            width_mode = fill.params.raw.get("width_mode", "0")
            print(f"{fill.caption}: vert_disp={vert_disp}, "
                  f"enbl_dotted={enbl_dotted}, width_mode={width_mode}")
```

## Build a JSON catalogue

```python
import json
from vexy_lines import parse, GroupInfo, LayerInfo

def walk_fills(nodes):
    for node in nodes:
        if isinstance(node, GroupInfo):
            yield from walk_fills(node.children)
        elif isinstance(node, LayerInfo):
            yield from node.fills

doc = parse("artwork.lines")
catalogue = {
    "caption": doc.caption,
    "version": doc.version,
    "dpi": doc.dpi,
    "width_mm": doc.props.width_mm,
    "height_mm": doc.props.height_mm,
    "fills": [
        {
            "caption": f.caption,
            "type": f.params.fill_type,
            "color": f.params.color,
            "interval": f.params.interval,
            "angle": f.params.angle,
        }
        for f in walk_fills(doc.groups)
    ],
}

with open("catalogue.json", "w") as fp:
    json.dump(catalogue, fp, indent=2)
```

## Replace the source image

Swap the source photo in a `.lines` template to produce a new project with the same fill structure but different content:

```python
from vexy_lines import replace_source_image

replace_source_image(
    "template.lines",       # existing .lines with desired fill style
    "new_photo.jpg",         # replacement source image
    "output.lines",          # new .lines file
    target_size=(1025, 1025) # resize to match template dimensions
)
```

## Compare two .lines files

Check structural differences between two projects:

```python
from vexy_lines import parse, GroupInfo, LayerInfo

def structure_summary(nodes, depth=0):
    """Return a list of (depth, type, caption) tuples."""
    result = []
    for node in nodes:
        if isinstance(node, GroupInfo):
            result.append((depth, "group", node.caption))
            result.extend(structure_summary(node.children, depth + 1))
        elif isinstance(node, LayerInfo):
            result.append((depth, "layer", node.caption))
            for fill in node.fills:
                result.append((depth + 1, fill.params.fill_type, fill.caption))
    return result

doc_a = parse("artwork_v1.lines")
doc_b = parse("artwork_v2.lines")

struct_a = structure_summary(doc_a.groups)
struct_b = structure_summary(doc_b.groups)

if struct_a == struct_b:
    print("Identical structure")
else:
    print(f"Structure A: {len(struct_a)} nodes")
    print(f"Structure B: {len(struct_b)} nodes")
    # Show first difference
    for i, (a, b) in enumerate(zip(struct_a, struct_b)):
        if a != b:
            indent_a = "  " * a[0]
            indent_b = "  " * b[0]
            print(f"First difference at position {i}:")
            print(f"  A: {indent_a}{a[1]} '{a[2]}'")
            print(f"  B: {indent_b}{b[1]} '{b[2]}'")
            break
```

## Generate a visual report

Print an indented tree showing the full project structure:

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")

def print_tree(nodes, depth=0):
    indent = "  " * depth
    for node in nodes:
        if isinstance(node, GroupInfo):
            state = "[-]" if node.expanded else "[+]"
            print(f"{indent}{state} {node.caption}")
            print_tree(node.children, depth + 1)
        elif isinstance(node, LayerInfo):
            vis = "visible" if node.visible else "hidden"
            mask = " [masked]" if node.mask and node.mask.mask_type > 0 else ""
            print(f"{indent}  {node.caption} ({vis}{mask})")
            for fill in node.fills:
                p = fill.params
                print(f"{indent}    [{p.fill_type}] {fill.caption} "
                      f"color={p.color} interval={p.interval:.2f}")

print(f"Project: {doc.caption} (v{doc.version}, {doc.dpi} dpi)")
print(f"Canvas: {doc.props.width_mm:.1f} x {doc.props.height_mm:.1f} mm")
print()
print_tree(doc.groups)
```

Output:

```
Project: chameleon (v3.0.1, 300 dpi)
Canvas: 84.7 x 84.7 mm

[-] Background
    Layer 1 (visible [masked])
      [linear] Linear color=#000000 interval=2.28
```

## Generate thumbnails with Pillow

If you have Pillow installed, create contact sheets from preview images:

```python
from pathlib import Path
from io import BytesIO
from PIL import Image
from vexy_lines import parse

files = sorted(Path("./artwork").glob("*.lines"))
thumbs = []

for f in files:
    doc = parse(f)
    if doc.preview_image_data:
        img = Image.open(BytesIO(doc.preview_image_data))
        img.thumbnail((200, 200))
        thumbs.append((f.stem, img))

if not thumbs:
    print("No previews found")
else:
    # Build a contact sheet: 4 columns
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    cell = 220
    sheet = Image.new("RGB", (cols * cell, rows * cell), "white")

    for i, (name, img) in enumerate(thumbs):
        x = (i % cols) * cell + (cell - img.width) // 2
        y = (i // cols) * cell + (cell - img.height) // 2
        sheet.paste(img, (x, y))

    sheet.save("contact_sheet.png")
    print(f"Saved contact sheet with {len(thumbs)} thumbnails")
```

## Parse from a string (no file needed)

Useful for testing or when the XML comes from a database or API:

```python
from vexy_lines import parse_string

xml = """<?xml version="1.0" encoding="utf-8"?>
<Project caption="Test" version="3.0.1" dpi="300">
  <Document width_mm="100" height_mm="100" dpi="300"
            thicknessMin="0" thicknessMax="5"
            intervalMin="0.5" intervalMax="5" />
  <Objects>
    <FreeMesh caption="Layer 1" object_id="1" visible="1">
      <Objects>
        <LinearStrokesTmpl caption="Lines" object_id="10"
            color_name="#ff000000" interval="2" angle="0" />
      </Objects>
    </FreeMesh>
  </Objects>
</Project>"""

doc = parse_string(xml)
print(doc.caption)  # "Test"
print(len(doc.groups))  # 1
print(doc.groups[0].fills[0].params.fill_type)  # "linear"
```

## Export fill parameters to CSV

```python
import csv
from vexy_lines import parse, GroupInfo, LayerInfo

def walk_fills(nodes, path=""):
    for node in nodes:
        if isinstance(node, GroupInfo):
            yield from walk_fills(node.children, f"{path}/{node.caption}")
        elif isinstance(node, LayerInfo):
            for fill in node.fills:
                yield path, node.caption, fill

doc = parse("artwork.lines")

with open("fills.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["group_path", "layer", "fill", "type", "color",
                     "interval", "angle", "multiplier"])
    for group_path, layer_name, fill in walk_fills(doc.groups):
        p = fill.params
        writer.writerow([group_path, layer_name, fill.caption,
                         p.fill_type, p.color, p.interval, p.angle,
                         p.multiplier])
```
