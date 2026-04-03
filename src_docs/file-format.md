# .lines File Format

The `.lines` format is XML. A single file holds the complete Vexy Lines project: layer tree, fill parameters, document properties, the original source image, and a rendered preview.

This page documents every element and attribute observed in real `.lines` files, verified against the `vexy-lines-py` parser source code and test data.

## Document structure

```
<Project>
  <form_data>              (internal, ignored by parser)
  <Objects>                 layer tree root
    <LrSection>             group
      <Objects>
        <FreeMesh>          layer
          <Objects>
            <*StrokesTmpl>  fill
          <MaskData>        optional mask
          <row_grid_edge>   mesh row
          <col_grid_edge>   mesh column
  <SourcePict>              embedded source image (JPEG, compressed)
  <Document>                canvas dimensions, stroke limits
  <Workspace>               viewport state (ignored by parser)
  <PreviewDoc>              embedded preview image (PNG)
</Project>
```

## Root element: `<Project>`

```xml
<Project caption="My Art" version="3.0.1" app="vexylines" dpi="300"
         object_id="2" expanded="1" type="16777602"
         is_transparent="0" fusion_of_templates="0">
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `caption` | string | Project name |
| `version` | string | Vexy Lines app version that created the file |
| `app` | string | Application identifier, always `"vexylines"` |
| `dpi` | int | Document resolution in dots per inch |
| `object_id` | int | Unique object ID for the root node |
| `expanded` | `"0"` / `"1"` | Whether the root is expanded in the UI |
| `type` | int | Internal type code (`16777602`) |
| `is_transparent` | `"0"` / `"1"` | Background transparency flag |
| `fusion_of_templates` | `"0"` / `"1"` | Internal rendering flag |

The parser reads `caption`, `version`, and `dpi`. Other attributes are preserved in the XML but not promoted to dataclass fields.

## `<Document>` element

Canvas dimensions and global stroke limits.

```xml
<Document width_mm="210.0" height_mm="297.0" dpi="300"
          thicknessMin="0" thicknessMax="5.66"
          intervalMin="0.283" intervalMax="5.66"
          termNodesMax="62.16"
          current_unit="0"
          source_opacity="0.44"
          project_back_color="4294967295"
          selected_color="4288616596"
          frame_color="4281492680"
          freehand_color="4280221440"
          single_workspace="0"
          type="16777219" />
```

| Attribute | Type | Parsed | Description |
|-----------|------|--------|-------------|
| `width_mm` | float | yes | Canvas width in millimetres |
| `height_mm` | float | yes | Canvas height in millimetres |
| `dpi` | int | yes | Document resolution (default 300) |
| `thicknessMin` | float | yes | Minimum stroke thickness (mm) |
| `thicknessMax` | float | yes | Maximum stroke thickness (mm) |
| `intervalMin` | float | yes | Minimum line spacing (mm) |
| `intervalMax` | float | yes | Maximum line spacing (mm) |
| `termNodesMax` | float | no | Maximum terminal node size |
| `current_unit` | int | no | Display unit: `0`=mm, `1`=cm, `2`=inches, `3`=points |
| `source_opacity` | float | no | Source image overlay opacity (0.0--1.0) |
| `project_back_color` | decimal ARGB | no | Background colour (decimal integer) |
| `selected_color` | decimal ARGB | no | Selection highlight colour |
| `frame_color` | decimal ARGB | no | Frame border colour |
| `freehand_color` | decimal ARGB | no | Freehand drawing colour |
| `single_workspace` | `"0"` / `"1"` | no | Single workspace mode flag |
| `type` | int | no | Internal type code (`16777219`) |

Unparsed attributes are accessible via the raw XML when using `xml.etree.ElementTree` directly.

## Layer tree

The `<Objects>` element directly under `<Project>` is the root of the layer tree. It contains two node types: groups and layers.

### Groups: `<LrSection>`

```xml
<LrSection caption="Group 1" object_id="5" expanded="1"
           type="16777602" dpi="0"
           is_transparent="0" fusion_of_templates="0">
  <Objects>
    <!-- child layers and sub-groups -->
  </Objects>
