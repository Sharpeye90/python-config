"""Tests for python_config.document."""

import io

import pytest

from python_config import document
from python_config.exceptions import ParsingError
from python_config.models import ConfigDocument


MINIMAL_SOURCE = '''\
# section
NAME = "app"

COUNT = 2 + 3
"""Five."""
'''


def test_load(confpath):
    doc = document.load(confpath)

    assert isinstance(doc, ConfigDocument)
    assert doc["PROJECT_NAME"] == "python-config"
    assert doc["BUILD_NUMBER"] == 7
    assert doc["VERSION"] == "1.0.0"
    assert "NOTE: This commentary" in doc.preamble

    assert doc["METADATA"] == [
        {
            "name": "default-pr-template",
            "value": ".github/templates/pr.md",
        },
        {
            "name": "default-smoke-hook",
            "value": f".github/hooks/smoke-{doc['PROJECT_NAME']}",
        },
        {
            "name": "max-test-duration-ms",
            "value": 2 * 1000 * 60,
        },
    ]


def test_loads(confpath):
    doc = document.loads(MINIMAL_SOURCE)

    assert isinstance(doc, ConfigDocument)
    assert doc.preamble.startswith("# section")
    assert doc["NAME"] == "app"
    assert doc["COUNT"] == 5

    assert doc.getvar("COUNT").docstring == "Five."

    with pytest.raises(ParsingError):
        document.loads("NOT_AN_ASSIGNMENT()\n")


def test_dump():
    doc = document.loads(MINIMAL_SOURCE)
    buffer = io.StringIO()

    document.dump(buffer, doc)

    again = document.loads(buffer.getvalue())
    assert again["NAME"] == "app"
    assert again["COUNT"] == 5
    assert again.preamble.startswith("# section")


def test_dumps(confpath):
    doc = document.load(confpath)
    text = document.dumps(doc)

    with open(confpath) as source:
        assert text == source.read()


def test_load_dumped(confpath):
    doc = document.load(confpath)
    assert doc == document.loads(document.dumps(doc))


def test_dump_example_formatted(confpath):
    doc = document.load(confpath)
    text = document.dumps(doc)
    assert "NOTE: This commentary" in doc.preamble
    assert '"""Module docstrings are supported too."""' in text
    assert "BUILD_NUMBER = 7" in text
    assert 'PACKAGE_NAME = "python-config-1.0.0"' in text
    assert ".github/hooks/smoke-python-config" in text
    assert '"""PEP 440 version string."""' in text
    assert "# str without docstring" not in text
    assert "1 + 2 * 3" not in text
    assert '= f"' not in text


def test_section_comment_not_preserved_on_dump():
    source = '# preamble\n"""mod"""\n# section\nX = 1\n'
    doc = document.loads(source)
    assert "# section" not in document.dumps(doc)
    assert doc.preamble.startswith("# preamble")


def test_setvar_updates_value_and_docstring(confpath):
    doc = document.load(confpath)
    doc.setvar("LOG_LEVEL", 99, docstring="High verbosity.")
    item = doc.getvar("LOG_LEVEL")
    assert item.value == 99
    assert item.docstring == "High verbosity."


def test_setvar_docstring_only(confpath):
    doc = document.load(confpath)
    doc.setvar("VERSION", docstring="Updated note.")
    assert doc.getvar("VERSION").value == "1.0.0"
    assert doc.getvar("VERSION").docstring == "Updated note."


def test_setvar_clears_docstring(confpath):
    doc = document.load(confpath)
    doc.setvar("VERSION", docstring=None)
    assert doc.getvar("VERSION").docstring is None


def test_setvar_new_assignment():
    doc = document.loads('X = 1\n"""note."""\n')
    doc.setvar("NEW_OPT", 42, docstring="Brand new.")
    assert doc["NEW_OPT"] == 42
    assert doc.getvar("NEW_OPT").docstring == "Brand new."


def test_setvar_requires_value_for_new_assignment():
    doc = document.loads("X = 1\n")
    with pytest.raises(TypeError):
        doc.setvar("Y", docstring="only doc")


def test_setvar_requires_value_or_docstring(confpath):
    doc = document.load(confpath)
    with pytest.raises(TypeError):
        doc.setvar("LOG_LEVEL")
