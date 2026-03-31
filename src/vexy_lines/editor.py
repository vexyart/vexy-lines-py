# this_file: vexy-lines-py/src/vexy_lines/editor.py
"""Editing operations for .lines files.

Currently supports replacing the embedded source image while preserving
all fill parameters, layers, groups, masks, and document settings.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PILImage
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


def _resize_to_fit(img: "PILImage.Image", target_w: int, target_h: int) -> "PILImage.Image":
    """Resize image to fit within target dimensions, centered on white background.

    - If the image already matches: return as-is.
    - If the image is larger in any dimension: downscale to fit inside target
      (maintaining aspect ratio), then center on a white canvas of target size.
    - If the image is smaller: center on a white canvas of target size (no upscale).

    White padding is correct for Vexy Lines: the fill algorithms treat white
    as "no strokes" (brightness-driven), so padded areas produce no output.
    """
    from PIL import Image as PILImage

    w, h = img.size
    if w == target_w and h == target_h:
        return img

    # Ensure RGB mode
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    # Downscale if larger in any dimension
    if w > target_w or h > target_h:
        scale = min(target_w / w, target_h / h)
        new_w = round(w * scale)
        new_h = round(h * scale)
        img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
        w, h = new_w, new_h

    # Create white canvas and paste centered
    canvas = PILImage.new("RGB", (target_w, target_h), (255, 255, 255))
    offset_x = (target_w - w) // 2
    offset_y = (target_h - h) // 2
    canvas.paste(img, (offset_x, offset_y))
    return canvas


def replace_source_image(
    lines_path: str | Path,
    new_image_path: str | Path,
    output_path: str | Path,
    *,
    target_size: tuple[int, int] | None = None,
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
        target_size: If provided, resize the new image to fit these (width, height) pixel dimensions.

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

    # Resize if target dimensions specified and don't match
    if target_size and (width, height) != target_size:
        from PIL import Image as PILImage

        img = PILImage.open(new_image_path)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img = _resize_to_fit(img, target_size[0], target_size[1])
        width, height = img.size
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        jpeg_bytes = buf.getvalue()

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