</LrSection>
```

| Attribute | Type | Parsed | Description |
|-----------|------|--------|-------------|
| `caption` | string | yes | Group name |
| `object_id` | int | yes | Unique ID |
| `expanded` | `"0"` / `"1"` | yes | Whether group is expanded in the UI tree |
| `type` | int | no | Internal type code (`16777602`) |
| `dpi` | int | no | Group-level DPI override (usually `0`) |
| `is_transparent` | `"0"` / `"1"` | no | Transparency flag |
| `fusion_of_templates` | `"0"` / `"1"` | no | Template fusion flag |

Groups nest recursively. A group's `<Objects>` child can contain both `<FreeMesh>` (layers) and nested `<LrSection>` (sub-groups).

### Layers: `<FreeMesh>`

```xml
<FreeMesh caption="Layer 1" object_id="936" visible="1"
          expanded="1" selected="1"
          type="16793857" dpi="0"
          z_mask_enbl="0" z_mask_mode="0" z_mask_quality="6"
          thickness_mul="1" interval_mul="1" rotation_mul="0"
          is_unbounded="1" mask_by_form="0"
          cx="114.84" cy="153.12">
  <Objects>
    <!-- fill elements -->
  </Objects>
  <MaskData ... />
  <row_grid_edge ... />
  <col_grid_edge ... />
</FreeMesh>
```

| Attribute | Type | Parsed | Description |
|-----------|------|--------|-------------|
| `caption` | string | yes | Layer name |
| `object_id` | int | yes | Unique ID |
| `visible` | `"0"` / `"1"` | yes | `"0"` hides the layer; absent means visible |
| `expanded` | `"0"` / `"1"` | no | Tree expansion state |
| `selected` | `"0"` / `"1"` | no | Whether layer is selected |
| `type` | int | no | Internal type code (`16793857`) |
| `dpi` | int | no | Layer-level DPI |
| `cx`, `cy` | float | no | Layer centre coordinates (pixels) |
| `thickness_mul` | float | no | Thickness multiplier for all fills in this layer |
| `interval_mul` | float | no | Interval multiplier for all fills |
| `rotation_mul` | float | no | Rotation multiplier |
| `z_mask_enbl` | `"0"` / `"1"` | no | Z-depth mask enabled |
| `z_mask_mode` | int | no | Z-depth mask mode |
| `z_mask_quality` | int | no | Z-depth mask quality (1--10) |
| `is_unbounded` | `"0"` / `"1"` | no | Whether fills extend beyond canvas |
| `mask_by_form` | `"0"` / `"1"` | no | Mask by vector form |
| `locked` | `"0"` / `"1"` | no | Editing lock |

## Fill elements

Each fill is an XML element inside a layer's `<Objects>`. The tag name identifies the algorithm.

### Fill tag to algorithm mapping

| XML Tag | `fill_type` | Algorithm |
|---------|-------------|-----------|
| `LinearStrokesTmpl` | `linear` | Parallel straight lines |
| `SigmoidStrokesTmpl` | `wave` | Sinusoidal wave strokes |
| `CircleStrokesTmpl` | `circular` | Concentric circles |
| `RadialStrokesTmpl` | `radial` | Lines radiating from centre |
| `SpiralStrokesTmpl` | `spiral` | Spiral from centre outward |
| `ScribbleStrokesTmpl` | `scribble` | Randomised scribble paths |
| `HalftoneStrokesTmpl` | `halftone` | Grid-based halftone dots/shapes |
| `FreeCurveStrokesTmpl` | `handmade` | Freehand curves (default) |
| `FreeCurveStrokesTmpl` (with `type_conv="9"`) | `trace` | Edge-tracing curves |
| `PeanoStrokesTmpl` | `fractals` | Space-filling Peano/fractal curves |
| `TracedAreaTmpl` | `trace` | Traced area fills |
| `SourceStrokes` | `source_strokes` | Strokes imported from source vector |

The `FreeCurveStrokesTmpl` tag serves double duty. When its `type_conv` attribute equals `"9"`, the parser resolves it to `"trace"`. All other `type_conv` values (including absent) resolve to `"handmade"`.

### Common fill attributes

These attributes appear on most or all fill element tags. The parser promotes a subset to named `FillParams` fields; the rest are available in `FillParams.raw`.

#### Core parameters (promoted to `FillParams` fields)

| XML Attribute | `FillParams` Field | Type | Default | Description |
|---------------|-------------------|------|---------|-------------|
| `color_name` | `color` | `#AARRGGBB` | `"#000000"` | Stroke colour (see [Colour encoding](#colour-encoding)) |
| `interval` | `interval` | float | `0.0` | Line spacing in mm |
| `angle` | `angle` | float | `0.0` | Stroke angle in degrees |
| `thick_gap` | `thickness` | float | `0.0` | Stroke thickness / gap ratio |
| `base_width` | `thickness_min`, `base_width` | float | `0.0` | Baseline stroke width in mm |
| `smoothness` | `smoothness` | float | `0.0` | Curve smoothness factor |
| `uplimit` | `uplimit` | float | `0.0` | Upper brightness threshold (0--255) |
| `downlimit` | `downlimit` | float | `255.0` | Lower brightness threshold (0--255) |
| `multiplier` | `multiplier` | float | `1.0` | Width multiplier applied to strokes |
| `dispersion` | `dispersion` | float | `0.0` | Random perpendicular offset |
| `shear` | `shear` | float | `0.0` | Shear distortion angle in degrees |

