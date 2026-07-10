"""Test load, modify values in code, and save back via document API."""

import shutil

import pytest

import python_config
from python_config import ValidationError


@pytest.fixture
def example_copy(confpath, tmpdir):
    path = tmpdir.join("test.conf")
    shutil.copy(confpath, str(path))
    return str(path)


def test_modify_scalar_preserves_other_assignments(example_copy):
    doc = python_config.document.load(example_copy)
    assert doc["LOG_LEVEL"] == 3
    doc["LOG_LEVEL"] = 5

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)
    assert again["LOG_LEVEL"] == 5
    assert "BUILD_NUMBER = 7" in text
    assert "PROJECT_NAME" in text
    assert "NOTE: This commentary" in again.preamble


def test_modify_scalar_visible_via_simple_load(example_copy):
    doc = python_config.document.load(example_copy)
    doc["LOG_LEVEL"] = 5
    with open(example_copy, "w") as out:
        python_config.document.dump(out, doc)

    assert python_config.load(example_copy)["log_level"] == 5


def test_dumps_ext_conf_matches_canonical(confpath):
    ext_path = confpath.parent / "pyproject_like_ext.conf"
    doc = python_config.document.load(ext_path)

    with open(confpath) as source:
        assert python_config.document.dumps(doc) == source.read()


def test_modify_project_name_keeps_evaluated_metadata_literals(example_copy):
    doc = python_config.document.load(example_copy)
    doc["PROJECT_NAME"] = "renamed"
    again = python_config.document.loads(python_config.document.dumps(doc))
    assert again["PROJECT_NAME"] == "renamed"
    hook = next(
        entry["value"] for entry in again["METADATA"] if entry["name"] == "default-smoke-hook"
    )
    # Evaluated at load; changing PROJECT_NAME does not re-evaluate nested literals.
    assert hook == ".github/hooks/smoke-python-config"


def test_file_roundtrip(example_copy):
    doc = python_config.document.load(example_copy)
    doc["LOG_LEVEL"] = 99
    with open(example_copy, "w") as out:
        python_config.document.dump(out, doc)

    again = python_config.document.load(example_copy)
    assert again["LOG_LEVEL"] == 99
    text = python_config.document.dumps(again)
    assert "BUILD_NUMBER = 7" in text


def test_setitem_rejects_invalid_type(confpath):
    doc = python_config.document.loads(confpath.read_text())
    with pytest.raises(ValidationError):
        doc["LOG_LEVEL"] = object()


def test_dumps_rejects_invalid_document(confpath):
    doc = python_config.document.loads(confpath.read_text())
    doc.items[0].value = object()
    with pytest.raises(ValidationError):
        python_config.document.dumps(doc)


def test_modify_top_level(confpath):
    doc = python_config.document.load(confpath)

    # Numbers
    assert doc["CLOG_LEVEL"] == -1
    assert doc["LOG_LEVEL"] == 3
    doc["CLOG_LEVEL"], doc["LOG_LEVEL"] = doc["LOG_LEVEL"], doc["CLOG_LEVEL"]

    # Consequent reassignment
    doc["APPROX_FRIDGE_TEMP_C"] += 5
    doc["APPROX_FRIDGE_TEMP_C"] = 6

    # Booleans
    assert doc["ENABLED"] is True
    assert doc["DISABLED"] is False
    doc["ENABLED"], doc["DISABLED"] = doc["DISABLED"], doc["ENABLED"]

    # F-strings evaluated at load
    assert doc["PACKAGE_NAME"] == "python-config-1.0.0"
    assert doc["PACKAGE_FULLNAME"] == "python-config-1.0.0.7"

    # Arithmetic evaluated at load
    assert doc["BUILD_NUMBER"] == 7
    doc["BUILD_NUMBER"] = 10

    doc["PACKAGE_NAME"] = "pkg-python-config-1.0.0"
    assert doc["PACKAGE_NAME"] == "pkg-python-config-1.0.0"
    assert doc["PACKAGE_FULLNAME"] == "python-config-1.0.0.7"

    # Lists (flat)
    assert doc["CLASSIFIERS"] == [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ]
    doc["CLASSIFIERS"][0] = "Development Status :: 5 - Production/Stable"
    doc["CLASSIFIERS"].append("Programming Language :: Python :: 3.10")

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)

    assert again["CLOG_LEVEL"] == 3
    assert again["LOG_LEVEL"] == -1

    # Consequent reassignment
    assert again["APPROX_FRIDGE_TEMP_C"] == 6

    assert "BUILD_NUMBER = 10" in text
    assert again["BUILD_NUMBER"] == 10

    assert 'PACKAGE_NAME = "pkg-python-config-1.0.0"' in text
    assert again["PACKAGE_NAME"] == "pkg-python-config-1.0.0"
    assert again["PACKAGE_FULLNAME"] == "python-config-1.0.0.7"

    # Booleans
    assert again["ENABLED"] is False
    assert again["DISABLED"] is True

    # Lists
    assert again["CLASSIFIERS"] == [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ]


