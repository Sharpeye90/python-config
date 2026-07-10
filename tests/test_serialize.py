"""Tests for python_config.serialize."""

import ast

from python_config import document
from python_config.parse import parse_config
from python_config.serialize import (
    _unparse_expr,
    serialize_config,
)


def test_dumps_evaluated_expressions_as_literals():
    source = 'A = 1\nB = 2\nNUM = 1 + 2 * 3\nMSG = f"{A}:{B}"\n'
    doc = document.loads(source)
    text = document.dumps(doc)

    assert doc["NUM"] == 7
    assert doc["MSG"] == "1:2"
    assert "NUM = 7" in text
    assert 'MSG = "1:2"' in text
    assert "1 + 2 * 3" not in text
    assert '= f"' not in text


def test_unparse_expr():
    # Multi-line list
    node = ast.parse("[1, 2, 3]").body[0].value
    result = _unparse_expr(node)
    assert (
        result
        == """[
    1,
    2,
    3,
]"""
    )

    # Forced double quotes
    node = ast.parse('"python-config"').body[0].value
    assert _unparse_expr(node) == '"python-config"'

    node = ast.parse("'python-config'").body[0].value
    assert _unparse_expr(node) == '"python-config"'


def test_parse_serialized(confpath):
    doc = parse_config(confpath.read_text())
    assert doc == parse_config(serialize_config(doc))