Note: `base_width` maps to *both* `FillParams.thickness_min` and `FillParams.base_width` (they read the same XML attribute).

#### Width and thickness control (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `vert_disp` | float | Vertical displacement of strokes |
| `enbl_width` | `"0"` / `"1"` | Enable width variation from source image brightness |
| `smooth_width` | float | Width variation smoothness (higher = smoother transitions) |
| `width_mode` | int | Width calculation mode: `0`=standard, `2`=alternate |
| `static_stroke` | `"0"` / `"1"` | Use uniform stroke width (ignore brightness) |

#### Bas-relief effect (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `enbl_basrelief` | `"0"` / `"1"` | Enable bas-relief shading effect |
| `bsrf_rise` | float | Bas-relief height/rise factor |
| `bsrf_smoothness` | float | Bas-relief smoothness |
| `bsrf_front` | `"0"` / `"1"` | Bas-relief front lighting |

#### Dotted line control (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `enbl_dotted` | `"0"` / `"1"` | Enable dotted/dashed stroke mode |
| `null_in_cut` | `"0"` / `"1"` | Insert nulls at intersection cuts |
| `null_tails_count` | float | Number of null segments at stroke tails |
| `invert_dotted` | `"0"` / `"1"` | Invert dot/dash pattern |
| `length_black` | float | Length of the dash (black) segment |
| `length_white` | float | Length of the gap (white) segment |
| `edged_dashes` | `"0"` / `"1"` | Sharpen dash edges |
| `edged_strokes` | `"0"` / `"1"` | Sharpen stroke edges |
| `dashes_cup` | `"0"` / `"1"` | Rounded dash caps |
| `dashes_orientation` | int | Dash orientation mode |
| `dash_comb_thick` | `"0"` / `"1"` | Combine dash with thickness variation |
| `dash_dots_mode` | int | Dash/dot combination mode |

#### Edge and contour (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `is_edge` | `"0"` / `"1"` | Enable edge detection mode |
| `edge_global` | `"0"` / `"1"` | Use global edge detection |
| `edge_mul` | float | Edge detection multiplier |

#### Colour mode (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `color_mode` | int | `0`=solid, `1`=source palette, `2`=single, `3`=monochrome |
| `color_seg_len` | float | Colour segment length for multi-colour modes |
| `channel_mode` | int | Channel interpretation mode |
| `channel_invert` | `"0"` / `"1"` | Invert channel for brightness calculation |
| `channel_mask` | int | Channel mask for brightness extraction |
| `invert_cont` | `"0"` / `"1"` | Invert contrast mapping |
| `invert_wdth` | `"0"` / `"1"` | Invert width mapping |

#### Image processing (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `image_contrast` | float | Pre-processing contrast adjustment |
| `image_brightness` | float | Pre-processing brightness adjustment |

#### Stroke caps and joins (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `curve_cup_front` | `"0"` / `"1"` | Rounded cap at stroke front |
| `curve_cup_back` | `"0"` / `"1"` | Rounded cap at stroke back |
| `thick_cup` | `"0"` / `"1"` | Thickness-dependent caps |
| `join_cup` | `"0"` / `"1"` | Rounded joins |

#### Clipping bounds (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `cb_t` | float | Clipping bound top |
| `cb_b` | float | Clipping bound bottom |
| `cb_l` | float | Clipping bound left |
| `cb_r` | float | Clipping bound right |

#### White segment control (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `white_down_limit` | float | Lower brightness limit for white gaps (0--255) |
| `white_max_len` | float | Maximum white segment length |
| `white_min_const_len` | float | Minimum constant white segment length |
| `black_max_len` | float | Maximum black segment length |
| `black_min_constlen` | float | Minimum constant black segment length |

