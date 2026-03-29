# this_file: vexy-lines-py/src/vexy_lines/parser.py
"""Parser for Vexy Lines .lines files.

.lines files are XML documents containing the full project structure:
layer tree (groups, layers, fills), source image, preview image, and
document properties. This module parses them into typed dataclasses
without requiring the Vexy Lines app.

The embedded source image is base64 -> 4-byte BE size header -> zlib -> JPEG.
The preview image is base64 -> raw PNG.
"""

from __future__ import annotations

import base64
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

from loguru import logger

from vexy_lines.types import (
    FILL_TAGS,
    FILL_TAG_MAP,
    DocumentProps,
    FillNode,
    FillParams,
    GroupInfo,
    LayerInfo,
    LinesDocument,
    MaskInfo,
)

# ---------------------------------------------------------------------------
# Private constants
# ---------------------------------------------------------------------------

# Colour constants
_HEX_COLOR_LEN = 8  # Length of #AARRGGBB hex part (without #)
_ALPHA_OPAQUE = 0xFF  # Fully opaque alpha channel value

# FreeCurveStrokesTmpl type_conv value that maps to "trace" fill type.
_TYPE_CONV_TRACE = 9

# Minimum byte count for a valid base64-decoded SourcePict payload
# (4-byte size header + at least 1 byte of zlib data).
_MIN_SOURCE_PICT_BYTES = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_float(attrib: dict[str, str], key: str, default: float = 0.0) -> float:
    """Safely parse a float from an XML attribute dict.

    Returns *default* when the key is absent or the value is not numeric.
    """
    val = attrib.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _get_int(attrib: dict[str, str], key: str, default: int = 0) -> int:
    """Safely parse an int from an XML attribute dict.

    Returns *default* when the key is absent or the value is not numeric.
    """
    val = attrib.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        # Handle float strings like "300.0" by truncating.
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default


def _normalise_color(raw_color: str) -> str:
    """Normalise a Vexy Lines colour string to ``#RRGGBB`` or ``#RRGGBBAA``.

    Input formats seen in ``.lines`` files:

    * ``#ffRRGGBB`` -- fully opaque, the ``ff`` alpha prefix is stripped.
    * ``#RRGGBBAA`` -- eight hex digits with trailing alpha, kept as-is.
    * ``#RRGGBB``  -- six hex digits, kept as-is.
    * Decimal ARGB int (e.g. ``4278190080``) -- converted.
    * Empty / missing -- returns ``#000000``.
    """
    if not raw_color:
        return "#000000"

    raw_color = raw_color.strip()

    # Hex format
    if raw_color.startswith("#"):
        hex_part = raw_color[1:]
        if len(hex_part) == _HEX_COLOR_LEN:
            alpha = hex_part[:2].lower()
            rgb = hex_part[2:]
            if alpha == "ff":
                return f"#{rgb}"
            # Non-ff alpha: reorder to #RRGGBBAA
            return f"#{rgb}{alpha}"
        # Already 6 digits or other length -- pass through.
        return raw_color

    # Decimal ARGB integer (e.g. from project_back_color)
    try:
        argb = int(raw_color)
        a = (argb >> 24) & 0xFF
        r = (argb >> 16) & 0xFF
        g = (argb >> 8) & 0xFF
        b = argb & 0xFF
        if a == _ALPHA_OPAQUE:
            return f"#{r:02x}{g:02x}{b:02x}"
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
    except (ValueError, TypeError):
        return "#000000"


def _is_href(elem: ET.Element) -> bool:
    """Return True if *elem* is a lightweight href reference (not a real node).

    Href elements carry only ``href_id`` and ``type`` attributes with no
    children -- they reference another element elsewhere in the tree.
    """
    return "href_id" in elem.attrib


