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

---

### `DocumentProps`

Canvas dimensions and stroke range limits from the `<Document>` element.

| Field | Type | Description |
|-------|------|-------------|
| `width_mm` | `float` | Canvas width in millimetres |
| `height_mm` | `float` | Canvas height in millimetres |
| `dpi` | `int` | Document resolution |
| `thickness_min` | `float` | Minimum stroke thickness (mm) |
| `thickness_max` | `float` | Maximum stroke thickness (mm) |
| `interval_min` | `float` | Minimum line spacing (mm) |
| `interval_max` | `float` | Maximum line spacing (mm) |

---

### `GroupInfo`

A group (`<LrSection>` element) containing layers and sub-groups.

| Field | Type | Description |
|-------|------|-------------|
| `caption` | `str` | Group name |
| `object_id` | `int \| None` | Unique ID, or `None` for href references |
| `expanded` | `bool` | Whether the group is expanded in the UI |
| `children` | `list[GroupInfo \| LayerInfo]` | Child nodes |

---

### `LayerInfo`

A single layer (`<FreeMesh>` element) with fills and optional mask.

| Field | Type | Description |
|-------|------|-------------|
| `caption` | `str` | Layer name |
| `object_id` | `int \| None` | Unique ID |
| `visible` | `bool` | Whether the layer is visible |
| `mask` | `MaskInfo \| None` | Mask settings |
| `fills` | `list[FillNode]` | Ordered fill algorithms |
| `grid_edges` | `list[dict[str, str]]` | Mesh deformation data |

---

### `FillNode`

A single fill algorithm instance inside a layer.

| Field | Type | Description |
|-------|------|-------------|
| `xml_tag` | `str` | Original XML tag (e.g. `"LinearStrokesTmpl"`) |
| `caption` | `str` | Fill name as shown in the UI |
| `params` | `FillParams` | All fill parameters |
| `object_id` | `int \| None` | Unique ID |

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

`raw` includes algorithm-specific keys not promoted to named fields (e.g. `vert_disp`).

---

### `MaskInfo`

Mask settings from a `<MaskData>` element.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mask_type` | `int` | `0` | Mask mode: 0 = none, 1 = raster |
| `invert` | `bool` | `False` | Whether the mask is inverted |
| `tolerance` | `float` | `0.0` | Edge tolerance |

---

## Constants

### `FILL_TAG_MAP`

`dict[str, str]` mapping XML element tags to human-readable fill type names.

```python
from vexy_lines import FILL_TAG_MAP

FILL_TAG_MAP["LinearStrokesTmpl"]  # "linear"
FILL_TAG_MAP["SpiralStrokesTmpl"]  # "spiral"
```

### `FILL_TAGS`

`set[str]` of all recognised XML fill element tag names.

### `NUMERIC_PARAMS`

`list[str]` of XML attribute names whose values are numeric and can be interpolated: `interval`, `angle`, `thick_gap`, `smoothness`, `uplimit`, `downlimit`, `multiplier`, `base_width`, `dispersion`, `vert_disp`, `shear`.
