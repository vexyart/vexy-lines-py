# API Reference

## Functions

### `parse(path) -> LinesDocument`

Parse a `.lines` file and return a fully populated `LinesDocument`.

```python
from vexy_lines import parse

doc = parse("artwork.lines")
print(doc.caption, doc.dpi)
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Path to the `.lines` file |

**Returns:** `LinesDocument` with the full layer tree, document properties, and decoded images.

**Raises:**

- `FileNotFoundError` -- path does not exist
- `xml.etree.ElementTree.ParseError` -- file is not valid XML

**Type hint:**

```python
def parse(path: str | Path) -> LinesDocument: ...
```

---

### `parse_string(xml) -> LinesDocument`

Parse a `.lines` XML string and return a `LinesDocument`. Use this when you already have the XML content in memory (from a network response, database, or test fixture) instead of a file path.

```python
from vexy_lines import parse_string

xml = open("artwork.lines").read()
doc = parse_string(xml)
print(doc.caption, doc.dpi)
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `xml` | `str` | Raw XML string from a `.lines` file |

**Returns:** `LinesDocument` with the full layer tree, document properties, and decoded images.

**Raises:**

- `xml.etree.ElementTree.ParseError` -- string is not valid XML

**Type hint:**

```python
def parse_string(xml: str) -> LinesDocument: ...
```

---

### `extract_source_image(path, output) -> Path`

Parse a `.lines` file and save the embedded JPEG source image.

```python
from vexy_lines import extract_source_image

extract_source_image("artwork.lines", "source.jpg")
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Path to the `.lines` file |
| `output` | `str \| Path` | Destination path for the JPEG |

**Returns:** Resolved output `Path`.

**Raises:**

- `FileNotFoundError` -- `.lines` file does not exist
- `ValueError` -- no source image embedded in the file

---

### `extract_preview_image(path, output) -> Path`

Parse a `.lines` file and save the embedded PNG preview image.

```python
from vexy_lines import extract_preview_image

extract_preview_image("artwork.lines", "preview.png")
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str \| Path` | Path to the `.lines` file |
| `output` | `str \| Path` | Destination path for the PNG |

**Returns:** Resolved output `Path`.

**Raises:**

- `FileNotFoundError` -- `.lines` file does not exist
- `ValueError` -- no preview image embedded in the file

---

### `replace_source_image(lines_path, new_image_path, output_path, *, target_size) -> Path`

Replace the embedded source image in a `.lines` file, writing the result to a new file. All fill parameters, layers, groups, masks, and document settings are preserved. The new image is converted to JPEG if needed (the `.lines` format requires JPEG for source images).

Requires the `pillow` package (installed as a dependency).

```python
from vexy_lines import replace_source_image

replace_source_image(
    "template.lines",
    "new_photo.png",
    "output.lines",
    target_size=(1025, 1025),
)
```

**Args:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `lines_path` | `str \| Path` | Path to the source `.lines` file (template) |
| `new_image_path` | `str \| Path` | Path to the replacement image (JPEG, PNG, etc.) |
| `output_path` | `str \| Path` | Where to write the modified `.lines` file |
| `target_size` | `tuple[int, int] \| None` | Optional `(width, height)` to resize the new image to fit |

When `target_size` is provided and the new image dimensions differ, the image is scaled to fit within the target dimensions (maintaining aspect ratio) and centred on a white canvas. White padding is correct for Vexy Lines: fill algorithms treat white as "no strokes".

**Returns:** Resolved output `Path`.

**Raises:**

- `FileNotFoundError` -- either input file does not exist
- `ValueError` -- the `.lines` file has no `<SourcePict>` element

**Type hint:**

```python
def replace_source_image(
    lines_path: str | Path,
    new_image_path: str | Path,
    output_path: str | Path,
    *,
    target_size: tuple[int, int] | None = None,
) -> Path: ...
```

---

## Dataclasses

### `LinesDocument`

Everything parsed from a `.lines` file.

| Field | Type | Description |
|-------|------|-------------|
| `caption` | `str` | Project name from the root `<Project>` element |
| `version` | `str` | Vexy Lines app version that created the file |
| `dpi` | `int` | Document resolution (default 300) |
| `props` | `DocumentProps` | Canvas dimensions and stroke limits |
| `groups` | `list[GroupInfo \| LayerInfo]` | Top-level layer tree |
| `source_image_data` | `bytes \| None` | Decoded JPEG bytes of the source image |
| `preview_image_data` | `bytes \| None` | Decoded PNG bytes of the preview |

All fields have defaults, so `LinesDocument()` creates a valid empty document.

---

### `DocumentProps`

Canvas dimensions and stroke range limits from the `<Document>` element.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width_mm` | `float` | `0.0` | Canvas width in millimetres |
| `height_mm` | `float` | `0.0` | Canvas height in millimetres |
| `dpi` | `int` | `300` | Document resolution |
| `thickness_min` | `float` | `0.0` | Minimum stroke thickness (mm) |
| `thickness_max` | `float` | `0.0` | Maximum stroke thickness (mm) |
| `interval_min` | `float` | `0.0` | Minimum line spacing (mm) |
| `interval_max` | `float` | `0.0` | Maximum line spacing (mm) |

