# .lines File Format

The `.lines` format is XML. Every Vexy Lines project saves to a single file containing the full layer tree, fill parameters, document properties, and optionally the source and preview images.

## Root element

```xml
<Project caption="My Art" version="4.0" dpi="300">
  <Document ... />
  <Objects> ... </Objects>
  <SourcePict> ... </SourcePict>
  <PreviewDoc> ... </PreviewDoc>
</Project>
```

| Attribute | Description |
|-----------|-------------|
| `caption` | Project name |
| `version` | Vexy Lines app version |
| `dpi` | Document resolution |

## Document element

Canvas dimensions and stroke limits.

```xml
<Document width_mm="210" height_mm="297" dpi="300"
          thicknessMin="0.1" thicknessMax="5.0"
          intervalMin="0.5" intervalMax="10.0" />
```

## Layer tree

The `<Objects>` element under `<Project>` contains the layer tree. Two node types:

### Groups (`<LrSection>`)

```xml
<LrSection caption="Group 1" object_id="100" expanded="1">
  <Objects>
    <!-- child layers and sub-groups -->
  </Objects>
</LrSection>
```

### Layers (`<FreeMesh>`)

```xml
<FreeMesh caption="Layer 1" object_id="200" visible="1">
  <Objects>
    <!-- fill elements -->
  </Objects>
  <MaskData mask_type="0" invert_mask="0" tolerance="0" />
  <row_grid_edge ... />
  <col_grid_edge ... />
</FreeMesh>
```

## Fill elements

Each fill is an XML element inside a layer's `<Objects>`. The tag name identifies the algorithm:

| XML Tag | Fill Type |
|---------|-----------|
| `LinearStrokesTmpl` | `linear` |
| `SigmoidStrokesTmpl` | `wave` |
| `CircleStrokesTmpl` | `circular` |
| `RadialStrokesTmpl` | `radial` |
| `SpiralStrokesTmpl` | `spiral` |
| `ScribbleStrokesTmpl` | `scribble` |
| `HalftoneStrokesTmpl` | `halftone` |
| `FreeCurveStrokesTmpl` | `handmade` (or `trace` when `type_conv="9"`) |
| `PeanoStrokesTmpl` | `fractals` |
| `TracedAreaTmpl` | `trace` |
| `SourceStrokes` | `source_strokes` |

A fill element looks like:

```xml
<LinearStrokesTmpl caption="Black lines" object_id="300"
    color_name="#ff1a2b3c" interval="2.5" angle="45"
    thick_gap="0.8" base_width="0.2" smoothness="0.5"
    uplimit="200" downlimit="30" multiplier="1.2"
    dispersion="0.1" shear="0" />
```

### Colour encoding

Colours in `.lines` use `#AARRGGBB` format (alpha first). The parser normalises to standard `#RRGGBB` or `#RRGGBBAA`:

| Raw value | Normalised |
|-----------|-----------|
| `#ff1a2b3c` | `#1a2b3c` (alpha `ff` = opaque, stripped) |
| `#801a2b3c` | `#1a2b3c80` (alpha `80` = 50%, moved to end) |
| `#1a2b3c` | `#1a2b3c` (already standard) |
| `4278190080` | Decimal ARGB integer, converted to hex |

### Special case: FreeCurveStrokesTmpl

`FreeCurveStrokesTmpl` doubles as both the "trace" and other curve-based algorithms. The `type_conv` attribute disambiguates: `type_conv="9"` means "trace". The parser handles this automatically.

## Embedded images

### Source image (`<SourcePict>`)

The original raster image, encoded as:

```
base64( 4-byte-BE-uint32-uncompressed-size + zlib(JPEG) )
```

Structure:

```xml
<SourcePict>
  <ImageData>base64-encoded-data</ImageData>
</SourcePict>
```

To decode: base64-decode the text, read the first 4 bytes as a big-endian uint32 (the uncompressed size), then zlib-decompress the remaining bytes to get raw JPEG.

### Preview image (`<PreviewDoc>`)

The rendered preview thumbnail, encoded as plain base64 PNG:

```xml
<PreviewDoc>base64-encoded-PNG</PreviewDoc>
```

To decode: base64-decode the text directly to get raw PNG bytes.

## Href references

Some elements use `href_id` attributes to reference objects defined elsewhere in the tree. These are pointer nodes, not real data. The parser skips them.

```xml
<LinearStrokesTmpl href_id="300" />
```

## Mesh deformation

Layers can have warp meshes stored as `<row_grid_edge>` and `<col_grid_edge>` elements with control point attributes. These describe the grid deformation applied to the layer's fill output.
