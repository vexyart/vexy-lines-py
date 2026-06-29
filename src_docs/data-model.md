# Data Model

`vexy-lines-py` represents a parsed `.lines` document as a tree of typed
dataclasses.  All types are importable from `vexy_lines` directly.

## Type hierarchy

```
LinesDocument
├── caption: str                    project name
├── version: str                    app version that wrote the file
├── dpi: int                        root-level DPI (from <Project dpi="...">)
├── props: DocumentProps            canvas dimensions and stroke limits
├── groups: list[GroupInfo | LayerInfo]   top-level layer tree
├── source_image_data: bytes | None first document-scope JPEG (convenience)
├── source_images: list[SourceImageInfo]  all decoded <SourcePict> payloads
└── preview_image_data: bytes | None decoded PNG preview thumbnail

DocumentProps
├── width_mm: float
├── height_mm: float
├── dpi: int
├── thickness_min: float
├── thickness_max: float
├── interval_min: float
└── interval_max: float

GroupInfo                           maps to <LrSection>
├── caption: str
├── object_id: int | None
├── expanded: bool
└── children: list[GroupInfo | LayerInfo]   recursive

LayerInfo                           maps to <FreeMesh>
├── caption: str
├── object_id: int | None
├── visible: bool
├── mask: MaskInfo | None
├── fills: list[FillNode]
└── grid_edges: list[dict[str, str]]   raw row_grid_edge / col_grid_edge attrs

FillNode                            one fill algorithm instance
├── xml_tag: str                    original XML element name
├── caption: str
├── object_id: int | None
├── params: FillParams
└── image_filters: list[ImageFilterEntry]

FillParams
├── fill_type: str                  e.g. "linear", "circular", "handmade"
├── color: str                      normalised hex: #RRGGBB or #RRGGBBAA
├── interval: float                 line spacing in mm
├── angle: float                    stroke angle in degrees
├── thickness: float                XML thick_gap
├── thickness_min: float            XML base_width
├── smoothness: float
├── uplimit: float                  upper brightness threshold (0–255)
├── downlimit: float                lower brightness threshold (0–255)
├── multiplier: float               width multiplier
├── base_width: float               same source as thickness_min
├── dispersion: float               random perpendicular offset
├── shear: float                    shear distortion angle in degrees
└── raw: dict[str, str]             all XML attributes (unmodified)

ImageFilterEntry                    one entry in a fill's filter chain
├── type_id: int                    upstream numeric type (0–9)
├── name: str                       MCP-compatible name e.g. "brightness"
├── params: dict[str, bool|int|float|str]   typed parameter values
└── raw: dict[str, str]             original XML attributes

MaskInfo                            from <MaskData>
├── mask_type: int                  0=none, 1=raster
├── invert: bool
└── tolerance: float

SourceImageInfo                     one decoded <SourcePict> payload
├── index: int                      1-based position in source_images list
├── data: bytes                     decoded JPEG bytes
├── scope: str                      "document" or "group"
├── caption: str
├── object_id: int | None
├── owner_caption: str
├── owner_path: str                 slash-separated group path
├── width: int | None               pixels
└── height: int | None              pixels
```

## Walking the layer tree

`LinesDocument.groups` is a flat list of top-level nodes. Each node is either
a `GroupInfo` (with its own `children` list) or a `LayerInfo` (with a `fills`
list).  Groups nest recursively.

```python
from vexy_lines import parse, GroupInfo, LayerInfo

doc = parse("artwork.lines")

def walk(nodes, depth=0):
    indent = "  " * depth
    for node in nodes:
        if isinstance(node, GroupInfo):
            print(f"{indent}[group] {node.caption!r}")
            walk(node.children, depth + 1)
        elif isinstance(node, LayerInfo):
            vis = "" if node.visible else " (hidden)"
            print(f"{indent}[layer] {node.caption!r}{vis}")
            for fill in node.fills:
                p = fill.params
                print(f"{indent}  [{p.fill_type}] {p.color}")

walk(doc.groups)
```

## Fill type names

The `fill_type` field on `FillParams` is the MCP-compatible algorithm name:

| `fill_type` | XML element |
|---|---|
| `"linear"` | `LinearStrokesTmpl` |
| `"wave"` | `SigmoidStrokesTmpl` |
| `"circular"` | `CircleStrokesTmpl` |
| `"radial"` | `RadialStrokesTmpl` |
| `"spiral"` | `SpiralStrokesTmpl` |
| `"scribble"` | `ScribbleStrokesTmpl` |
| `"halftone"` | `HalftoneStrokesTmpl` |
| `"handmade"` | `FreeCurveStrokesTmpl` (default) |
| `"trace"` | `FreeCurveStrokesTmpl` with `type_conv="9"`, or `TracedAreaTmpl` |
| `"fractals"` | `PeanoStrokesTmpl` |
| `"source_strokes"` | `SourceStrokes` |

The complete mapping is in `vexy_lines.types.FILL_TAG_MAP`.

## Image filter chain

Each fill can carry an ordered list of `ImageFilterEntry` objects that are
applied before stroke rendering.  Filter IDs 0–9 map to named operations:

```python
from vexy_lines.types import IMAGE_FILTER_TYPE_MAP
# {0: "brightness", 1: "contrast", 2: "blur", 3: "sharpen",
#  4: "levels", 5: "shadows_highlights", 6: "invert",
#  7: "remove_background", 8: "color", 9: "gradient"}
```

Parameter values are typed: `bool` for `"inverted"`, `int` for `"left"` /
`"right"` / `"direction"`, `str` for `"color"`, `float` for everything else.

```python
for fill in layer.fills:
    for f in fill.image_filters:
        print(f.name, f.params)
        # "brightness" {"value": -12.5}
        # "levels"     {"left": 12, "right": 224}
```

## Source images

A `.lines` file can embed more than one source image: one at document level
and one per group.  `LinesDocument.source_images` lists them all:

```python
for img in doc.source_images:
    print(img.index, img.scope, img.owner_path,
          img.width, img.height, len(img.data), "bytes")
    # 1  document  ""          1025 1025  48392 bytes
    # 2  group     "Background"  512  512  12000 bytes
```

`LinesDocument.source_image_data` is a convenience shortcut to the first
document-scope image's bytes (or `None` when absent).

## Accessing raw attributes

Every `FillParams.raw` dict and every `LayerInfo.grid_edges` entry holds the
unmodified XML attribute strings for attributes the parser does not promote to
named fields.  This is the escape hatch for algorithm-specific or
undocumented parameters:

```python
fill.params.raw.get("vert_disp")        # "0.5"
fill.params.raw.get("crossed_dir")      # "1"
layer.grid_edges[0]["allocation_t"]     # "0.5"
```
