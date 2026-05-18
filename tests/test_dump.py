"""Test configuration serialization."""

import io

import pytest

import python_config


def test_dumps_roundtrip():
    obj = {"key": "value", "count": 42, "enabled": True}
    text = python_config.dumps(obj)
    assert python_config.loads(text) == obj


def test_dump_to_file_like():
    obj = {"alpha": 1, "beta": "two"}
    buf = io.StringIO()
    python_config.dump(buf, obj)
    assert python_config.loads(buf.getvalue()) == obj


def test_dumps_invalid_type():
    with pytest.raises(python_config.ValidationError):
        python_config.dumps({"bad": object()})


def test_dumps_uppercase_keys():
    text = python_config.dumps({"my_opt": "x"})
    assert "MY_OPT" in text
    assert "my_opt" not in text.split("=")[0]
