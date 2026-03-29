# this_file: vexy-lines-py/tests/test_types.py
"""Tests for vexy_lines.types dataclasses and constants."""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_fill_tag_map_has_14_entries(self):
        assert len(FILL_TAG_MAP) == 14

    def test_fill_tags_matches_tag_map_keys(self):
        assert FILL_TAGS == set(FILL_TAG_MAP)

    def test_fill_tag_map_contains_linear(self):
        assert FILL_TAG_MAP["LinearStrokesTmpl"] == "linear"

    def test_fill_tag_map_contains_source_strokes(self):
        assert FILL_TAG_MAP["SourceStrokes"] == "source_strokes"

    def test_numeric_params_has_11_entries(self):
        assert len(NUMERIC_PARAMS) == 11

    def test_numeric_params_contains_interval(self):
        assert "interval" in NUMERIC_PARAMS

    def test_numeric_params_contains_shear(self):
        assert "shear" in NUMERIC_PARAMS


# ---------------------------------------------------------------------------
# Dataclass construction and defaults
# ---------------------------------------------------------------------------


class TestFillParams:
    def test_construction_with_required_fields(self):
        fp = FillParams(fill_type="linear", color="#ff0000")
        assert fp.fill_type == "linear"
        assert fp.color == "#ff0000"

    def test_defaults(self):
        fp = FillParams(fill_type="linear", color="#000000")
        assert fp.interval == 0.0
        assert fp.angle == 0.0
        assert fp.thickness == 0.0
        assert fp.downlimit == 255.0
        assert fp.multiplier == 1.0
        assert fp.raw == {}

    def test_custom_values(self):
        fp = FillParams(
            fill_type="circular",
            color="#00ff00",
            interval=2.5,
            angle=45.0,
            thickness=1.0,
            raw={"key": "val"},
        )
        assert fp.interval == 2.5
        assert fp.angle == 45.0
        assert fp.raw == {"key": "val"}


class TestMaskInfo:
    def test_defaults(self):
        m = MaskInfo()
        assert m.mask_type == 0
        assert m.invert is False
        assert m.tolerance == 0.0

    def test_custom_values(self):
        m = MaskInfo(mask_type=1, invert=True, tolerance=0.5)
        assert m.mask_type == 1
        assert m.invert is True
        assert m.tolerance == 0.5


class TestFillNode:
    def test_construction(self):
        fp = FillParams(fill_type="linear", color="#000000")
        fn = FillNode(xml_tag="LinearStrokesTmpl", caption="Fill 1", params=fp)
        assert fn.xml_tag == "LinearStrokesTmpl"
        assert fn.caption == "Fill 1"
        assert fn.object_id is None

    def test_with_object_id(self):
        fp = FillParams(fill_type="linear", color="#000000")
        fn = FillNode(xml_tag="LinearStrokesTmpl", caption="Fill 1", params=fp, object_id=42)
        assert fn.object_id == 42


class TestLayerInfo:
    def test_defaults(self):
        li = LayerInfo(caption="Layer 1")
        assert li.caption == "Layer 1"
        assert li.object_id is None
        assert li.visible is True
        assert li.mask is None
        assert li.fills == []
        assert li.grid_edges == []

    def test_with_fills_and_mask(self):
        fp = FillParams(fill_type="linear", color="#000000")
        fn = FillNode(xml_tag="LinearStrokesTmpl", caption="Fill", params=fp)
        m = MaskInfo(mask_type=1)
        li = LayerInfo(caption="Layer", fills=[fn], mask=m, visible=False)
        assert len(li.fills) == 1
        assert li.mask is not None
        assert li.visible is False


class TestGroupInfo:
    def test_defaults(self):
        gi = GroupInfo(caption="Group 1")
        assert gi.caption == "Group 1"
        assert gi.expanded is True
        assert gi.children == []

    def test_nested_children(self):
        layer = LayerInfo(caption="Child Layer")
        sub_group = GroupInfo(caption="Sub Group", children=[layer])
        gi = GroupInfo(caption="Parent", children=[sub_group])
        assert len(gi.children) == 1
        assert isinstance(gi.children[0], GroupInfo)
        child = gi.children[0]
        assert isinstance(child, GroupInfo)
        assert len(child.children) == 1


class TestDocumentProps:
    def test_defaults(self):
        dp = DocumentProps()
        assert dp.width_mm == 0.0
        assert dp.height_mm == 0.0
        assert dp.dpi == 300
        assert dp.thickness_min == 0.0
        assert dp.interval_max == 0.0

    def test_custom(self):
        dp = DocumentProps(width_mm=210.0, height_mm=297.0, dpi=600)
        assert dp.width_mm == 210.0
        assert dp.dpi == 600


class TestLinesDocument:
    def test_defaults(self):
        ld = LinesDocument()
        assert ld.caption == ""
        assert ld.version == ""
        assert ld.dpi == 300
        assert ld.groups == []
        assert ld.source_image_data is None
        assert ld.preview_image_data is None

    def test_with_data(self):
        ld = LinesDocument(
            caption="My Art",
            version="1.0",
            dpi=150,
            source_image_data=b"\xff\xd8\xff\xe0",
            preview_image_data=b"\x89PNG",
        )
        assert ld.caption == "My Art"
        assert ld.source_image_data == b"\xff\xd8\xff\xe0"
        assert ld.preview_image_data == b"\x89PNG"
