# vexy-lines-py

Parse [Vexy Lines](https://vexy.art) `.lines` vector art files in pure Python — no app, no macOS, no heavy dependencies.

## Install

```bash
pip install vexy-lines-py
```

Python 3.11+. Runtime dependencies: `loguru` (logging) and `pillow` (image conversion in `replace_source_image()`).

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
                    for image_filter in fill.image_filters:
                        print(image_filter.name, image_filter.params)
                        # "brightness" {"value": 25.0}

# Embedded document source image (JPEG)
if doc.source_image_data:
    open("source.jpg", "wb").write(doc.source_image_data)

# Every embedded source image: document first, then group sources
for source in doc.source_images:
    print(source.index, source.scope, source.owner_path, source.width, source.height)

# Embedded preview image (PNG)
if doc.preview_image_data:
    open("preview.png", "wb").write(doc.preview_image_data)
```

Convenience wrappers for image extraction:

```python
from vexy_lines import extract_source_image, extract_source_images, extract_preview_image

extract_source_image("artwork.lines", "source.jpg")
extract_source_images("artwork.lines", "artwork-sources/")
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

Parse and save the document-level embedded JPEG source image to *output*. Raises `ValueError` if no source image is present.

### `extract_source_images(path, output_dir) -> list[Path]`

Parse and save every canonical source image: the document source first, then source images attached to groups. Href references are ignored. Output files use stable names such as `artwork-source-001-document.jpg` and `artwork-source-002-face.jpg`.

### `extract_preview_image(path, output) -> Path`

Parse and save the embedded PNG preview to *output*. Raises `ValueError` if no preview is present.

## Editing .lines files

Three helpers edit a `.lines` file while preserving everything else (fill parameters, masks, mesh, document settings) byte-for-byte. Each writes to `output_path` (pass the same path as the input to edit in place).

### `replace_source_image(lines_path, new_image_path, output_path, *, target_size=None) -> Path`

Swap the embedded JPEG source image, reusing a `.lines` file's fill style with new content. Requires `pillow`. Raises `FileNotFoundError` if an input is missing, `ValueError` if there is no `<SourcePict>`.

### `rename_objects(lines_path, output_path, renames) -> int`

Rewrite the `caption` of groups, layers, and/or fills. `renames` maps `object_id` (from `GroupInfo`/`LayerInfo`/`FillNode`) to a new caption; returns the number actually changed (a caption already equal to its target is not counted). Only canonical definitions are touched — `href` reference elements have no `object_id`.

### `set_visibility(lines_path, output_path, visible) -> int`

Set the `visible="0"`/`"1"` attribute (absent = visible) per `object_id`; returns the number changed. Toggling visibility *live* over the app's [MCP API](https://help.vexy.art/lines/) does not change what the app exports, but baking the attribute into a copy and re-opening it does — this is how the AI-rename feature renders one fill in isolation.

```python
from vexy_lines import rename_objects, set_visibility

rename_objects("artwork.lines", "artwork.lines", {1: "Background", 10: "Sky lines"})
set_visibility("artwork.lines", "fill_10_only.lines", {10: True, 11: False, 12: False})
```

Both raise `FileNotFoundError` if `lines_path` is missing.

## Types

| Type | Key attributes |
|------|----------------|
| `LinesDocument` | `caption`, `version`, `dpi`, `props`, `groups`, `source_image_data`, `source_images`, `preview_image_data` |
| `DocumentProps` | `width_mm`, `height_mm`, `dpi`, `thickness_min/max`, `interval_min/max` |
| `GroupInfo` | `caption`, `object_id`, `expanded`, `children: list[GroupInfo | LayerInfo]` |
| `LayerInfo` | `caption`, `object_id`, `visible`, `mask`, `fills: list[FillNode]`, `grid_edges` |
| `FillNode` | `xml_tag`, `caption`, `params: FillParams`, `image_filters: list[ImageFilterEntry]`, `object_id` |
| `FillParams` | `fill_type`, `color`, `interval`, `angle`, `thickness`, `smoothness`, `uplimit`, `downlimit`, `multiplier`, `dispersion`, `shear`, `raw` |
| `ImageFilterEntry` | `type_id`, `name`, `params`, `raw` |
| `MaskInfo` | `mask_type`, `invert`, `tolerance` |
| `SourceImageInfo` | `index`, `data`, `scope`, `caption`, `object_id`, `owner_caption`, `owner_path`, `width`, `height` |

`FillParams.raw` holds every original XML attribute, including algorithm-specific keys not promoted to named fields.

`FillNode.image_filters` holds the ordered source-image filter chain saved inside a fill's `<image_filters>` child. Known filters are named `brightness`, `contrast`, `blur`, `sharpen`, `levels`, `shadows_highlights`, `invert`, `remove_background`, `color`, and `gradient`; unknown future filter IDs are preserved as `unknown_<id>` with their raw attributes.

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