#### Miscellaneous (in `raw`)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `object_id` | int | Unique object ID |
| `caption` | string | Fill display name |
| `type` | int | Internal type code |
| `selected` | `"0"` / `"1"` | Whether fill is currently selected |
| `visible` | `"0"` / `"1"` | Whether fill is visible |
| `expanded` | `"0"` / `"1"` | Tree node expansion state |
| `locked` | `"0"` / `"1"` | Editing lock |
| `parity` | `"0"` / `"1"` | Stroke parity (alternating direction) |
| `crossed_dir` | `"0"` / `"1"` | Enable cross-hatching (strokes in both directions) |
| `random_continuity` | `"0"` / `"1"` | Randomise stroke continuity |
| `min_length` | float | Minimum stroke length before culling |
| `push_strength` | float | Stroke push/repulsion strength |

### Algorithm-specific attributes

Beyond the common set, individual fill types carry attributes specific to their algorithm. These are always available in `FillParams.raw`.

#### `FreeCurveStrokesTmpl` (handmade / trace)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `type_conv` | int | Sub-algorithm: `9`=trace, `0`=manual, `1`=blend, `2`=balanced |
| `averaning` | float | Curve averaging/smoothing passes |
| `is_clone_strokes` | `"true"` / `"false"` | Clone strokes from another fill |
| `is_expand_curves` | `"0"` / `"1"` | Expand curves to outlines |
| `is_imported` | `"0"` / `"1"` | Strokes were imported from external data |
| `is_ordered` | `"0"` / `"1"` | Maintain stroke ordering |

#### `HalftoneStrokesTmpl` (halftone)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `halftone_mode` | int | Grid mode: `0`=square, `1`=hexagonal |
| `cell_size` | float | Halftone cell width |
| `cell_height` | float | Halftone cell height |
| `morphing_mode` | int | Shape morphing: `0`=none, `1`=circle-to-square |
| `contrast` | float | Halftone contrast adjustment |
| `rotation_mode` | int | Cell rotation mode |
| `rotation_mul` | float | Cell rotation multiplier |
| `randomization_dot` | float | Random dot position offset |
| `base_x0`, `base_y0` | float | Grid origin X/Y |
| `base_x1`, `base_y1` | float | Grid end X/Y |

#### `ScribbleStrokesTmpl` (scribble)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `complexity` | float | Scribble path complexity |
| `curviness` | float | Scribble curve amplitude |
| `variety` | float | Stroke variation amount |
| `scribble_length` | float | Target scribble path length |
| `trace_density` | float | Tracing density |

#### `TracedAreaTmpl` (trace area)

| XML Attribute | Type | Description |
|---------------|------|-------------|
| `clearing_level` | float | Area clearing/simplification level |
| `detailing` | float | Detail preservation level |
| `mask_gen` | `"0"` / `"1"` | Generate mask from traced area |

#### `SourceStrokes` (source strokes)

Shares the same attribute set as `FreeCurveStrokesTmpl`. Source strokes represent imported vector paths that are treated as fill data.

#### `SigmoidStrokesTmpl` (wave)

Uses the common attribute set. Wave behaviour is controlled by `smoothness` (wave amplitude) and `interval` (wave period). Not observed in the current test data set; the tag name is defined in `FILL_TAG_MAP`.

#### `CircleStrokesTmpl` (circular), `RadialStrokesTmpl` (radial), `SpiralStrokesTmpl` (spiral)

These use the common attribute set. The tag name determines the geometric pattern. Not observed in the current test data; their fill tag names are defined in `FILL_TAG_MAP`.

#### `PeanoStrokesTmpl` (fractals)

Uses the common attribute set. The Peano space-filling curve behaviour is determined by `interval` (recursion scale) and `smoothness` (curve smoothing). No additional algorithm-specific attributes observed beyond the common set.

## Colour encoding

Vexy Lines uses two colour formats in XML attributes:

### Hex: `#AARRGGBB` (alpha first)

The native format stores alpha *before* the RGB channels -- the opposite of CSS convention.

| Raw value | Meaning | Parser output |
|-----------|---------|---------------|
| `#ff112233` | Opaque (`ff` alpha), RGB `112233` | `#112233` |
| `#80112233` | 50% alpha (`80`), RGB `112233` | `#11223380` |
| `#aabbcc` | Already 6-digit, no alpha | `#aabbcc` (pass-through) |

The parser normalises `#AARRGGBB` to standard `#RRGGBB` (stripping `ff` alpha) or `#RRGGBBAA` (moving non-opaque alpha to the end).

### Decimal ARGB integer

Some non-fill attributes (like `project_back_color`, `pen_color`, `selected_color`) store colour as a decimal integer encoding ARGB:

