# Changelog

All notable changes to `vexy-lines-py` are documented here.
The version scheme follows the Vexy Lines SDK suite (SemVer-compatible, v1.x series).

## v1.0.36 (2026-06-28)

- Added `replace_source_image()` for writing a new JPEG source image into a
  `.lines` file without touching any other data.
- Added `set_visibility()` for toggling the `visible` attribute on groups,
  layers, and fills by object ID.
- Added `extract_source_images()` to extract every `<SourcePict>` payload
  (document-level and group-level) in a single call.
- Extended `LinesDocument` with a `source_images` list holding typed
  `SourceImageInfo` entries (index, scope, owner path, dimensions).
- `pillow` added as a runtime dependency to support JPEG conversion and
  canvas-fit resizing inside `replace_source_image()`.

## v1.0.25 (2026-03-30)

- Added `parse_string()` — parse a `.lines` XML string already in memory
  instead of reading from disk.

## v1.0.20 (2026-01-01)

- Initial public release.
- Pure-Python, cross-platform parser for the `.lines` binary XML format.
- No Vexy Lines app required; works entirely offline.
- Typed dataclasses: `LinesDocument`, `GroupInfo`, `LayerInfo`, `FillNode`,
  `FillParams`, `MaskInfo`, `DocumentProps`.
- Decodes embedded JPEG source image (`<SourcePict>`) and PNG preview
  (`<PreviewDoc>`).
- Parses image-filter chains with typed parameter values
  (`ImageFilterEntry`).
- `rename_objects()` for in-place caption editing by object ID.
