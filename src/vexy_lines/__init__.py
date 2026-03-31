# this_file: vexy-lines-py/src/vexy_lines/__init__.py
"""Parse Vexy Lines ``.lines`` files in pure Python — no app required.

Read the layer tree, extract fill parameters, and decode embedded images
from any ``.lines`` file on any platform.

Example::

    from vexy_lines import parse, GroupInfo, LayerInfo

    doc = parse("artwork.lines")
    print(doc.caption, doc.dpi)  # "My Art" 300

    for node in doc.groups:
        if isinstance(node, GroupInfo):
            for layer in node.children:
                if isinstance(layer, LayerInfo):
                    for fill in layer.fills:
                        print(fill.params.fill_type, fill.params.color)
                        # "linear" "#1a2b3c"

    # Save the embedded source image to disk
    if doc.source_image_data:
        with open("source.jpg", "wb") as f:
            f.write(doc.source_image_data)
"""

from __future__ import annotations

from vexy_lines.editor import replace_source_image
from vexy_lines.parser import extract_preview_image, extract_source_image, parse, parse_string
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
    "replace_source_image",
    "extract_source_image",
    "parse",
    "parse_string",
]
