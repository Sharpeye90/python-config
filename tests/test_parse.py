"""Tests for python_config.parse."""

import pytest

from python_config.parse import ParseError, parse_config


def test_parse_config(confpath):
    # Empty file is ok
    doc = parse_config("")
    assert doc.preamble == ""
    assert doc.module_docstring is None
    assert doc.items == []

    # Only module docstring still ok
    doc = parse_config('"""module only"""\n')
    assert doc.preamble == ""
    assert doc.module_docstring == "module only"
    assert doc.items == []

    # Single var
    doc = parse_config("VAR = 'val'")
    assert doc.preamble == ""
    assert doc.module_docstring is None
    assert len(doc.items) == 1
    assert doc["VAR"] == "val"
    assert doc.getvar("VAR").docstring is None

    doc = parse_config(confpath.read_text())
    assert "# vim: set tf=python:" in doc.preamble
    assert "NOTE: This commentary" in doc.preamble

    assert doc["PROJECT_NAME"] == "python-config"
    assert doc["BUILD_NUMBER"] == 7
    assert doc["ENABLED"] is True

    assert doc.getvar("VERSION").docstring == "PEP 440 version string."
    assert doc.getvar("TWEAKS_CHUNK_SIZE").docstring == "Chunk size for IO operations."
    assert doc.getvar("PROJECT_NAME").docstring is None
    assert doc.module_docstring == "Module docstrings are supported too."

    with pytest.raises(ParseError, match="docstring must immediately follow"):
        parse_config('"""module"""\n"""orphan"""\n')

    with pytest.raises(ParseError, match="disallowed expression"):
        parse_config("X = len([1])\n")