```
4294967295 = 0xFFFFFFFF = opaque white
4278190080 = 0xFF000000 = opaque black
```

Bit layout:

```
bits 31-24: alpha (0x00=transparent, 0xFF=opaque)
bits 23-16: red
bits 15-8:  green
bits 7-0:   blue
```

The parser's `_normalise_color()` function handles both formats and outputs `#RRGGBB` or `#RRGGBBAA`.

## Embedded images

### Source image: `<SourcePict>`

The original raster image used as input for the fill algorithms. Encoded with compression.

```xml
<SourcePict caption="__is_empty" width="1025" height="1025"
            object_id="927" type="16777729"
            h_resolution="4.1667" v_resolution="4.1667">
  <ImageData width="1025" height="1025" pict_format="jpg">
    base64-encoded-data
  </ImageData>
</SourcePict>
```

**`<SourcePict>` attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `width` | int | Image width in pixels |
| `height` | int | Image height in pixels |
| `caption` | string | Internal label (often `"__is_empty"`) |
| `object_id` | int | Unique ID |
| `type` | int | Internal type code (`16777729`) |
| `h_resolution` | float | Horizontal resolution (pixels per mm) |
| `v_resolution` | float | Vertical resolution (pixels per mm) |

**`<ImageData>` attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `width` | int | Image width in pixels |
| `height` | int | Image height in pixels |
| `pict_format` | string | Always `"jpg"` |

**Decoding the image data:**

```
base64 decode  ->  [ 4-byte big-endian uint32: uncompressed size ] [ zlib-compressed JPEG ]
                                     |                                        |
                                     v                                        v
                          used for validation              zlib.decompress() -> raw JPEG bytes
```

In Python:

```python
import base64, struct, zlib

raw = base64.b64decode(image_data_text)
expected_size = struct.unpack(">I", raw[:4])[0]
jpeg_bytes = zlib.decompress(raw[4:])
```

### Preview image: `<PreviewDoc>`

The rendered preview thumbnail. No compression wrapper -- just base64-encoded PNG.

```xml
<PreviewDoc width="984" height="984"
            pict_format="png" pict_compressed="0">
  base64-encoded-PNG
</PreviewDoc>
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `width` | int | Preview width in pixels |
| `height` | int | Preview height in pixels |
| `pict_format` | string | Always `"png"` |
| `pict_compressed` | `"0"` / `"1"` | Compression flag (always `"0"` in observed files) |

Decoding:

```python
import base64

png_bytes = base64.b64decode(preview_doc_text)
```

## `<MaskData>` element

Each layer can have an optional mask controlling which areas produce strokes.

```xml
<MaskData mask_type="1" invert_mask="0" tolerance="0"
          joined_mask="1" transsparency="0"
          mask_resolution_dpi="0" />
```

| Attribute | Type | Parsed | Description |
|-----------|------|--------|-------------|
| `mask_type` | int | yes | `0`=none, `1`=raster mask |
| `invert_mask` | `"0"` / `"1"` | yes | Invert the mask (strokes where mask is dark) |
| `tolerance` | float | yes | Edge tolerance for mask application |
| `joined_mask` | `"0"` / `"1"` | no | Join mask with adjacent layers |
| `transsparency` | float | no | Mask transparency (note: typo is in the format) |
| `mask_resolution_dpi` | int | no | Mask rasterisation DPI (`0`=use document DPI) |

## Mesh deformation

Layers can have warp meshes stored as `<row_grid_edge>` and `<col_grid_edge>` elements. These define a grid of control points that deform the fill output.

```xml
<row_grid_edge width="0" allocation_t="0.5"
               compressed="1" enbl_width_func="1"
               nodes_cnt="2" object_id="15073"
               pen_color="4278190080" type="16786432">
  <Nodes>base64-encoded-control-point-data</Nodes>
</row_grid_edge>
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `width` | float | Edge line width |
| `allocation_t` | float | Allocation parameter (0.0--1.0) |
| `compressed` | `"0"` / `"1"` | Whether `<Nodes>` data is compressed |
| `enbl_width_func` | `"0"` / `"1"` | Enable width function on this edge |
| `nodes_cnt` | int | Number of control point nodes |
| `object_id` | int | Unique ID for this edge |
| `pen_color` | decimal ARGB | Edge display colour (decimal integer) |
| `type` | int | Internal type code (`16786432`) |

The `<Nodes>` child contains base64-encoded binary control point data. When `compressed="1"`, the data is zlib-compressed after base64 decoding.

