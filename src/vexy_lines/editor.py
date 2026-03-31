# this_file: vexy-lines-py/src/vexy_lines/editor.py
"""Editing operations for .lines files.

Currently supports replacing the embedded source image while preserving
all fill parameters, layers, groups, masks, and document settings.
"""

from __future__ import annotations

import base64
import io
import shutil
import struct
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET


def _encode_source_pict(jpeg_bytes: bytes) -> str:
    """Encode JPEG bytes into the .lines SourcePict format.

    Format: base64( 4-byte big-endian uint32 uncompressed_size + zlib(jpeg_bytes) )
    """
    compressed = zlib.compress(jpeg_bytes)
    header = struct.pack(">I", len(jpeg_bytes))
    return base64.b64encode(header + compressed).decode("ascii")


def _image_to_jpeg_bytes(image_path: Path) -> tuple[bytes, int, int]:
    """Load an image file and return (jpeg_bytes, width, height).

    Converts PNG/other formats to JPEG. Returns the JPEG bytes and dimensions.
    """
    from PIL import Image as PILImage

    with PILImage.open(image_path) as img:
        width, height = img.size
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return buf.getvalue(), width, height


def replace_source_image(
    lines_path: str | Path,
    new_image_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Replace the source image in a .lines file, writing to a new file.

    Parses the XML, finds the canonical ``<SourcePict>`` element (direct child
    of root ``<Project>``), replaces its ``<ImageData>`` content with the new
    image, and writes the result to *output_path*. All fill parameters, layers,
    groups, masks, and document settings are preserved byte-for-byte.

    The new image is converted to JPEG if it isn't already (the .lines format
    requires JPEG for source images).

    Args:
        lines_path: Path to the source ``.lines`` file (template).
        new_image_path: Path to the replacement image (JPEG, PNG, etc.).
        output_path: Where to write the modified ``.lines`` file.

    Returns:
        The resolved output path.

    Raises:
        FileNotFoundError: If either input file doesn't exist.
        ValueError: If the .lines file has no ``<SourcePict>`` element.
    """
    lines_path = Path(lines_path)
    new_image_path = Path(new_image_path)
    output_path = Path(output_path)

    if not lines_path.is_file():
        msg = f"Lines file not found: {lines_path}"
        raise FileNotFoundError(msg)
    if not new_image_path.is_file():
        msg = f"Image file not found: {new_image_path}"
        raise FileNotFoundError(msg)

    # Load and convert new image to JPEG
    jpeg_bytes, width, height = _image_to_jpeg_bytes(new_image_path)
    encoded = _encode_source_pict(jpeg_bytes)

    # Copy the .lines file first (preserve exact bytes for non-XML portions)
    if output_path != lines_path:
        shutil.copy2(lines_path, output_path)

    # Parse the XML
    tree = ET.parse(output_path)
    root = tree.getroot()

    # Find the canonical <SourcePict> — direct child of root, NOT an href reference
    source_pict = None
    for elem in root:
        if elem.tag == "SourcePict" and elem.get("href_id") is None:
            source_pict = elem
            break

    if source_pict is None:
        msg = f"No <SourcePict> element found in {lines_path}"
        raise ValueError(msg)

    # Update SourcePict attributes
    source_pict.set("width", str(width))
    source_pict.set("height", str(height))

    # Find or create the <ImageData> child
    image_data = source_pict.find("ImageData")
    if image_data is None:
        image_data = ET.SubElement(source_pict, "ImageData")

    # Update ImageData attributes and content
    image_data.set("width", str(width))
    image_data.set("height", str(height))
    image_data.set("pict_format", "jpg")
    image_data.text = encoded

    # Write back
    tree.write(output_path, encoding="unicode", xml_declaration=False)

    return output_path