def _resolve_fill_type(xml_tag: str, attrib: dict[str, str]) -> str:
    """Determine the fill type string for a fill element.

    For ``FreeCurveStrokesTmpl``, the ``type_conv`` attribute refines the
    type.  ``type_conv=9`` maps to "trace"; other values default to the
    generic tag mapping (also "trace" for that tag).
    """
    base = FILL_TAG_MAP.get(xml_tag, xml_tag)

    if xml_tag == "FreeCurveStrokesTmpl":
        type_conv = _get_int(attrib, "type_conv", default=-1)
        if type_conv == _TYPE_CONV_TRACE:
            return "trace"
        # Other type_conv values: 2 = "balanced" variant, etc.
        # Keep the base mapping ("trace") as the canonical type.
        return base

    return base


# ---------------------------------------------------------------------------
# Binary decoders
# ---------------------------------------------------------------------------


def _decode_source_pict(elem: ET.Element) -> bytes:
    """Decode the ``<SourcePict>`` element into JPEG bytes.

    Encoding: the ``<ImageData>`` child holds base64 text.  After decoding,
    the first 4 bytes are a big-endian uint32 giving the *uncompressed*
    size, followed by a zlib-compressed JPEG payload.

    Raises:
        ValueError: If the element structure is unexpected or decoding fails.
    """
    image_data_elem = elem.find("ImageData")
    if image_data_elem is None or not image_data_elem.text:
        msg = "SourcePict has no ImageData child or it is empty"
        raise ValueError(msg)

    raw = base64.b64decode(image_data_elem.text)
    if len(raw) < _MIN_SOURCE_PICT_BYTES:
        msg = f"SourcePict ImageData too short ({len(raw)} bytes)"
        raise ValueError(msg)

    # 4-byte big-endian uncompressed size header, then zlib payload.
    _expected_size = struct.unpack(">I", raw[:4])[0]
    try:
        decompressed = zlib.decompress(raw[4:])
    except zlib.error as exc:
        msg = f"Failed to zlib-decompress source image: {exc}"
        raise ValueError(msg) from exc

    logger.debug(f"Decoded source image: {len(decompressed)} bytes (expected {_expected_size})")
    return decompressed


def _decode_preview_doc(elem: ET.Element) -> bytes:
    """Decode the ``<PreviewDoc>`` element into PNG bytes.

    The element text is base64-encoded raw PNG data (no compression wrapper).

    Raises:
        ValueError: If the element text is missing or decoding fails.
    """
    if not elem.text:
        msg = "PreviewDoc element has no text content"
        raise ValueError(msg)

    raw = base64.b64decode(elem.text)
    logger.debug(f"Decoded preview image: {len(raw)} bytes")
    return raw


# ---------------------------------------------------------------------------
# Element parsers
# ---------------------------------------------------------------------------


def _parse_fill(elem: ET.Element) -> FillNode:
    """Parse a fill element into a :class:`~vexy_lines.types.FillNode`."""
    attrib = dict(elem.attrib)
    xml_tag = elem.tag
    fill_type = _resolve_fill_type(xml_tag, attrib)

    params = FillParams(
        fill_type=fill_type,
        color=_normalise_color(attrib.get("color_name", "")),
        interval=_get_float(attrib, "interval"),
        angle=_get_float(attrib, "angle"),
        thickness=_get_float(attrib, "thick_gap"),
        thickness_min=_get_float(attrib, "base_width"),
        smoothness=_get_float(attrib, "smoothness"),
        uplimit=_get_float(attrib, "uplimit"),
        downlimit=_get_float(attrib, "downlimit", default=255.0),
        multiplier=_get_float(attrib, "multiplier", default=1.0),
        base_width=_get_float(attrib, "base_width"),
        dispersion=_get_float(attrib, "dispersion"),
        shear=_get_float(attrib, "shear"),
        raw=attrib,
    )

    return FillNode(
        xml_tag=xml_tag,
        caption=attrib.get("caption", ""),
        params=params,
        object_id=_get_int(attrib, "object_id") if "object_id" in attrib else None,
    )


