# vexy-lines-py

Pure-Python cross-platform parser for the [Vexy Lines](https://vexy.art) `.lines` vector art format. Read and extract data from `.lines` files without requiring the Vexy Lines application.

## Installation

```bash
pip install vexy-lines-py
```

## Quick start

```python
from vexy_lines import parse

doc = parse("artwork.lines")

print(f"{doc.caption} (v{doc.version}, {doc.dpi} DPI)")
print(f"Canvas: {doc.props.width_mm} x {doc.props.height_mm} mm")

for item in doc.groups:
    print(f"  {item.caption}")
```

### Extract embedded images

```python
from vexy_lines import extract_source_image, extract_preview_image

# Source photograph (JPEG)
extract_source_image("artwork.lines", "source.jpg")

# Preview render (PNG)
extract_preview_image("artwork.lines", "preview.png")
```

### Inspect fills

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")

for item in doc.groups:
    if isinstance(item, GroupInfo):
        for child in item.children:
            if isinstance(child, LayerInfo):
                for fill in child.fills:
                    p = fill.params
                    print(f"  {fill.caption}: {p.fill_type} {p.color} interval={p.interval}")
```

## API reference

### Functions

| Function | Description |
|----------|-------------|
| `parse(path)` | Parse a `.lines` file into a `LinesDocument` |
| `extract_source_image(path, output)` | Extract the embedded JPEG source image |
| `extract_preview_image(path, output)` | Extract the embedded PNG preview image |

### Types

| Type | Description |
|------|-------------|
| `LinesDocument` | Top-level document: caption, version, DPI, props, layer tree, images |
| `DocumentProps` | Canvas dimensions, DPI, thickness/interval ranges |
| `GroupInfo` | Layer group with caption, children (groups or layers) |
| `LayerInfo` | Layer with fills, mask, grid edges, visibility |
| `FillNode` | Single fill: XML tag, caption, parsed parameters |
| `FillParams` | Numeric fill parameters: type, colour, interval, angle, thickness, etc. |
| `MaskInfo` | Layer mask: type, invert flag, tolerance |

### Constants

| Constant | Description |
|----------|-------------|
| `FILL_TAG_MAP` | `dict[str, str]` mapping XML tags to human-readable fill type names |
| `FILL_TAGS` | `set[str]` of all recognised fill element tags |
| `NUMERIC_PARAMS` | `list[str]` of interpolatable numeric fill attributes |

## The .lines format

`.lines` files are XML documents produced by the Vexy Lines vector art application. They contain:

- **Layer tree** -- groups and layers, each with ordered fill definitions
- **Fill parameters** -- type (linear, circular, wave, etc.), colour, interval, angle, thickness, and more
- **Source image** -- the original photograph, stored as base64-encoded zlib-compressed JPEG
- **Preview image** -- a rendered preview, stored as base64-encoded PNG
- **Document properties** -- canvas size, DPI, global thickness and interval ranges

## License

MIT
