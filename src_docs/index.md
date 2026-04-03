
[Vexy Lines for Mac & Windows](https://vexy.art/lines/) | [Download](https://www.vexy.art/lines/#buy) | [Buy](https://www.vexy.art/lines/#buy) | [Batch GUI](https://vexy.dev/vexy-lines-run/) | [CLI/MCP](https://vexy.dev/vexy-lines-cli/) | [API](https://vexy.dev/vexy-lines-apy/) | **.lines format**

[![Vexy Lines](https://i.vexy.art/vl/websiteart/vexy-lines-hero-poster.png)](https://www.vexy.art/lines/)

# vexy-lines-py

Parse [Vexy Lines](https://vexy.art/lines/) `.lines` vector art files in pure Python.

- [On Github](https://github.com/vexyart/vexy-lines-py)
- [On PyPI](https://pypi.org/project/vexy-lines-py/)

## What it does

A `.lines` file holds everything Vexy Lines needs to reproduce a piece of vector artwork: the layer tree (groups, layers, fills with algorithm parameters), document properties, and optionally the original source image and a rendered preview -- all packed into XML.

This package reads that XML and gives you typed Python dataclasses. It can also replace the embedded source image to reuse a fill style with different content.

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

## Replace the source image

Swap the source photo in an existing `.lines` file to reuse its fill style with new content:

```python
from vexy_lines import replace_source_image

replace_source_image("template.lines", "new_photo.jpg", "output.lines")
```

## Parse from a string

When you already have the XML in memory:

```python
from vexy_lines import parse_string

doc = parse_string(xml_content)
```

## Why this package exists

Vexy Lines is a macOS/Windows app that transforms raster images into vector artwork using 14 fill algorithms. The `.lines` file format stores everything -- but it's undocumented XML.

This package decodes that format so you can:

- Inspect artwork metadata without the app
- Extract embedded images for thumbnailing or cataloguing
- Feed fill parameters into automation pipelines
- Replace source images to reuse fill styles with different content
- Build tools on top of the parsed data (style transfer, interpolation, batch processing)

## Next steps

- [Installation](installation.md) -- install options and requirements
- [API Reference](api-reference.md) -- every class, function, and constant
- [File Format](file-format.md) -- how `.lines` XML is structured
- [Examples](examples.md) -- real-world usage patterns