def _parse_mask(elem: ET.Element) -> MaskInfo:
    """Parse a ``<MaskData>`` element into a :class:`~vexy_lines.types.MaskInfo`."""
    attrib = elem.attrib
    return MaskInfo(
        mask_type=_get_int(attrib, "mask_type"),
        invert=attrib.get("invert_mask", "0") != "0",
        tolerance=_get_float(attrib, "tolerance"),
    )


def _parse_layer(elem: ET.Element) -> LayerInfo:
    """Parse a ``<FreeMesh>`` element into a :class:`~vexy_lines.types.LayerInfo`.

    Child ``<Objects>`` contains the fill elements.  ``<MaskData>`` provides
    the optional mask.  ``<row_grid_edge>`` and ``<col_grid_edge>`` supply
    mesh deformation data.
    """
    attrib = elem.attrib
    caption = attrib.get("caption", "")
    object_id = _get_int(attrib, "object_id") if "object_id" in attrib else None
    visible = attrib.get("visible", "1") != "0"

    fills: list[FillNode] = []
    mask: MaskInfo | None = None
    grid_edges: list[dict[str, str]] = []

    for child in elem:
        tag = child.tag

        if tag == "Objects":
            for fill_elem in child:
                if _is_href(fill_elem):
                    continue
                if fill_elem.tag in FILL_TAGS:
                    fills.append(_parse_fill(fill_elem))

        elif tag == "MaskData":
            mask = _parse_mask(child)

        elif tag in ("row_grid_edge", "col_grid_edge"):
            grid_edges.append({"type": tag, **dict(child.attrib)})

    return LayerInfo(
        caption=caption,
        object_id=object_id,
        visible=visible,
        mask=mask,
        fills=fills,
        grid_edges=grid_edges,
    )


def _parse_group(elem: ET.Element) -> GroupInfo:
    """Parse an ``<LrSection>`` element into a :class:`~vexy_lines.types.GroupInfo`.

    Groups contain an ``<Objects>`` child whose children are either
    ``FreeMesh`` (layers) or nested ``LrSection`` (sub-groups).
    """
    attrib = elem.attrib
    caption = attrib.get("caption", "")
    object_id = _get_int(attrib, "object_id") if "object_id" in attrib else None
    expanded = attrib.get("expanded", "1") != "0"

    children: list[GroupInfo | LayerInfo] = []
    objects_elem = elem.find("Objects")
    if objects_elem is not None:
        children = _parse_objects(objects_elem)

    return GroupInfo(
        caption=caption,
        object_id=object_id,
        expanded=expanded,
        children=children,
    )


def _parse_objects(objects_elem: ET.Element) -> list[GroupInfo | LayerInfo]:
    """Parse the children of an ``<Objects>`` element into groups and layers.

    Skips href references and elements that are neither groups nor layers.
    """
    result: list[GroupInfo | LayerInfo] = []

    for child in objects_elem:
        if _is_href(child):
            continue

        tag = child.tag
        if tag == "LrSection":
            result.append(_parse_group(child))
        elif tag == "FreeMesh":
            result.append(_parse_layer(child))
        # Other tags at this level (form_data, etc.) are silently skipped.

    return result


