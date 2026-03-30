# this_file: vexy-lines-py/tests/test_parser.py
"""Tests for vexy_lines.parser — the .lines file parser."""

from __future__ import annotations

import base64
import struct
import textwrap
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from unittest.mock import patch

import pytest

from vexy_lines.parser import (
    _decode_preview_doc,
    _decode_source_pict,
    _get_float,
    _get_int,
    _is_href,
    _normalise_color,
    _parse_document_props,
    _parse_fill,
    _parse_group,
    _parse_layer,
    _parse_objects,
    _resolve_fill_type,
    extract_preview_image,
    extract_source_image,
    parse,
    parse_string,
)
from vexy_lines.types import (
    FillNode,
    FillParams,
    GroupInfo,
    LayerInfo,
    LinesDocument,
)

# ---------------------------------------------------------------------------
# Fixtures — minimal synthetic XML
# ---------------------------------------------------------------------------

# A JPEG-like payload for SourcePict tests.
_FAKE_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 20

# Build a valid SourcePict base64 blob: 4-byte BE size + zlib(jpeg).
_COMPRESSED_JPEG = zlib.compress(_FAKE_JPEG)
_SOURCE_PICT_RAW = struct.pack(">I", len(_FAKE_JPEG)) + _COMPRESSED_JPEG
_SOURCE_PICT_B64 = base64.b64encode(_SOURCE_PICT_RAW).decode()

# A fake PNG payload for PreviewDoc tests.
_FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_PREVIEW_B64 = base64.b64encode(_FAKE_PNG).decode()

MINIMAL_LINES_XML = textwrap.dedent(f"""\
    <?xml version="1.0" encoding="utf-8"?>
    <Project caption="TestProject" version="2.1" dpi="150">
      <Document width_mm="210.0" height_mm="297.0" dpi="300"
                thicknessMin="0.1" thicknessMax="2.0"
                intervalMin="0.5" intervalMax="5.0"/>
      <Objects>
        <LrSection caption="Group A" object_id="1" expanded="1">
          <Objects>
            <FreeMesh caption="Layer 1" object_id="10" visible="1">
              <Objects>
                <LinearStrokesTmpl caption="Linear Fill"
                    object_id="100" color_name="#ff112233"
                    interval="1.5" angle="45.0" thick_gap="0.3"
                    base_width="0.1" smoothness="0.8"
                    uplimit="200" downlimit="10"
                    multiplier="1.2" dispersion="0.05" shear="5.0"/>
              </Objects>
              <MaskData mask_type="1" invert_mask="1" tolerance="0.75"/>
              <row_grid_edge x1="0" y1="0" x2="100" y2="100"/>
            </FreeMesh>
            <FreeMesh caption="Layer 2" object_id="11" visible="0">
              <Objects>
                <CircleStrokesTmpl caption="Circle Fill"
                    object_id="101" color_name="#aabbcc"/>
              </Objects>
            </FreeMesh>
          </Objects>
        </LrSection>
      </Objects>
      <SourcePict>
        <ImageData>{_SOURCE_PICT_B64}</ImageData>
      </SourcePict>
      <PreviewDoc>{_PREVIEW_B64}</PreviewDoc>
    </Project>
""")


