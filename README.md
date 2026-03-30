# vexy-lines-py

Parse [Vexy Lines](https://vexy.art) `.lines` vector art files in pure Python — no app, no macOS, no heavy dependencies.

## Install

```bash
pip install vexy-lines-py
```

Python 3.11+. Runtime dependency: `loguru` only.

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
                    # "linear"  "#1a2b3c"  interval=2.5

# Embedded source image (JPEG)
if doc.source_image_data:
    open("source.jpg", "wb").write(doc.source_image_data)

# Embedded preview image (PNG)
if doc.preview_image_data:
    open("preview.png", "wb").write(doc.preview_image_data)
```

Convenience wrappers for image extraction:

```python
from vexy_lines import extract_source_image, extract_preview_image

extract_source_image("artwork.lines", "source.jpg")
extract_preview_image("artwork.lines", "preview.png")
```

## API

> **Read-only parser.** This package parses `.lines` files but does not support creating or writing them. For creating and manipulating `.lines` documents, use `vexy-lines-apy` with the MCP API.

### `parse(path) -> LinesDocument`

Parse a `.lines` file and return a fully populated `LinesDocument`.

- `FileNotFoundError` — path does not exist
- `xml.etree.ElementTree.ParseError` — file is not valid XML

### `parse_string(xml_text) -> LinesDocument`

Parse a `.lines` XML string (in-memory) and return a `LinesDocument`. Useful when the XML content is already loaded or received from another source.

- `xml.etree.ElementTree.ParseError` — string is not valid XML

### `extract_source_image(path, output) -> Path`

Parse and save the embedded JPEG source image to *output*. Raises `ValueError` if no source image is present.

### `extract_preview_image(path, output) -> Path`

Parse and save the embedded PNG preview to *output*. Raises `ValueError` if no preview is present.

## Types

| Type | Key attributes |
|------|----------------|
| `LinesDocument` | `caption`, `version`, `dpi`, `props`, `groups`, `source_image_data`, `preview_image_data` |
| `DocumentProps` | `width_mm`, `height_mm`, `dpi`, `thickness_min/max`, `interval_min/max` |
| `GroupInfo` | `caption`, `object_id`, `expanded`, `children: list[GroupInfo | LayerInfo]` |
| `LayerInfo` | `caption`, `object_id`, `visible`, `mask`, `fills: list[FillNode]`, `grid_edges` |
| `FillNode` | `xml_tag`, `caption`, `params: FillParams`, `object_id` |
| `FillParams` | `fill_type`, `color`, `interval`, `angle`, `thickness`, `smoothness`, `uplimit`, `downlimit`, `multiplier`, `dispersion`, `shear`, `raw` |
| `MaskInfo` | `mask_type`, `invert`, `tolerance` |

`FillParams.raw` holds every original XML attribute, including algorithm-specific keys not promoted to named fields.

Colors are normalised to `#RRGGBB` (opaque) or `#RRGGBBAA`. The raw Vexy Lines `#AARRGGBB` encoding is converted automatically.

## Fill types

11 fill algorithms are recognised in `FillParams.fill_type`:

| Value | Algorithm | XML Tag |
|-------|-----------|---------|
| `linear` | Parallel straight lines | `LinearStrokesTmpl` |
| `wave` | Sine-wave strokes | `SigmoidStrokesTmpl` |
| `circular` | Concentric circles | `CircleStrokesTmpl` |
| `radial` | Lines radiating from a centre point | `RadialStrokesTmpl` |
| `spiral` | Archimedean spirals | `SpiralStrokesTmpl` |
| `scribble` | Random scribble-style strokes | `ScribbleStrokesTmpl` |
| `halftone` | Halftone dot/line patterns | `HalftoneStrokesTmpl` |
| `handmade` | Sketch-style handmade strokes | `FreeCurveStrokesTmpl` |
| `fractals` | Fractal / Peano space-filling strokes | `PeanoStrokesTmpl` |
| `trace` | Strokes following image contours | `TracedAreaTmpl` |
| `source_strokes` | Strokes derived from the source image | `SourceStrokes` |

`FreeCurveStrokesTmpl` with attribute `type_conv="9"` is resolved to `trace` at parse time (otherwise `handmade`).

The mapping from XML tags to these names is available as `FILL_TAG_MAP`. The full set of recognised tags is `FILL_TAGS`.

## Full documentation

[Read the docs](https://vexyart.github.io/vexy-lines/vexy-lines-py/) for the complete API reference, file format specification, and more examples.

## License

MIT