def _parse_document_props(doc_elem: ET.Element) -> DocumentProps:
    """Parse the ``<Document>`` element into :class:`~vexy_lines.types.DocumentProps`."""
    attrib = doc_elem.attrib
    return DocumentProps(
        width_mm=_get_float(attrib, "width_mm"),
        height_mm=_get_float(attrib, "height_mm"),
        dpi=_get_int(attrib, "dpi", default=300),
        thickness_min=_get_float(attrib, "thicknessMin"),
        thickness_max=_get_float(attrib, "thicknessMax"),
        interval_min=_get_float(attrib, "intervalMin"),
        interval_max=_get_float(attrib, "intervalMax"),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(path: str | Path) -> LinesDocument:
    """Parse a ``.lines`` file and return a :class:`~vexy_lines.types.LinesDocument`.

    This is the main entry point.  It reads the XML, extracts the layer
    tree, document properties, and optionally decodes the embedded source
    and preview images.

    Args:
        path: Path to the ``.lines`` file.

    Returns:
        Fully populated :class:`~vexy_lines.types.LinesDocument`.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ET.ParseError: If the file is not valid XML.
    """
    path = Path(path)
    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)

    logger.debug(f"Parsing .lines file: {path}")
    tree = ET.parse(path)  # noqa: S314
    root = tree.getroot()

    # Root <Project> attributes
    caption = root.attrib.get("caption", "")
    version = root.attrib.get("version", "")
    dpi = _get_int(root.attrib, "dpi", default=300)

    # Layer tree
    groups: list[GroupInfo | LayerInfo] = []
    objects_elem = root.find("Objects")
    if objects_elem is not None:
        groups = _parse_objects(objects_elem)

    # Document properties
    props = DocumentProps()
    doc_elem = root.find("Document")
    if doc_elem is not None:
        props = _parse_document_props(doc_elem)

    # Source image (JPEG inside base64 + zlib)
    source_image_data: bytes | None = None
    source_pict = root.find("SourcePict")
    if source_pict is not None:
        try:
            source_image_data = _decode_source_pict(source_pict)
        except (ValueError, Exception) as exc:  # noqa: BLE001
            logger.warning(f"Could not decode source image: {exc}")

    # Preview image (PNG inside base64)
    preview_image_data: bytes | None = None
    preview_doc = root.find("PreviewDoc")
    if preview_doc is not None:
        try:
            preview_image_data = _decode_preview_doc(preview_doc)
        except (ValueError, Exception) as exc:  # noqa: BLE001
            logger.warning(f"Could not decode preview image: {exc}")

    doc = LinesDocument(
        caption=caption,
        version=version,
        dpi=dpi,
        props=props,
        groups=groups,
        source_image_data=source_image_data,
        preview_image_data=preview_image_data,
    )

    _log_summary(doc)
    return doc


def _log_summary(doc: LinesDocument) -> None:
    """Log a brief summary of the parsed document."""
    n_groups = 0
    n_layers = 0
    n_fills = 0

    def _count(nodes: list[GroupInfo | LayerInfo]) -> None:
        nonlocal n_groups, n_layers, n_fills
        for node in nodes:
            if isinstance(node, GroupInfo):
                n_groups += 1
                _count(node.children)
            elif isinstance(node, LayerInfo):
                n_layers += 1
                n_fills += len(node.fills)

    _count(doc.groups)
    logger.debug(
        f"Parsed '{doc.caption}' v{doc.version}: "
        f"{n_groups} groups, {n_layers} layers, {n_fills} fills, "
        f"source_image={'yes' if doc.source_image_data else 'no'}, "
        f"preview={'yes' if doc.preview_image_data else 'no'}"
    )


def extract_source_image(path: str | Path, output: str | Path) -> Path:
    """Parse a ``.lines`` file and save its embedded source image as JPEG.

    Args:
        path: Path to the ``.lines`` file.
        output: Destination path for the JPEG file.

    Returns:
        The resolved output :class:`~pathlib.Path`.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If no source image is embedded in the file.
    """
    doc = parse(path)
    if doc.source_image_data is None:
        msg = f"No source image found in {path}"
        raise ValueError(msg)

    output = Path(output)
    output.write_bytes(doc.source_image_data)
    logger.info(f"Saved source image ({len(doc.source_image_data)} bytes) -> {output}")
    return output


def extract_preview_image(path: str | Path, output: str | Path) -> Path:
    """Parse a ``.lines`` file and save its embedded preview image as PNG.

    Args:
        path: Path to the ``.lines`` file.
        output: Destination path for the PNG file.

    Returns:
        The resolved output :class:`~pathlib.Path`.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If no preview image is embedded in the file.
    """
    doc = parse(path)
    if doc.preview_image_data is None:
        msg = f"No preview image found in {path}"
        raise ValueError(msg)

    output = Path(output)
    output.write_bytes(doc.preview_image_data)
    logger.info(f"Saved preview image ({len(doc.preview_image_data)} bytes) -> {output}")
    return output
