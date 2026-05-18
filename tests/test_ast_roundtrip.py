"""Test internal AST parse/serialize round-trip."""

import os

import pytest

from python_config.parse import ParseError, parse_config
from python_config.serialize import serialize_config

EXAMPLE = os.path.join(os.path.dirname(__file__), "example.conf")


def test_load_example_values():
    doc = parse_config(open(EXAMPLE).read())
    assert doc["VAR1"] == "string-value"
    assert doc["VAR2"] == 10.0
    assert doc["SOMEDATA"] == {"key1": 20, "key2": {"subkey": 30}}
    assert doc["SOMETHINGS"] == ["thing1", "thing2"]


def test_load_example_docstrings():
    doc = parse_config(open(EXAMPLE).read())
    by_name = {item.name: item for item in doc.items}
    assert by_name["VAR2"].docstring == "This variable has a docstring."
    assert by_name["SOMETHINGS"].docstring == "Another docstring."
    assert by_name["VAR1"].docstring is None


def test_load_example_preamble():
    doc = parse_config(open(EXAMPLE).read())
    assert doc.preamble.startswith("# vim: set tf=python:")


def test_roundtrip_preserves_semantics():
    source = open(EXAMPLE).read()
    doc = parse_config(source)
    again = parse_config(serialize_config(doc))
    assert again.preamble == doc.preamble
    assert again.names() == doc.names()
    for name in doc.names():
        assert again[name] == doc[name]
    for left, right in zip(doc.items, again.items):
        assert left.docstring == right.docstring


def test_roundtrip_docstrings_in_output():
    doc = parse_config(open(EXAMPLE).read())
    text = serialize_config(doc)
    assert '"""This variable has a docstring."""' in text
    assert '"""Another docstring."""' in text


def test_rejects_orphan_docstring():
    with pytest.raises(ParseError, match="docstring must immediately follow"):
        parse_config('"""orphan"""\n')


def test_rejects_function_call():
    with pytest.raises(ParseError, match="disallowed expression"):
        parse_config("X = len([1])\n")