def test_modify_nested_structures(confpath):
    doc = python_config.document.load(confpath)

    # Lists (of dicts)
    assert doc["METADATA"] == [
        {
            "name": "default-pr-template",
            "value": ".github/templates/pr.md",
        },
        {
            "name": "default-smoke-hook",
            "value": f".github/hooks/smoke-{doc['PROJECT_NAME']}",  # evaluted ofc
        },
        {
            "name": "max-test-duration-ms",
            "value": 2 * 1000 * 60,  # evaluated ofc
        },
    ]
    doc["METADATA"][0]["value"] = ".github/templates/pr-v2.md"

    # NOTE: changing order!
    doc["METADATA"][1], doc["METADATA"][2] = doc["METADATA"][2], doc["METADATA"][1]

    # NOTE: adding new entry
    doc["METADATA"].append({"name": "doc-auto-translation-hook", "value": ".github/hooks/dat.sh"})

    # Changing str in dict
    assert doc["PROJECT"]["readme"] == "README.rst"
    doc["PROJECT"]["readme"] = "README.org"

    # Deleting root-level key and adding new
    assert doc["PROJECT"]["dynamic"] == ["version"]
    assert "version" not in doc["PROJECT"]
    del doc["PROJECT"]["dynamic"]
    doc["PROJECT"]["version"] = doc["VERSION"]

    # Changing list in dict
    assert doc["PROJECT"]["keywords"] == ["ast", "config", "library"]
    doc["PROJECT"]["keywords"].insert(0, "python")
    doc["PROJECT"]["keywords"][2] = "configuration"

    assert doc["PROJECT"]["tools"]["ruff"]["line-length"] == 100
    doc["PROJECT"]["tools"]["ruff"]["line-length"] = 120

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)

    assert again["METADATA"] == [
        {
            "name": "default-pr-template",
            "value": ".github/templates/pr-v2.md",
        },
        {
            "name": "max-test-duration-ms",
            "value": 2 * 1000 * 60,  # evaluated ofc
        },
        {
            "name": "default-smoke-hook",
            "value": f".github/hooks/smoke-{doc['PROJECT_NAME']}",  # evaluted ofc
        },
        {
            "name": "doc-auto-translation-hook",
            "value": ".github/hooks/dat.sh",
        },
    ]

    # Dicts (deep nested everything)
    # Deleting root-level key and adding new
    assert "dynamic" not in again["PROJECT"]
    assert again["PROJECT"]["version"] == "1.0.0"

    assert again["PROJECT"]["readme"] == "README.org"
    assert again["PROJECT"]["keywords"] == ["python", "ast", "configuration", "library"]

    assert again["PROJECT"]["tools"]["ruff"]["line-length"] == 120


def test_modify_nested_values(confpath):
    doc = python_config.document.load(confpath)

    assert doc["METADATA"][2]["value"] == 2 * 1000 * 60
    assert doc["METADATA"][1]["value"] == ".github/hooks/smoke-python-config"
    assert doc["PROJECT"]["tools"]["sphinx-upload"]["path"] == "docs/python-config/1.0.0"

    doc["METADATA"][2]["value"] = 180000
    assert doc["METADATA"][2]["value"] == 180000
    assert doc["METADATA"][2]["value"] // 60 == 3000

    doc["METADATA"][1]["value"] = ".github/hooks/smoke-python-config"
    doc["PROJECT"]["tools"]["sphinx-upload"]["path"] = "docs/python-config/1.0.0"

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)

    assert "180000" in text
    assert ".github/hooks/smoke-python-config" in text
    assert '"path": "docs/python-config/1.0.0"' in text
    assert "3 * 60 * 1000" not in text
    assert '= f"' not in text

    assert again["METADATA"][2]["value"] == 180000
    assert again["METADATA"][1]["value"] == ".github/hooks/smoke-python-config"
    assert again["PROJECT"]["tools"]["sphinx-upload"]["path"] == "docs/python-config/1.0.0"


