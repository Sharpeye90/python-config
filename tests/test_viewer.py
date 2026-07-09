"""Integration tests for the interactive config viewer."""

from unittest.mock import patch

from click.testing import CliRunner

from python_config.viewer import nav
from python_config.viewer.app import run_viewer
from python_config.viewer.cli import main


def test_paginate_empty():
    items, page, total_pages = nav.paginate([], 0, 20)
    assert items == []
    assert page == 0
    assert total_pages == 1


def test_paginate_multiple_pages():
    items = list(range(45))
    page_items, page, total_pages = nav.paginate(items, 1, 20)
    assert page_items == list(range(20, 40))
    assert page == 1
    assert total_pages == 3


def test_preview_value_truncates_long_string():
    text = "x" * 100
    preview = nav.preview_value(text, max_len=20)
    assert preview != repr(text)
    assert len(preview) <= 20


def test_list_children_root_lists_variables(confdoc):
    children = nav.list_children(confdoc, ())
    labels = [row[0] for row in children]
    assert "PROJECT_NAME" in labels
    assert all(row[1] != "section" for row in children)


def test_search_root_matches(confdoc):
    matches = nav.search(confdoc, (), "log")
    labels = [label for label, _path in matches]
    assert "LOG_LEVEL" in labels


def test_resolve_nested_dict(confdoc):
    path = (nav.VarKey("PROJECT"), nav.DictKey("tools"))
    value, assignment = nav.resolve(confdoc, path)
    assert assignment is None
    assert "ruff" in value


def test_assignment_source_shows_literal_value(confdoc):
    item = confdoc.getvar("BUILD_NUMBER")
    source = nav.assignment_source_text(item)
    assert source == "BUILD_NUMBER = 7"


def test_assignment_source_unparse(confdoc):
    item = confdoc.getvar("PACKAGE_NAME")
    source = nav.assignment_source_text(item)
    assert source == 'PACKAGE_NAME = "python-config-1.0.0"'


def test_format_detail_value_truncates_large_list():
    value = list(range(100))
    text = nav.format_detail_value(value, max_items=3)
    assert "more items" in text


def test_truncate_text():
    assert nav.truncate_text(None) == ""
    text = nav.truncate_text("a" * 3000, max_len=100)
    assert len(text) <= 100
    assert text != "a" * 3000


def test_pager_viewport_centers_short_content():
    visible, scroll, can_up, can_down = nav.pager_viewport(["a", "b"], 0, 5)
    assert visible == ["", "a", "b", "", ""]
    assert scroll == 0
    assert not can_up
    assert not can_down


def test_pager_viewport_scrolls_long_content():
    lines = [str(index) for index in range(10)]
    visible, scroll, can_up, can_down = nav.pager_viewport(lines, 0, 3)
    assert visible == ["0", "1", "2"]
    assert scroll == 0
    assert not can_up
    assert can_down

    visible, scroll, can_up, can_down = nav.pager_viewport(lines, 1, 3)
    assert visible == ["1", "2", "3"]
    assert scroll == 1
    assert can_up
    assert can_down


def test_value_pager_lines_dict(confdoc):
    value, _assignment = nav.resolve(confdoc, (nav.VarKey("PROJECT"),))
    lines = nav.value_pager_lines(value, width=100)
    assert len(lines) > 5
    assert any("python-config" in line for line in lines)


def test_viewer_app_toggle_source(confdoc, confpath):
    keys = iter(["a", "a", "q"])

    run_viewer(
        confdoc,
        str(confpath),
        no_color=True,
        input_fn=lambda: next(keys),
        prompt_fn=lambda *args, **kwargs: "",
    )