def _write_lines_file(tmp_path: Path, xml_content: str = MINIMAL_LINES_XML) -> Path:
    """Write XML content to a temporary .lines file and return its path."""
    p = tmp_path / "test.lines"
    p.write_text(xml_content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _get_float
# ---------------------------------------------------------------------------


class TestGetFloat:
    def test_get_float_when_present_then_returns_value(self):
        assert _get_float({"x": "3.14"}, "x") == pytest.approx(3.14)

    def test_get_float_when_absent_then_returns_default(self):
        assert _get_float({}, "x") == 0.0

    def test_get_float_when_absent_then_returns_custom_default(self):
        assert _get_float({}, "x", default=99.0) == 99.0

    def test_get_float_when_non_numeric_then_returns_default(self):
        assert _get_float({"x": "abc"}, "x") == 0.0

    def test_get_float_when_integer_string_then_returns_float(self):
        assert _get_float({"x": "42"}, "x") == 42.0


# ---------------------------------------------------------------------------
# _get_int
# ---------------------------------------------------------------------------


class TestGetInt:
    def test_get_int_when_present_then_returns_value(self):
        assert _get_int({"n": "7"}, "n") == 7

    def test_get_int_when_absent_then_returns_default(self):
        assert _get_int({}, "n") == 0

    def test_get_int_when_float_string_then_truncates(self):
        assert _get_int({"n": "300.0"}, "n") == 300

    def test_get_int_when_non_numeric_then_returns_default(self):
        assert _get_int({"n": "xyz"}, "n") == 0

    def test_get_int_when_custom_default_then_returns_it(self):
        assert _get_int({}, "n", default=42) == 42


# ---------------------------------------------------------------------------
# _normalise_color
# ---------------------------------------------------------------------------


class TestNormaliseColor:
    def test_normalise_color_when_empty_then_returns_black(self):
        assert _normalise_color("") == "#000000"

    def test_normalise_color_when_ff_alpha_prefix_then_strips_alpha(self):
        assert _normalise_color("#ff112233") == "#112233"

    def test_normalise_color_when_non_ff_alpha_then_reorders(self):
        assert _normalise_color("#80112233") == "#11223380"

    def test_normalise_color_when_six_digit_hex_then_passes_through(self):
        assert _normalise_color("#aabbcc") == "#aabbcc"

    def test_normalise_color_when_decimal_argb_opaque_then_converts(self):
        # 0xFF000000 = 4278190080 → #000000
        assert _normalise_color("4278190080") == "#000000"

    def test_normalise_color_when_decimal_argb_with_alpha_then_converts(self):
        # 0x80FF0000 = 2164195328 → #ff000080
        assert _normalise_color("2164195328") == "#ff000080"

    def test_normalise_color_when_non_parseable_then_returns_black(self):
        assert _normalise_color("not-a-color") == "#000000"

    def test_normalise_color_when_whitespace_padded_then_strips(self):
        assert _normalise_color("  #aabbcc  ") == "#aabbcc"


# ---------------------------------------------------------------------------
# _is_href
# ---------------------------------------------------------------------------


class TestIsHref:
    def test_is_href_when_has_href_id_then_true(self):
        elem = ET.fromstring('<LinearStrokesTmpl href_id="5" type="42"/>')
        assert _is_href(elem) is True

    def test_is_href_when_no_href_id_then_false(self):
        elem = ET.fromstring('<LinearStrokesTmpl object_id="5"/>')
        assert _is_href(elem) is False


# ---------------------------------------------------------------------------
# _resolve_fill_type
# ---------------------------------------------------------------------------


class TestResolveFillType:
    def test_resolve_fill_type_when_linear_then_returns_linear(self):
        assert _resolve_fill_type("LinearStrokesTmpl", {}) == "linear"

    def test_resolve_fill_type_when_free_curve_type_conv_9_then_trace(self):
        assert _resolve_fill_type("FreeCurveStrokesTmpl", {"type_conv": "9"}) == "trace"

    def test_resolve_fill_type_when_free_curve_type_conv_2_then_handmade(self):
        # type_conv=2 (balanced) falls back to base mapping "handmade"
        assert _resolve_fill_type("FreeCurveStrokesTmpl", {"type_conv": "2"}) == "handmade"

    def test_resolve_fill_type_when_unknown_tag_then_returns_tag(self):
        assert _resolve_fill_type("UnknownTmpl", {}) == "UnknownTmpl"

    def test_resolve_fill_type_when_source_strokes_then_returns_source_strokes(self):
        assert _resolve_fill_type("SourceStrokes", {}) == "source_strokes"


# ---------------------------------------------------------------------------
# Binary decoders
# ---------------------------------------------------------------------------


class TestDecodeSourcePict:
    def test_decode_source_pict_when_valid_then_returns_jpeg(self):
        xml = f'<SourcePict><ImageData>{_SOURCE_PICT_B64}</ImageData></SourcePict>'
        elem = ET.fromstring(xml)
        result = _decode_source_pict(elem)
        assert result == _FAKE_JPEG

    def test_decode_source_pict_when_no_image_data_then_raises(self):
        elem = ET.fromstring("<SourcePict/>")
        with pytest.raises(ValueError, match="no ImageData"):
            _decode_source_pict(elem)

    def test_decode_source_pict_when_empty_text_then_raises(self):
        elem = ET.fromstring("<SourcePict><ImageData></ImageData></SourcePict>")
        with pytest.raises(ValueError, match="no ImageData"):
            _decode_source_pict(elem)

    def test_decode_source_pict_when_too_short_then_raises(self):
        short_b64 = base64.b64encode(b"\x00\x01").decode()
        xml = f"<SourcePict><ImageData>{short_b64}</ImageData></SourcePict>"
        elem = ET.fromstring(xml)
        with pytest.raises(ValueError, match="too short"):
            _decode_source_pict(elem)

    def test_decode_source_pict_when_bad_zlib_then_raises(self):
        bad_raw = struct.pack(">I", 100) + b"\x00\x01\x02\x03\x04\x05"
        bad_b64 = base64.b64encode(bad_raw).decode()
        xml = f"<SourcePict><ImageData>{bad_b64}</ImageData></SourcePict>"
        elem = ET.fromstring(xml)
        with pytest.raises(ValueError, match="zlib-decompress"):
            _decode_source_pict(elem)


class TestDecodePreviewDoc:
    def test_decode_preview_doc_when_valid_then_returns_png(self):
        xml = f"<PreviewDoc>{_PREVIEW_B64}</PreviewDoc>"
        elem = ET.fromstring(xml)
        result = _decode_preview_doc(elem)
        assert result == _FAKE_PNG

    def test_decode_preview_doc_when_empty_then_raises(self):
        elem = ET.fromstring("<PreviewDoc/>")
        with pytest.raises(ValueError, match="no text content"):
            _decode_preview_doc(elem)


# ---------------------------------------------------------------------------
# Element parsers
# ---------------------------------------------------------------------------


class TestParseFill:
    def test_parse_fill_when_linear_then_correct_params(self):
        xml = (
            '<LinearStrokesTmpl caption="My Fill" object_id="42" '
            'color_name="#ff112233" interval="1.5" angle="30.0" '
            'thick_gap="0.5" base_width="0.1" smoothness="0.9" '
            'uplimit="200" downlimit="10" multiplier="1.3" '
            'dispersion="0.2" shear="3.0"/>'
        )
        elem = ET.fromstring(xml)
        fn = _parse_fill(elem)
        assert fn.xml_tag == "LinearStrokesTmpl"
        assert fn.caption == "My Fill"
        assert fn.object_id == 42
        assert fn.params.fill_type == "linear"
        assert fn.params.color == "#112233"
        assert fn.params.interval == pytest.approx(1.5)
        assert fn.params.shear == pytest.approx(3.0)
        assert "interval" in fn.params.raw


class TestParseMask:
    def test_parse_mask_when_present_then_correct_fields(self):
        from vexy_lines.parser import _parse_mask

        xml = '<MaskData mask_type="1" invert_mask="1" tolerance="0.75"/>'
        elem = ET.fromstring(xml)
        m = _parse_mask(elem)
        assert m.mask_type == 1
        assert m.invert is True
        assert m.tolerance == pytest.approx(0.75)


class TestParseLayer:
    def test_parse_layer_when_full_then_has_fills_and_mask(self):
        xml = textwrap.dedent("""\
            <FreeMesh caption="Layer X" object_id="5" visible="1">
              <Objects>
                <LinearStrokesTmpl caption="F1" object_id="50" color_name="#aabbcc"/>
                <CircleStrokesTmpl caption="F2" object_id="51" color_name="#ddeeff"/>
              </Objects>
              <MaskData mask_type="1" invert_mask="0" tolerance="0.5"/>
              <row_grid_edge x1="0" y1="0"/>
            </FreeMesh>
        """)
        elem = ET.fromstring(xml)
        layer = _parse_layer(elem)
        assert layer.caption == "Layer X"
        assert layer.object_id == 5
        assert layer.visible is True
        assert len(layer.fills) == 2
        assert layer.mask is not None
        assert layer.mask.mask_type == 1
        assert len(layer.grid_edges) == 1

    def test_parse_layer_when_href_fill_then_skips_it(self):
        xml = textwrap.dedent("""\
            <FreeMesh caption="L" object_id="1">
              <Objects>
                <LinearStrokesTmpl href_id="99" type="42"/>
                <LinearStrokesTmpl caption="Real" object_id="2" color_name="#000000"/>
              </Objects>
            </FreeMesh>
        """)
        elem = ET.fromstring(xml)
        layer = _parse_layer(elem)
        assert len(layer.fills) == 1
        assert layer.fills[0].caption == "Real"

    def test_parse_layer_when_hidden_then_visible_false(self):
        xml = '<FreeMesh caption="Hidden" object_id="1" visible="0"/>'
        elem = ET.fromstring(xml)
        layer = _parse_layer(elem)
        assert layer.visible is False


class TestParseGroup:
    def test_parse_group_when_has_children_then_populates(self):
        xml = textwrap.dedent("""\
            <LrSection caption="Group" object_id="1" expanded="1">
              <Objects>
                <FreeMesh caption="Child Layer" object_id="2"/>
              </Objects>
            </LrSection>
        """)
        elem = ET.fromstring(xml)
        group = _parse_group(elem)
        assert group.caption == "Group"
        assert group.expanded is True
        assert len(group.children) == 1
        assert isinstance(group.children[0], LayerInfo)

    def test_parse_group_when_collapsed_then_expanded_false(self):
        xml = '<LrSection caption="G" object_id="1" expanded="0"/>'
        elem = ET.fromstring(xml)
        group = _parse_group(elem)
        assert group.expanded is False


class TestParseObjects:
    def test_parse_objects_when_mixed_then_returns_both_types(self):
        xml = textwrap.dedent("""\
            <Objects>
              <LrSection caption="G" object_id="1">
                <Objects>
                  <FreeMesh caption="L" object_id="2"/>
                </Objects>
              </LrSection>
              <FreeMesh caption="Top Layer" object_id="3"/>
            </Objects>
        """)
        elem = ET.fromstring(xml)
        result = _parse_objects(elem)
        assert len(result) == 2
        assert isinstance(result[0], GroupInfo)
        assert isinstance(result[1], LayerInfo)

    def test_parse_objects_when_href_then_skips(self):
        xml = textwrap.dedent("""\
            <Objects>
              <FreeMesh href_id="99" type="42"/>
              <FreeMesh caption="Real" object_id="1"/>
            </Objects>
        """)
        elem = ET.fromstring(xml)
        result = _parse_objects(elem)
        assert len(result) == 1


class TestParseDocumentProps:
    def test_parse_document_props_when_full_then_all_fields(self):
        xml = (
            '<Document width_mm="210.0" height_mm="297.0" dpi="600" '
            'thicknessMin="0.1" thicknessMax="2.0" '
            'intervalMin="0.5" intervalMax="5.0"/>'
        )
        elem = ET.fromstring(xml)
        props = _parse_document_props(elem)
        assert props.width_mm == pytest.approx(210.0)
        assert props.height_mm == pytest.approx(297.0)
        assert props.dpi == 600
        assert props.thickness_min == pytest.approx(0.1)
        assert props.interval_max == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Public API — parse()
# ---------------------------------------------------------------------------


class TestParse:
    def test_parse_when_valid_file_then_returns_document(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        assert isinstance(doc, LinesDocument)
        assert doc.caption == "TestProject"
        assert doc.version == "2.1"
        assert doc.dpi == 150

    def test_parse_when_valid_file_then_has_groups(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        assert len(doc.groups) == 1
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        assert group.caption == "Group A"
        assert len(group.children) == 2

    def test_parse_when_valid_file_then_has_fills(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        layer = group.children[0]
        assert isinstance(layer, LayerInfo)
        assert len(layer.fills) == 1
        assert layer.fills[0].params.fill_type == "linear"

    def test_parse_when_valid_file_then_has_mask(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        layer = group.children[0]
        assert isinstance(layer, LayerInfo)
        assert layer.mask is not None
        assert layer.mask.invert is True

    def test_parse_when_valid_file_then_has_document_props(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        assert doc.props.width_mm == pytest.approx(210.0)
        assert doc.props.height_mm == pytest.approx(297.0)
        assert doc.props.dpi == 300

    def test_parse_when_valid_file_then_has_source_image(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        assert doc.source_image_data is not None
        assert doc.source_image_data == _FAKE_JPEG

    def test_parse_when_valid_file_then_has_preview_image(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        assert doc.preview_image_data is not None
        assert doc.preview_image_data == _FAKE_PNG

    def test_parse_when_file_not_found_then_raises(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            parse("/nonexistent/path/test.lines")

    def test_parse_when_malformed_xml_then_raises(self, tmp_path):
        p = tmp_path / "bad.lines"
        p.write_text("<not-closed", encoding="utf-8")
        with pytest.raises(ET.ParseError):
            parse(p)

    def test_parse_when_empty_project_then_returns_defaults(self, tmp_path):
        xml = '<?xml version="1.0"?><Project/>'
        p = _write_lines_file(tmp_path, xml)
        doc = parse(p)
        assert doc.caption == ""
        assert doc.version == ""
        assert doc.dpi == 300
        assert doc.groups == []
        assert doc.source_image_data is None

    def test_parse_when_hidden_layer_then_visible_false(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        layer2 = group.children[1]
        assert isinstance(layer2, LayerInfo)
        assert layer2.visible is False

    def test_parse_when_string_path_then_works(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(str(p))
        assert doc.caption == "TestProject"

    def test_parse_when_no_source_image_element_then_none(self, tmp_path):
        xml = '<?xml version="1.0"?><Project caption="NoImages"/>'
        p = _write_lines_file(tmp_path, xml)
        doc = parse(p)
        assert doc.source_image_data is None
        assert doc.preview_image_data is None


# ---------------------------------------------------------------------------
# Public API — parse_string
# ---------------------------------------------------------------------------


class TestParseString:
    def test_parse_string_when_valid_xml_then_returns_document(self):
        doc = parse_string(MINIMAL_LINES_XML)
        assert isinstance(doc, LinesDocument)
        assert doc.caption == "TestProject"
        assert doc.version == "2.1"
        assert doc.dpi == 150

    def test_parse_string_when_valid_xml_then_has_groups(self):
        doc = parse_string(MINIMAL_LINES_XML)
        assert len(doc.groups) == 1
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        assert group.caption == "Group A"

    def test_parse_string_when_valid_xml_then_has_fills(self):
        doc = parse_string(MINIMAL_LINES_XML)
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        layer = group.children[0]
        assert isinstance(layer, LayerInfo)
        assert len(layer.fills) == 1
        assert layer.fills[0].params.fill_type == "linear"

    def test_parse_string_when_minimal_project_then_returns_defaults(self):
        doc = parse_string('<?xml version="1.0"?><Project caption="Bare"/>')
        assert doc.caption == "Bare"
        assert doc.groups == []
        assert doc.source_image_data is None

    def test_parse_string_when_malformed_xml_then_raises(self):
        with pytest.raises(ET.ParseError):
            parse_string("<not valid xml><<<")

    def test_parse_string_matches_file_parse(self, tmp_path):
        p = _write_lines_file(tmp_path)
        from_file = parse(p)
        from_string = parse_string(MINIMAL_LINES_XML)
        assert from_file.caption == from_string.caption
        assert from_file.dpi == from_string.dpi
        assert len(from_file.groups) == len(from_string.groups)
        assert from_file.source_image_data == from_string.source_image_data


# ---------------------------------------------------------------------------
# Public API — extract images
# ---------------------------------------------------------------------------


class TestExtractSourceImage:
    def test_extract_source_image_when_valid_then_writes_file(self, tmp_path):
        lines_path = _write_lines_file(tmp_path)
        out = tmp_path / "source.jpg"
        result = extract_source_image(lines_path, out)
        assert result == out
        assert out.read_bytes() == _FAKE_JPEG

    def test_extract_source_image_when_no_image_then_raises(self, tmp_path):
        xml = '<?xml version="1.0"?><Project caption="NoImg"/>'
        p = _write_lines_file(tmp_path, xml)
        with pytest.raises(ValueError, match="No source image"):
            extract_source_image(p, tmp_path / "out.jpg")

    def test_extract_source_image_when_missing_file_then_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_source_image(tmp_path / "nope.lines", tmp_path / "out.jpg")


class TestExtractPreviewImage:
    def test_extract_preview_image_when_valid_then_writes_file(self, tmp_path):
        lines_path = _write_lines_file(tmp_path)
        out = tmp_path / "preview.png"
        result = extract_preview_image(lines_path, out)
        assert result == out
        assert out.read_bytes() == _FAKE_PNG

    def test_extract_preview_image_when_no_image_then_raises(self, tmp_path):
        xml = '<?xml version="1.0"?><Project caption="NoImg"/>'
        p = _write_lines_file(tmp_path, xml)
        with pytest.raises(ValueError, match="No preview image"):
            extract_preview_image(p, tmp_path / "out.png")

    def test_extract_preview_image_when_missing_file_then_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_preview_image(tmp_path / "nope.lines", tmp_path / "out.png")


# ---------------------------------------------------------------------------
# Grid edges
# ---------------------------------------------------------------------------


class TestGridEdges:
    def test_parse_layer_when_grid_edges_then_captures_them(self, tmp_path):
        p = _write_lines_file(tmp_path)
        doc = parse(p)
        group = doc.groups[0]
        assert isinstance(group, GroupInfo)
        layer = group.children[0]
        assert isinstance(layer, LayerInfo)
        assert len(layer.grid_edges) == 1
        edge = layer.grid_edges[0]
        assert edge["type"] == "row_grid_edge"
        assert edge["x1"] == "0"