Maps from XML attributes: `thicknessMin` -> `thickness_min`, `thicknessMax` -> `thickness_max`, `intervalMin` -> `interval_min`, `intervalMax` -> `interval_max`.

---

### `GroupInfo`

A group (`<LrSection>` element) containing layers and sub-groups.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `caption` | `str` | -- | Group name |
| `object_id` | `int \| None` | `None` | Unique ID, or `None` for href references |
| `expanded` | `bool` | `True` | Whether the group is expanded in the UI |
| `children` | `list[GroupInfo \| LayerInfo]` | `[]` | Child nodes |

---

### `LayerInfo`

A single layer (`<FreeMesh>` element) with fills and optional mask.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `caption` | `str` | -- | Layer name |
| `object_id` | `int \| None` | `None` | Unique ID |
| `visible` | `bool` | `True` | Whether the layer is visible |
| `mask` | `MaskInfo \| None` | `None` | Mask settings |
| `fills` | `list[FillNode]` | `[]` | Ordered fill algorithms |
| `grid_edges` | `list[dict[str, str]]` | `[]` | Mesh deformation data |

Each entry in `grid_edges` is a dict with a `"type"` key (`"row_grid_edge"` or `"col_grid_edge"`) plus all XML attributes as string key-value pairs.

---

### `FillNode`

A single fill algorithm instance inside a layer.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `xml_tag` | `str` | -- | Original XML tag (e.g. `"LinearStrokesTmpl"`) |
| `caption` | `str` | -- | Fill name as shown in the UI |
| `params` | `FillParams` | -- | All fill parameters |
| `object_id` | `int \| None` | `None` | Unique ID |

---

### `FillParams`

Numeric and colour parameters for a fill algorithm.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fill_type` | `str` | -- | Algorithm name (e.g. `"linear"`, `"circular"`) |
| `color` | `str` | -- | Normalised hex colour (`#RRGGBB` or `#RRGGBBAA`) |
| `interval` | `float` | `0.0` | Line spacing in mm |
| `angle` | `float` | `0.0` | Stroke angle in degrees |
| `thickness` | `float` | `0.0` | Stroke thickness (from XML `thick_gap`) |
| `thickness_min` | `float` | `0.0` | Minimum thickness (from XML `base_width`) |
| `smoothness` | `float` | `0.0` | Curve smoothness factor |
| `uplimit` | `float` | `0.0` | Upper brightness threshold (0--255) |
| `downlimit` | `float` | `255.0` | Lower brightness threshold (0--255) |
| `multiplier` | `float` | `1.0` | Width multiplier |
| `base_width` | `float` | `0.0` | Baseline stroke width in mm |
| `dispersion` | `float` | `0.0` | Random perpendicular offset |
| `shear` | `float` | `0.0` | Shear distortion angle in degrees |
| `raw` | `dict[str, str]` | `{}` | All original XML attributes |

`raw` includes every attribute from the XML element, including algorithm-specific keys not promoted to named fields (e.g. `vert_disp`, `enbl_dotted`, `type_conv`). See the [File Format](file-format.md) reference for the complete attribute catalogue.

---

### `MaskInfo`

Mask settings from a `<MaskData>` element.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mask_type` | `int` | `0` | Mask mode: 0 = none, 1 = raster |
| `invert` | `bool` | `False` | Whether the mask is inverted |
| `tolerance` | `float` | `0.0` | Edge tolerance |

Maps from XML: `invert_mask` -> `invert` (any value other than `"0"` is `True`).

---

## Constants

### `FILL_TAG_MAP`

`dict[str, str]` mapping XML element tags to human-readable fill type names.

```python
from vexy_lines import FILL_TAG_MAP

