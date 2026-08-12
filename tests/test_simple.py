"""Tests for python_config.simple."""

import errno
import io
import os
import tempfile

import pytest

from python_config import simple
from python_config.exceptions import FileReadingError, ParsingError, ValidationError
from python_config.validation import _validate_value


# NOTE: ignore the imp module deprecation warning, this code will be deleted later.
def reference_load_impl(source):
    import imp

    config_module = imp.new_module("config")
    config_module.__file__ = "some/path.py"

    exec(compile(source, "some/path.py", "exec"), config_module.__dict__)

    config = {}

    for option, value in config_module.__dict__.items():
        if not option.startswith("_") and option.isupper():
            try:
                config[option.lower()] = _validate_value(option, value)
            except Exception as e:
                raise ValidationError("some/path.py", e)

    return config


def test_load(confpath):
    """Brief test that config loads correctly."""

    conf = simple.load(confpath)
    assert isinstance(conf, dict)
    assert conf["project_name"] == "python-config"
    assert conf["build_number"] == 7
    assert len(conf["metadata"]) == 3
    assert conf["project"]["tools"]["sphinx-upload"] == {"path": "docs/python-config/1.0.0"}

    sources = confpath.read_text()
    assert conf == simple.loads(sources) == reference_load_impl(sources)


def test_load_missing_file():
    assert (
        pytest.raises(
            FileReadingError,
            lambda: simple.load("missing.conf"),
        ).value.errno
        == errno.ENOENT
    )


def test_no_access():
    with tempfile.NamedTemporaryFile() as config:
        os.chmod(config.name, 0)

        assert (
            pytest.raises(FileReadingError, lambda: simple.load(config.name)).value.errno
            == errno.EACCES
        )


def test_dumps_roundtrip():
    obj = {"key": "value", "count": 42, "enabled": True}
    text = simple.dumps(obj)
    assert simple.loads(text) == obj


def test_dump_to_file_like():
    obj = {"alpha": 1, "beta": "two"}
    buf = io.StringIO()
    simple.dump(buf, obj)
    assert simple.loads(buf.getvalue()) == obj


def test_dumps_invalid_type():
    with pytest.raises(ValidationError):
        simple.dumps({"bad": object()})


def test_dumps_uppercase_keys():
    text = simple.dumps({"my_opt": "x"})
    assert "MY_OPT" in text
    assert "my_opt" not in text.split("=")[0]


def test_dumps_nested_dict_formatted():
    text = simple.dumps({"data": {"a": 1, "b": {"c": 2}}})
    assert "\n    " in text
    assert '"a": 1,' in text or "'a': 1," in text
    assert simple.loads(text) == {"data": {"a": 1, "b": {"c": 2}}}


def test_loads_rejects_string_arithmetic():
    with pytest.raises(ParsingError):
        simple.loads('X = "a" + "b"')


def test_loads_rejects_name_in_expression():
    with pytest.raises(ParsingError):
        simple.loads("X = OTHER + 1")


def test_loads_rejects_fstring_format_spec():
    with pytest.raises(ParsingError):
        simple.loads('X = 1\nY = f"{X:.2f}"\n')


def test_loads_invalid_type():
    with pytest.raises(ParsingError):
        simple.loads("OS = object()")


def test_loads_invalid_dict_key():
    with pytest.raises(ParsingError):
        simple.loads("A = {}; B = { (0, 1): 2 }")


def test_loads_invalid_syntax():
    with pytest.raises(ParsingError):
        simple.loads("a=")


def test_loads_rejects_import():
    with pytest.raises(ParsingError):
        simple.loads("import sys\nX = 1\n")
