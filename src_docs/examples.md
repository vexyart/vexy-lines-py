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
            # vert_disp is only in raw, not a named field
            vert_disp = fill.params.raw.get("vert_disp", "0")
            print(f"{fill.caption}: vert_disp={vert_disp}")
```

## Build a JSON catalogue

```python
import json
from dataclasses import asdict
from vexy_lines import parse

doc = parse("artwork.lines")
catalogue = {
    "caption": doc.caption,
    "version": doc.version,
    "dpi": doc.dpi,
    "width_mm": doc.props.width_mm,
    "height_mm": doc.props.height_mm,
}

with open("catalogue.json", "w") as f:
    json.dump(catalogue, f, indent=2)
```
