# this_file: vexy-lines-py/src/vexy_lines/__init__.py
"""vexy-lines-py: Pure-Python cross-platform parser for Vexy Lines .lines files.

Parse .lines vector art files, access the layer tree, and extract embedded
source and preview images -- all without requiring the Vexy Lines application.

Example::

    from vexy_lines import parse

    doc = parse("artwork.lines")
    print(doc.caption, doc.dpi)
    for group_or_layer in doc.groups:
        print(group_or_layer.caption)
"""

from __future__ import annotations

from vexy_lines.parser import extract_preview_image, extract_source_image, parse
from vexy_lines.types import (
    FILL_TAG_MAP,
    FILL_TAGS,
    NUMERIC_PARAMS,
    DocumentProps,
    FillNode,
    FillParams,
    GroupInfo,
    LayerInfo,
    LinesDocument,
    MaskInfo,
)

__all__ = [
    "FILL_TAG_MAP",
    "FILL_TAGS",
    "NUMERIC_PARAMS",
    "DocumentProps",
    "FillNode",
    "FillParams",
    "GroupInfo",
    "LayerInfo",
    "LinesDocument",
    "MaskInfo",
    "extract_preview_image",
    "extract_source_image",
    "parse",
]
