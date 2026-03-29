# this_file: vexy-lines-py/src/vexy_lines/types.py
"""Data types and constants for the Vexy Lines .lines file format.

All dataclasses and lookup tables used by the parser are defined here
so that downstream code can import types without pulling in the full
parsing machinery.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FILL_TAG_MAP: dict[str, str] = {
    "LinearStrokesTmpl": "linear",
    "FreeCurveStrokesTmpl": "trace",
    "CircleStrokesTmpl": "circular",
    "RadialStrokesTmpl": "radial",
    "SpiralStrokesTmpl": "spiral",
    "HalftoneStrokesTmpl": "halftone",
    "WaveStrokesTmpl": "wave",
    "HandmadeStrokesTmpl": "handmade",
    "FractalStrokesTmpl": "fractals",
    "ScribbleStrokesTmpl": "scribble",
    "PeanoStrokesTmpl": "peano",
    "SigmoidStrokesTmpl": "sigmoid",
    "TracedAreaTmpl": "trace_area",
    "SourceStrokes": "source_strokes",
}
"""Map from XML element tag to human-readable fill type name."""

FILL_TAGS: set[str] = set(FILL_TAG_MAP)
"""Set of all recognised fill element tag names."""

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
"""Fill attributes that are numeric and can be interpolated between values."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FillParams:
    """Parsed numeric and colour parameters for a single fill.

    Attributes:
        fill_type: Human-readable fill type (e.g. "linear", "circular").
        color: Normalised hex colour string (#RRGGBB or #RRGGBBAA).
        interval: Line spacing in mm.
        angle: Stroke angle in degrees.
        thickness: Stroke thickness (from ``thick_gap`` attribute).
        thickness_min: Minimum thickness (derived from ``base_width``).
        smoothness: Curve smoothness.
        uplimit: Upper brightness limit (0-255).
        downlimit: Lower brightness limit (0-255).
        multiplier: Width multiplier applied to strokes.
        base_width: Baseline stroke width in mm.
        dispersion: Random offset applied perpendicular to stroke direction.
        shear: Shear distortion angle in degrees.
        raw: Complete dict of all XML attributes on the fill element.
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
    """Layer mask metadata.

    Attributes:
        mask_type: Integer mask mode (0 = none, 1 = raster, etc.).
        invert: Whether the mask is inverted.
        tolerance: Mask tolerance value.
    """

    mask_type: int = 0
    invert: bool = False
    tolerance: float = 0.0


@dataclass
class FillNode:
    """A single fill inside a layer.

    Attributes:
        xml_tag: Original XML element tag (e.g. ``LinearStrokesTmpl``).
        caption: User-visible fill name.
        params: Parsed fill parameters.
        object_id: Unique object identifier, or ``None`` for href references.
    """

    xml_tag: str
    caption: str
    params: FillParams
    object_id: int | None = None


@dataclass
class LayerInfo:
    """A single layer (``FreeMesh`` element) with its fills and mask.

    Attributes:
        caption: User-visible layer name.
        object_id: Unique object identifier, or ``None`` for href references.
        visible: Whether the layer is visible in the viewport.
        mask: Optional mask information.
        fills: Ordered list of fills belonging to this layer.
        grid_edges: Raw grid edge dicts (row/col mesh deformation data).
    """

    caption: str
    object_id: int | None = None
    visible: bool = True
    mask: MaskInfo | None = None
    fills: list[FillNode] = field(default_factory=list)
    grid_edges: list[dict[str, str]] = field(default_factory=list)


@dataclass
class GroupInfo:
    """A group (``LrSection`` element) that may contain layers or sub-groups.

    Attributes:
        caption: User-visible group name.
        object_id: Unique object identifier, or ``None`` for href references.
        expanded: Whether the group is expanded in the UI.
        children: Ordered list of child groups and layers.
    """

    caption: str
    object_id: int | None = None
    expanded: bool = True
    children: list[GroupInfo | LayerInfo] = field(default_factory=list)


@dataclass
class DocumentProps:
    """Global document properties from the ``<Document>`` element.

    Attributes:
        width_mm: Document width in millimetres.
        height_mm: Document height in millimetres.
        dpi: Document resolution in dots per inch.
        thickness_min: Minimum stroke thickness (mm).
        thickness_max: Maximum stroke thickness (mm).
        interval_min: Minimum line interval (mm).
        interval_max: Maximum line interval (mm).
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
    """Top-level representation of a parsed ``.lines`` file.

    Attributes:
        caption: Project name.
        version: App version string that created the file.
        dpi: Document DPI from the root ``<Project>`` element.
        props: Parsed ``<Document>`` element properties.
        groups: Top-level layer tree (groups and layers).
        source_image_data: Decoded JPEG bytes of the source image, or ``None``.
        preview_image_data: Decoded PNG bytes of the preview image, or ``None``.
    """

    caption: str = ""
    version: str = ""
    dpi: int = 300
    props: DocumentProps = field(default_factory=DocumentProps)
    groups: list[GroupInfo | LayerInfo] = field(default_factory=list)
    source_image_data: bytes | None = None
    preview_image_data: bytes | None = None
