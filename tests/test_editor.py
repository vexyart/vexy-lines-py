# this_file: vexy-lines-py/tests/test_editor.py
"""Tests for vexy_lines.editor.rename_objects."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

import pytest

from vexy_lines import GroupInfo, LayerInfo, parse, rename_objects, set_visibility

if TYPE_CHECKING:
    from pathlib import Path

# A minimal .lines document with known object IDs:
#   group "Group A"          object_id=1
#     layer "Layer 1"        object_id=10
#       fill  "Linear Fill"  object_id=100
#     layer "Layer 2"        object_id=11
#       fill  "Circle Fill"  object_id=101
_LINES_XML = textwrap.dedent("""\
    <?xml version="1.0" encoding="utf-8"?>
    <Project caption="TestProject" version="2.1" dpi="150">
      <Document width_mm="210.0" height_mm="297.0" dpi="300"/>
      <Objects>
        <LrSection caption="Group A" object_id="1" expanded="1">
          <Objects>
            <FreeMesh caption="Layer 1" object_id="10" visible="1">
              <Objects>
                <LinearStrokesTmpl caption="Linear Fill" object_id="100"
                    color_name="#ff112233" interval="1.5"/>
              </Objects>
            </FreeMesh>
            <FreeMesh caption="Layer 2" object_id="11" visible="0">
              <Objects>
                <CircleStrokesTmpl caption="Circle Fill" object_id="101"
                    color_name="#aabbcc"/>
                <LinearStrokesTmpl href_id="100"/>
              </Objects>
            </FreeMesh>
          </Objects>
        </LrSection>
      </Objects>
    </Project>
""")


@pytest.fixture
def lines_file(tmp_path: Path) -> Path:
    p = tmp_path / "doc.lines"
    p.write_text(_LINES_XML, encoding="utf-8")
    return p


def _captions(doc) -> dict[str, str]:
    """Flatten the parsed tree into {object_id_role: caption}."""
    out: dict[str, str] = {}

    def walk(nodes: list[GroupInfo | LayerInfo]) -> None:
        for node in nodes:
            if isinstance(node, GroupInfo):
                out[f"group:{node.object_id}"] = node.caption
                walk(node.children)
            elif isinstance(node, LayerInfo):
                out[f"layer:{node.object_id}"] = node.caption
                for fill in node.fills:
                    out[f"fill:{fill.object_id}"] = fill.caption

    walk(doc.groups)
    return out


def test_rename_objects_when_fill_then_updates_caption(lines_file: Path, tmp_path: Path):
    out = tmp_path / "renamed.lines"
    count = rename_objects(lines_file, out, {100: "red-hatching"})
    assert count == 1
    caps = _captions(parse(out))
    assert caps["fill:100"] == "red-hatching"
    # Unrelated objects untouched.
    assert caps["fill:101"] == "Circle Fill"
    assert caps["layer:10"] == "Layer 1"


def test_rename_objects_when_layer_and_group_then_updates_both(lines_file: Path, tmp_path: Path):
    out = tmp_path / "renamed.lines"
    count = rename_objects(lines_file, out, {1: "background", 10: "sky"})
    assert count == 2
    caps = _captions(parse(out))
    assert caps["group:1"] == "background"
    assert caps["layer:10"] == "sky"


def test_rename_objects_when_multiple_then_all_applied(lines_file: Path, tmp_path: Path):
    out = tmp_path / "renamed.lines"
    renames = {1: "g", 10: "l1", 11: "l2", 100: "f1", 101: "f2"}
    count = rename_objects(lines_file, out, renames)
    assert count == 5
    caps = _captions(parse(out))
    assert caps == {
        "group:1": "g",
        "layer:10": "l1",
        "layer:11": "l2",
        "fill:100": "f1",
        "fill:101": "f2",
    }


def test_rename_objects_when_id_missing_then_no_change(lines_file: Path, tmp_path: Path):
    out = tmp_path / "renamed.lines"
    count = rename_objects(lines_file, out, {99999: "nope"})
    assert count == 0
    caps = _captions(parse(out))
    assert caps["fill:100"] == "Linear Fill"


def test_rename_objects_when_same_caption_then_not_counted(lines_file: Path, tmp_path: Path):
    out = tmp_path / "renamed.lines"
    count = rename_objects(lines_file, out, {100: "Linear Fill"})
    assert count == 0


def _visible_attrs(path: Path) -> dict[int, str | None]:
    """Read the ``visible`` attribute of every object_id-bearing element."""
    root = ET.parse(path).getroot()  # noqa: S314
    out: dict[int, str | None] = {}
    for elem in root.iter():
        raw = elem.get("object_id")
        if raw is not None:
            out[int(raw)] = elem.get("visible")
    return out


def test_set_visibility_when_hide_fill_then_sets_attr_zero(lines_file: Path, tmp_path: Path):
    out = tmp_path / "vis.lines"
    count = set_visibility(lines_file, out, {100: False})
    assert count == 1
    assert _visible_attrs(out)[100] == "0"


def test_set_visibility_when_show_only_one_fill(lines_file: Path, tmp_path: Path):
    out = tmp_path / "vis.lines"
    count = set_visibility(lines_file, out, {100: True, 101: False})
    assert count == 2
    attrs = _visible_attrs(out)
    assert attrs[100] == "1"
    assert attrs[101] == "0"


def test_set_visibility_when_layer_and_group(lines_file: Path, tmp_path: Path):
    out = tmp_path / "vis.lines"
    set_visibility(lines_file, out, {1: True, 11: False})
    attrs = _visible_attrs(out)
    assert attrs[1] == "1"
    assert attrs[11] == "0"


def test_set_visibility_when_already_correct_then_not_counted(lines_file: Path, tmp_path: Path):
    out = tmp_path / "vis.lines"
    set_visibility(lines_file, out, {100: False})
    # Re-applying the same value to the already-modified copy is a no-op.
    count = set_visibility(out, out, {100: False})
    assert count == 0


def test_set_visibility_when_empty_then_copies(lines_file: Path, tmp_path: Path):
    out = tmp_path / "vis.lines"
    count = set_visibility(lines_file, out, {})
    assert count == 0
    assert out.is_file()


def test_set_visibility_when_missing_input_then_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        set_visibility(tmp_path / "nope.lines", tmp_path / "out.lines", {1: False})


def test_rename_objects_when_empty_renames_then_copies_file(lines_file: Path, tmp_path: Path):
    out = tmp_path / "copy.lines"
    count = rename_objects(lines_file, out, {})
    assert count == 0
    assert out.is_file()
    assert _captions(parse(out))["fill:100"] == "Linear Fill"


def test_rename_objects_when_href_reference_then_not_touched(lines_file: Path, tmp_path: Path):
    # The href element (href_id=100, no object_id) must never receive a caption.
    out = tmp_path / "renamed.lines"
    rename_objects(lines_file, out, {100: "real-fill"})
    text = out.read_text(encoding="utf-8")
    # Only the canonical fill (object_id=100) gets the caption.
    assert text.count('caption="real-fill"') == 1


def test_rename_objects_when_in_place_then_edits_same_file(lines_file: Path):
    count = rename_objects(lines_file, lines_file, {100: "in-place"})
    assert count == 1
    assert _captions(parse(lines_file))["fill:100"] == "in-place"


def test_rename_objects_when_missing_input_then_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        rename_objects(tmp_path / "nope.lines", tmp_path / "out.lines", {1: "x"})