def test_render_detail_panel_source_toggle(confdoc):
    from io import StringIO

    from rich.console import Console

    from python_config.viewer.render import render_detail_panel

    path = (nav.VarKey("BUILD_NUMBER"),)
    console = Console(file=StringIO(), force_terminal=True, width=120, no_color=True)

    value_panel = render_detail_panel(confdoc, path, "BUILD_NUMBER", show_source=False)
    console.print(value_panel)
    value_output = console.file.getvalue()
    assert "Press s to expand value" in value_output
    assert "Press a to view assignment source" in value_output
    assert "1 + 2 * 3" not in value_output

    console = Console(file=StringIO(), force_terminal=True, width=120, no_color=True)
    source_panel = render_detail_panel(confdoc, path, "BUILD_NUMBER", show_source=True)
    console.print(source_panel)
    source_output = console.file.getvalue()
    assert "BUILD_NUMBER = 7" in source_output
    assert "Press a to return to value" in source_output


def test_viewer_app_pager_toggle(confdoc, confpath):
    children = nav.list_children(confdoc, ())
    project_index = next(
        index for index, (label, *_rest) in enumerate(children) if label == "PROJECT"
    )
    keys = ["n"] * project_index + ["s", "s", "q"]
    key_iter = iter(keys)

    run_viewer(
        confdoc,
        str(confpath),
        no_color=True,
        input_fn=lambda: next(key_iter),
        prompt_fn=lambda *args, **kwargs: "",
    )


def test_render_pager_screen(confdoc):
    from io import StringIO

    from rich.console import Console

    from python_config.viewer.render import build_pager_screen

    value, _assignment = nav.resolve(confdoc, (nav.VarKey("PROJECT"),))
    lines = nav.value_pager_lines(value, width=100)
    screen = build_pager_screen("PROJECT", (nav.VarKey("PROJECT"),), lines, 0, 40)
    console = Console(file=StringIO(), force_terminal=True, width=100, height=40, no_color=True)
    console.print(screen)
    output = console.file.getvalue()
    assert "PROJECT" in output
    assert "python-config" in output
    assert "[j/n] down" in output


def test_viewer_app_quits_on_q(confdoc, confpath):
    keys = iter(["q"])
    run_viewer(
        confdoc,
        str(confpath),
        no_color=True,
        input_fn=lambda: next(keys),
        prompt_fn=lambda *args, **kwargs: "",
    )


def test_viewer_app_search_and_open(confdoc, confpath):
    keys = iter(["/", "\r", "b", "q"])

    def prompt_fn(*args, **kwargs):
        return "LOG"

    run_viewer(
        confdoc,
        str(confpath),
        no_color=True,
        input_fn=lambda: next(keys),
        prompt_fn=prompt_fn,
    )


def test_cli_smoke_quit(confpath):
    runner = CliRunner()

    with patch("click.getchar", side_effect=iter(["q"])):
        result = runner.invoke(main, [str(confpath), "--no-color"], catch_exceptions=False)

    assert result.exit_code == 0


def test_cli_shows_variable_names(confpath):
    runner = CliRunner()

    with patch("click.getchar", side_effect=iter(["q"])):
        result = runner.invoke(main, [str(confpath), "--no-color"])

    assert result.exit_code == 0
    assert "PROJECT_NAME" in result.output


def test_cli_missing_file():
    runner = CliRunner()
    result = runner.invoke(main, ["/no/such/config.conf"])
    assert result.exit_code != 0


def test_huge_config_output_bounded(huge_conf_path):
    runner = CliRunner()

    with patch("click.getchar", side_effect=iter(["q"])):
        result = runner.invoke(main, [str(huge_conf_path), "--no-color", "--page-size", "20"])

    assert result.exit_code == 0
    assert "VAR1" in result.output or "VAR200" in result.output
    assert result.output.count("sub2-sub1-") < 50


def test_huge_config_search_var42(huge_conf_path):
    keys = iter(["/", "q"])

    def input_fn():
        return next(keys)

    def prompt_fn(*args, **kwargs):
        return "VAR42"

    from python_config import document

    doc = document.load(huge_conf_path)
    run_viewer(
        doc,
        str(huge_conf_path),
        no_color=True,
        input_fn=input_fn,
        prompt_fn=prompt_fn,
    )

    matches = nav.search(doc, (), "VAR42")
    assert len(matches) == 1
    assert matches[0][0] == "VAR42"