FILL_TAG_MAP["LinearStrokesTmpl"]       # "linear"
FILL_TAG_MAP["SigmoidStrokesTmpl"]      # "wave"
FILL_TAG_MAP["CircleStrokesTmpl"]       # "circular"
FILL_TAG_MAP["RadialStrokesTmpl"]       # "radial"
FILL_TAG_MAP["SpiralStrokesTmpl"]       # "spiral"
FILL_TAG_MAP["ScribbleStrokesTmpl"]     # "scribble"
FILL_TAG_MAP["HalftoneStrokesTmpl"]     # "halftone"
FILL_TAG_MAP["FreeCurveStrokesTmpl"]    # "handmade"
FILL_TAG_MAP["PeanoStrokesTmpl"]        # "fractals"
FILL_TAG_MAP["TracedAreaTmpl"]          # "trace"
FILL_TAG_MAP["SourceStrokes"]           # "source_strokes"
```

Note: `FreeCurveStrokesTmpl` resolves to `"trace"` at parse time when `type_conv="9"`. The map holds the base mapping (`"handmade"`); the parser applies the override.

### `FILL_TAGS`

`set[str]` of all recognised XML fill element tag names (keys of `FILL_TAG_MAP`).

```python
from vexy_lines import FILL_TAGS

"LinearStrokesTmpl" in FILL_TAGS  # True
"UnknownElement" in FILL_TAGS     # False
```

### `NUMERIC_PARAMS`

`list[str]` of XML attribute names whose values are numeric and can be interpolated between two fills of the same type.

```python
from vexy_lines import NUMERIC_PARAMS

print(NUMERIC_PARAMS)
# ['interval', 'angle', 'thick_gap', 'smoothness', 'uplimit',
#  'downlimit', 'multiplier', 'base_width', 'dispersion',
#  'vert_disp', 'shear']
```

These are the XML attribute names (not the Python field names). Most map directly to `FillParams` fields; `vert_disp` is only available in `FillParams.raw`.

---

## Error handling

The parser is lenient where possible and strict where data integrity matters.

**Lenient behaviour:**

- Missing numeric attributes default to `0.0` (or field-specific defaults like `255.0` for `downlimit`)
- Missing `color_name` defaults to `"#000000"`
- Unparseable numeric strings fall back to the default value
- Missing `<Document>` element produces a default `DocumentProps()`
- Failed source/preview image decoding logs a warning and sets the field to `None`

**Strict behaviour:**

- `parse()` raises `FileNotFoundError` if the path does not exist
- `parse()` raises `ET.ParseError` if the XML is malformed
- `extract_source_image()` / `extract_preview_image()` raise `ValueError` if no image is embedded

**Pattern for safe parsing:**

```python
from vexy_lines import parse

try:
    doc = parse("artwork.lines")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Parse error: {e}")
else:
    if doc.source_image_data:
        print(f"Source image: {len(doc.source_image_data)} bytes")
    else:
        print("No source image embedded")
```

---

## Thread safety

The parser is stateless and safe to call from multiple threads concurrently. Each call to `parse()` or `parse_string()` creates its own XML tree and dataclass instances with no shared mutable state.

The `loguru` logger used internally is thread-safe.

`replace_source_image()` performs file I/O (copy + XML write) and is **not** safe to call concurrently on the same output file.

---

## Performance

Parsing performance depends on file size, which is dominated by embedded images:

- **XML parsing**: `xml.etree.ElementTree` (C-accelerated in CPython) handles the structural parsing. Typical layer trees with hundreds of fills parse in under 10ms.
- **Image decoding**: The base64 decode + zlib decompress of the source image is the main cost. A 5MB JPEG source adds ~50--100ms.
- **Memory**: The decoded JPEG and PNG bytes are held in memory as `bytes` objects on the `LinesDocument`. For files with large embedded images, expect memory usage roughly 2x the uncompressed image size (compressed + decompressed copies during decode, then only decompressed is retained).

**Tips for large files:**

- If you only need metadata (fills, layer tree), the overhead is the image decoding. The parser currently always decodes images when present. Access `doc.groups` and `doc.props` without touching the image fields.
- For batch processing many files, parse in a process pool to parallelise the zlib decompression.
- `parse_string()` avoids the file I/O overhead when you already have the XML in memory.