def test_modify_list(confpath):
    doc = python_config.document.load(confpath)

    assert doc["METADATA"] == [
        {
            "name": "default-pr-template",
            "value": ".github/templates/pr.md",
        },
        {
            "name": "default-smoke-hook",
            "value": ".github/hooks/smoke-python-config",
        },
        {
            "name": "max-test-duration-ms",
            "value": 2 * 1000 * 60,
        },
    ]
    metadata = doc["METADATA"]
    metadata[:] = metadata[::-1]

    assert doc["CLASSIFIERS"] == [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ]
    classifiers = doc["CLASSIFIERS"]
    classifiers[0:2] = classifiers[1::-1]

    assert doc["PROJECT"]["keywords"] == ["ast", "config", "library"]
    keywords = doc["PROJECT"]["keywords"]
    keywords[:] = keywords[1:] + keywords[:1]

    rules = doc["PROJECT"]["tools"]["ruff"]["rules"]
    assert rules == ["E", "A", "B"]
    rules[:] = rules[::-1]

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)

    assert again["METADATA"] == [
        {
            "name": "max-test-duration-ms",
            "value": 120000,
        },
        {
            "name": "default-smoke-hook",
            "value": ".github/hooks/smoke-python-config",
        },
        {
            "name": "default-pr-template",
            "value": ".github/templates/pr.md",
        },
    ]
    assert "smoke-{PROJECT_NAME}" not in text
    assert "2 * 1000 * 60" not in text

    assert again["CLASSIFIERS"] == [
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ]

    assert again["PROJECT"]["keywords"] == ["config", "library", "ast"]
    assert again["PROJECT"]["tools"]["ruff"]["rules"] == ["B", "A", "E"]


def test_modify_dict(confpath):
    doc = python_config.document.load(confpath)

    assert doc["PROJECT"]["readme"] == "README.rst"
    assert doc["PROJECT"]["dynamic"] == ["version"]
    assert doc["PROJECT"]["tools"]["sphinx-upload"]["path"] == "docs/python-config/1.0.0"

    project = doc["PROJECT"]
    project["readme"] = "README.org"
    del project["dynamic"]
    project["version"] = doc["VERSION"]
    project["tools"]["ruff"]["line-length"] = 120

    authors = project["authors"]
    authors[0], authors[1] = authors[1], authors[0]

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)

    assert "smoke-{PROJECT_NAME}" not in text
    assert "2 * 1000 * 60" not in text
    assert 'f"docs/{PROJECT_NAME}/{VERSION}"' not in text
    assert '"path": "docs/python-config/1.0.0"' in text

    assert again["PROJECT"]["readme"] == "README.org"
    assert "dynamic" not in again["PROJECT"]
    assert again["PROJECT"]["version"] == "1.0.0"
    assert again["PROJECT"]["tools"]["ruff"]["line-length"] == 120
    assert again["PROJECT"]["authors"] == [
        {
            "name": "Pavel Kulyov",
            "email": "kulyov.pavel@gmail.com",
        },
        {
            "name": "Dmitry Konishchev",
            "email": "konishchev@gmail.com",
        },
    ]


def test_add_remove_top_level(confpath):
    doc = python_config.document.load(confpath)
    assert doc == python_config.document.loads(python_config.document.dumps(doc))

    # add new
    doc["METADATA2"] = [dict(item) for item in doc["METADATA"]]
    assert doc["METADATA2"] == doc["METADATA"]

    # remove existing root-level assignment
    assert "PACKAGE_FULLNAME" in doc
    del doc["PACKAGE_FULLNAME"]
    assert "PACKAGE_FULLNAME" not in doc.names()

    # remove nested dict key
    assert "readme" in doc["PROJECT"]
    del doc["PROJECT"]["readme"]
    assert "readme" not in doc["PROJECT"]

    text = python_config.document.dumps(doc)
    again = python_config.document.loads(text)

    assert "METADATA2" in again
    assert again["METADATA2"] == again["METADATA"]

    assert "PACKAGE_FULLNAME" not in again
    assert "readme" not in again["PROJECT"]

    assert python_config.document.loads(python_config.document.dumps(again)) == again
