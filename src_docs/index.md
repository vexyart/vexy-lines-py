# vexy-lines-py

Parse [Vexy Lines](https://vexy.art) `.lines` vector art files in pure Python.

No app. No macOS. No heavy dependencies. Just `pip install` and go.

## What it does

A `.lines` file holds everything Vexy Lines needs to reproduce a piece of vector artwork: the layer tree (groups, layers, fills with algorithm parameters), document properties, and optionally the original source image and a rendered preview -- all packed into XML.

This package reads that XML and gives you typed Python dataclasses.

## Quick start

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")
print(doc.caption, doc.dpi)          # "My Art"  300
print(doc.props.width_mm, "x", doc.props.height_mm, "mm")

# Walk the layer tree
for node in doc.groups:
    if isinstance(node, GroupInfo):
        for child in node.children:
            if isinstance(child, LayerInfo):
                for fill in child.fills:
                    p = fill.params
                    print(p.fill_type, p.color, f"interval={p.interval}")
```

## Extract embedded images

Every `.lines` file can contain a JPEG source image (the original photo) and a PNG preview (the rendered result). Pull them out without opening the app:

```python
from vexy_lines import extract_source_image, extract_preview_image

extract_source_image("artwork.lines", "source.jpg")
extract_preview_image("artwork.lines", "preview.png")
```

## Why this package exists

Vexy Lines is a macOS/Windows app that transforms raster images into vector artwork using 14 fill algorithms. The `.lines` file format stores everything -- but it's undocumented XML.

This package decodes that format so you can:

- Inspect artwork metadata without the app
- Extract embedded images for thumbnailing or cataloguing
- Feed fill parameters into automation pipelines
- Build tools on top of the parsed data (style transfer, interpolation, batch processing)

## Next steps

- [Installation](installation.md) -- install options and requirements
- [API Reference](api-reference.md) -- every class, function, and constant
- [File Format](file-format.md) -- how `.lines` XML is structured
- [Examples](examples.md) -- real-world usage patterns