The parser captures grid edges as raw attribute dictionaries in `LayerInfo.grid_edges`:

```python
layer.grid_edges[0]
# {"type": "row_grid_edge", "width": "0", "allocation_t": "0.5", ...}
```

Rows define horizontal grid lines; columns define vertical grid lines. Together they form the deformation mesh.

## Href references

Some elements use `href_id` to reference objects defined elsewhere in the tree. These are lightweight pointer nodes -- they carry only `href_id` and `type` attributes with no children.

```xml
<FreeMesh type="16793857" href_id="936" />
<LrSection type="16777602" href_id="5" />
<SourcePict type="16777729" href_id="927">
```

The parser detects href elements via the presence of `href_id` and skips them. They appear in the `<Document>` element's internal `<model>` tree (a mirror of the layer tree used by the app's rendering engine).

## Internal elements (ignored by parser)

| Element | Description |
|---------|-------------|
| `<form_data>` / `<data>` | Internal form/bezier path data. Present on `<Project>`, `<LrSection>`, `<FreeMesh>`, and fill elements. |
| `<Workspace>` | Viewport state: scroll position, zoom, visibility toggles. |
| `<Images>` | Image container inside `<Document>`. |
| `<model>` | Internal rendering model (contains href copies of the layer tree). |
| `<doc_pict>` | Internal document picture reference. |

## Complete example

A minimal but structurally complete `.lines` file:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Project caption="Example" version="3.0.1" app="vexylines" dpi="300"
         object_id="1" expanded="1" type="16777602">
  <Objects>
    <LrSection caption="Background" object_id="2" expanded="1"
               type="16777602">
      <Objects>
        <FreeMesh caption="Lines Layer" object_id="10" visible="1"
                  type="16793857" thickness_mul="1" interval_mul="1">
          <Objects>
            <LinearStrokesTmpl caption="Linear" object_id="100"
                color_name="#ff000000" interval="2.28" angle="40"
                thick_gap="0" base_width="0.16" smoothness="0"
                uplimit="0" downlimit="255" multiplier="1"
                dispersion="0" shear="0" vert_disp="0"
                enbl_width="1" width_mode="0" smooth_width="2"
                enbl_basrelief="0" bsrf_rise="1" bsrf_smoothness="2"
                enbl_dotted="0" null_in_cut="1" null_tails_count="1"
                channel_invert="0" channel_mode="0" color_mode="3"
                crossed_dir="1" type="16781569" />
          </Objects>
          <MaskData mask_type="1" invert_mask="0" tolerance="0" />
          <row_grid_edge width="0" allocation_t="0.5" compressed="1"
                         nodes_cnt="2" object_id="200"
                         pen_color="4278190080" type="16786432"
                         enbl_width_func="1">
            <Nodes>base64data</Nodes>
          </row_grid_edge>
          <col_grid_edge width="0" allocation_t="0.5" compressed="1"
                         nodes_cnt="2" object_id="201"
                         pen_color="4278190080" type="16786432"
                         enbl_width_func="1">
            <Nodes>base64data</Nodes>
          </col_grid_edge>
        </FreeMesh>
      </Objects>
    </LrSection>
  </Objects>
  <SourcePict caption="__is_empty" width="1025" height="1025"
              object_id="900" type="16777729"
              h_resolution="4.1667" v_resolution="4.1667">
    <ImageData width="1025" height="1025" pict_format="jpg">
      <!-- base64( uint32-BE-uncompressed-size + zlib(JPEG) ) -->
    </ImageData>
  </SourcePict>
  <Document width_mm="86.78" height_mm="86.78" dpi="300"
            thicknessMin="0" thicknessMax="5.66"
            intervalMin="0.28" intervalMax="5.66"
            project_back_color="4294967295" type="16777219" />
  <PreviewDoc width="984" height="984"
              pict_format="png" pict_compressed="0">
    <!-- base64( raw PNG ) -->
  </PreviewDoc>
</Project>
```

## Fill type internal type codes

Each fill tag has an associated `type` attribute containing an integer type code. These are not used by the parser but are part of the format:

| Fill Tag | `type` value |
|----------|-------------|
| `LinearStrokesTmpl` | `16781569` |
| `HalftoneStrokesTmpl` | `16781574` |
| `PeanoStrokesTmpl` | `16781576` |
| `TracedAreaTmpl` | `16781577` |
| `FreeCurveStrokesTmpl` | `16781578` |
| `ScribbleStrokesTmpl` | `16781579` |
| `SourceStrokes` | `16781578` |
