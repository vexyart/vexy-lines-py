# this_file: vexy-lines-py/src/vexy_lines/types.py
"""Data types and constants for the Vexy Lines ``.lines`` file format.

Dataclasses and lookup tables used by the parser.  Import from here
when you need the types without the parsing machinery.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FILL_TAG_MAP: dict[str, str] = {
    "LinearStrokesTmpl": "linear",
    "SigmoidStrokesTmpl": "wave",
    "CircleStrokesTmpl": "circular",
    "RadialStrokesTmpl": "radial",
    "SpiralStrokesTmpl": "spiral",
    "ScribbleStrokesTmpl": "scribble",
    "HalftoneStrokesTmpl": "halftone",
    "FreeCurveStrokesTmpl": "handmade",
    "PeanoStrokesTmpl": "fractals",
    "TracedAreaTmpl": "trace",
    "SourceStrokes": "source_strokes",
}
"""XML element tag → human-readable fill type name.

Names match the Vexy Lines MCP server fill type identifiers exactly.
``FreeCurveStrokesTmpl`` with ``type_conv=9`` is resolved to ``"trace"``
at parse time by :func:`~vexy_lines.parser._resolve_fill_type`.
"""

FILL_TAGS: set[str] = set(FILL_TAG_MAP)
"""All recognised fill element tag names (keys of :data:`FILL_TAG_MAP`)."""

NUMERIC_PARAMS: list[str] = [
    "interval",
    "angle",
    "thick_gap",
    "smoothness",
    "uplimit",
    "downlimit",
    "multiplier",
    "base_width",
    "dispersion",
    "vert_disp",
    "shear",
]
"""XML attribute names whose values are numeric and can be interpolated.

Most map directly to :class:`FillParams` fields; ``vert_disp`` is only
available in :attr:`FillParams.raw` (no dedicated field).
"""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FillParams:
    """Numeric and colour parameters for a single fill algorithm.

    Attributes:
        fill_type: Algorithm name, e.g. ``"linear"``, ``"circular"``.
        color: Normalised hex colour — ``#RRGGBB`` or ``#RRGGBBAA``.
        interval: Line spacing in mm.
        angle: Stroke angle in degrees.
        thickness: Stroke thickness (XML ``thick_gap``).
        thickness_min: Minimum thickness (XML ``base_width``).
        smoothness: Curve smoothness factor.
        uplimit: Upper brightness threshold (0–255).
        downlimit: Lower brightness threshold (0–255).
        multiplier: Width multiplier applied to strokes.
        base_width: Baseline stroke width in mm (same source as ``thickness_min``).
        dispersion: Random perpendicular offset applied to strokes.
        shear: Shear distortion angle in degrees.
        raw: All XML attributes on the fill element, including ``vert_disp``
            and any algorithm-specific keys not promoted to named fields.
    """

    fill_type: str
    color: str
    interval: float = 0.0
    angle: float = 0.0
    thickness: float = 0.0
    thickness_min: float = 0.0
    smoothness: float = 0.0
    uplimit: float = 0.0
    downlimit: float = 255.0
    multiplier: float = 1.0
    base_width: float = 0.0
    dispersion: float = 0.0
    shear: float = 0.0
    raw: dict[str, str] = field(default_factory=dict)


@dataclass
class MaskInfo:
    """Mask settings from a ``<MaskData>`` element.

    Attributes:
        mask_type: Mask mode — ``0`` = none, ``1`` = raster mask.
        invert: ``True`` when the mask is inverted (XML ``invert_mask != "0"``).
        tolerance: Edge tolerance for mask application.
    """

    mask_type: int = 0
    invert: bool = False
    tolerance: float = 0.0


@dataclass
class FillNode:
    """A single fill algorithm instance inside a layer.

    Attributes:
        xml_tag: Original XML tag, e.g. ``"LinearStrokesTmpl"``.
        caption: User-visible fill name as shown in the Vexy Lines UI.
        params: Parsed fill parameters including type, colour, and numerics.
        object_id: Unique object ID, or ``None`` when the element is an href reference.
    """

    xml_tag: str
    caption: str
    params: FillParams
    object_id: int | None = None


@dataclass
class LayerInfo:
    """A single layer (``<FreeMesh>`` element) with its fills and optional mask.

    Attributes:
        caption: User-visible layer name.
        object_id: Unique object ID, or ``None`` for href references.
        visible: ``False`` when the layer is hidden in the Vexy Lines UI.
        mask: Mask settings, or ``None`` if no mask is applied.
        fills: Ordered list of fill algorithms on this layer.
        grid_edges: Raw ``row_grid_edge`` / ``col_grid_edge`` attribute dicts
            describing mesh deformation applied to the layer.
    """

    caption: str
    object_id: int | None = None
    visible: bool = True
    mask: MaskInfo | None = None
    fills: list[FillNode] = field(default_factory=list)
    grid_edges: list[dict[str, str]] = field(default_factory=list)


@dataclass
class GroupInfo:
    """A group (``<LrSection>`` element) containing layers and/or sub-groups.

    Attributes:
        caption: User-visible group name.
        object_id: Unique object ID, or ``None`` for href references.
        expanded: ``False`` when the group is collapsed in the Vexy Lines UI.
        children: Ordered child nodes — each is a :class:`GroupInfo` or :class:`LayerInfo`.
    """

    caption: str
    object_id: int | None = None
    expanded: bool = True
    children: list[GroupInfo | LayerInfo] = field(default_factory=list)


@dataclass
class DocumentProps:
    """Canvas dimensions and stroke range limits from the ``<Document>`` element.

    Attributes:
        width_mm: Canvas width in millimetres.
        height_mm: Canvas height in millimetres.
        dpi: Document resolution in dots per inch.
        thickness_min: Minimum allowed stroke thickness (mm).
        thickness_max: Maximum allowed stroke thickness (mm).
        interval_min: Minimum allowed line spacing (mm).
        interval_max: Maximum allowed line spacing (mm).
    """

    width_mm: float = 0.0
    height_mm: float = 0.0
    dpi: int = 300
    thickness_min: float = 0.0
    thickness_max: float = 0.0
    interval_min: float = 0.0
    interval_max: float = 0.0


@dataclass
class LinesDocument:
    """Everything parsed from a ``.lines`` file.

    Attributes:
        caption: Project name (root ``<Project caption="...">``).
        version: Vexy Lines app version that created the file.
        dpi: Document resolution from the root ``<Project>`` element.
        props: Canvas dimensions and stroke limits from ``<Document>``.
        groups: Top-level layer tree; each entry is a :class:`GroupInfo`
            or :class:`LayerInfo`.
        source_image_data: Decoded JPEG bytes of the embedded source image,
            or ``None`` if absent.
        preview_image_data: Decoded PNG bytes of the embedded preview image,
            or ``None`` if absent.
    """

    caption: str = ""
    version: str = ""
    dpi: int = 300
    props: DocumentProps = field(default_factory=DocumentProps)
    groups: list[GroupInfo | LayerInfo] = field(default_factory=list)
    source_image_data: bytes | None = None
    preview_image_data: bytes | None = None
