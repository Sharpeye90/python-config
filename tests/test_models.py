"""Tests for python_config.models."""

from python_config.document import dumps, load, loads
from python_config.models import Assignment


def test_assignment_equality():
    left = Assignment(name="COUNT", value=7)
    right = Assignment(name="COUNT", value=7)
    assert left is not right
    assert left == right


def test_assignment_inequality_on_value_or_docstring():
    base = Assignment(name="X", value=1)
    assert base != Assignment(name="Y", value=1)
    assert base != Assignment(name="X", value=2)
    assert base != Assignment(name="X", value=1, docstring="note")


def test_list_mutation(confpath):
    doc = load(confpath)
    classifiers = doc["CLASSIFIERS"]

    assert isinstance(classifiers, list)
    assert len(classifiers) == 4
    assert classifiers == [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ]
    assert repr(classifiers) == repr(classifiers[:])

    assert classifiers[0] == "Development Status :: 4 - Beta"
    assert classifiers[1:3] == [
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ]

    classifiers.insert(0, "Topic :: Software Development :: Libraries")
    classifiers.append("Programming Language :: Python :: 3.11")
    classifiers.extend(
        [
            "Private :: Do Not Upload",
            "Environment :: Console",
        ]
    )
    classifiers[1] = "Development Status :: 5 - Production/Stable"
    classifiers[1], classifiers[2] = classifiers[2], classifiers[1]
    classifiers[3] = "Programming Language :: Python :: 3.10"
    classifiers.remove("Private :: Do Not Upload")
    classifiers.pop()
    del classifiers[1]

    assert classifiers == [
        "Topic :: Software Development :: Libraries",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
    ]

    metadata = doc["METADATA"]
    assert isinstance(metadata, list)
    assert len(metadata) == 3
    assert isinstance(metadata[0], dict)
    assert [entry["name"] for entry in metadata] == [
        "default-pr-template",
        "default-smoke-hook",
        "max-test-duration-ms",
    ]
    metadata.append(
        {
            "name": "doc-auto-translation-hook",
            "value": ".github/hooks/dat.sh",
        }
    )
    metadata[1], metadata[2] = metadata[2], metadata[1]
    assert metadata[1]["name"] == "max-test-duration-ms"
    assert metadata[2]["name"] == "default-smoke-hook"

    doc["ARITH_LIST"] = [100, 200, 300]
    arith = doc["ARITH_LIST"]
    assert isinstance(arith, list)

    arith[1] = 200
    assert arith[1] == 200
    arith.clear()
    assert len(arith) == 0
    arith.extend([199, 200, 201])

    text = dumps(doc)
    again = loads(text)

    assert again["CLASSIFIERS"] == [
        "Topic :: Software Development :: Libraries",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
    ]
    assert again["METADATA"] == [
        {
            "name": "default-pr-template",
            "value": ".github/templates/pr.md",
        },
        {
            "name": "max-test-duration-ms",
            "value": 120000,
        },
        {
            "name": "default-smoke-hook",
            "value": ".github/hooks/smoke-python-config",
        },
        {
            "name": "doc-auto-translation-hook",
            "value": ".github/hooks/dat.sh",
        },
    ]
    assert again["ARITH_LIST"] == [199, 200, 201]
    assert "ARITH_LIST = [" in text


def test_dict_mutation(confpath):
    doc = load(confpath)
    project = doc["PROJECT"]

    assert isinstance(project, dict)
    assert len(project) == len(doc.to_dict()["project"])

    assert project["name"] == "python-config"
    assert "name" in project and "name" in project.keys()
    assert "missing-key" not in project
    assert list(project.keys()) == list(project) == list(doc.to_dict()["project"])

    assert list(project.values()) == list(doc.to_dict()["project"].values())
    assert ("name", "python-config") in project.items()

    project.update(
        {
            "description": "Updated description",
            "license": "MIT",
        }
    )
    assert project["description"] == "Updated description"

    assert "build-backend" not in project
    assert project.setdefault("build-backend", "setuptools") == "setuptools"
    assert project["build-backend"] == "setuptools"
    assert project.setdefault("name", "other") == "python-config"
    assert project.pop("build-backend") == "setuptools"
    assert "build-backend" not in project

    ruff = project["tools"]["ruff"]
    assert isinstance(ruff, dict)
    popped_key, popped_value = ruff.popitem()
    ruff[popped_key] = popped_value
    assert ruff["line-length"] == 100

    keywords = project["keywords"]
    assert isinstance(keywords, list)
    keywords.clear()
    assert project["keywords"] == keywords == []
    keywords.extend(["python", "config", "library"])
    assert project["keywords"] == ["python", "config", "library"]

    del project["license"]
    project["readme"] = "README.md"
    project["version"] = doc["VERSION"]

    sphinx = project["tools"]["sphinx-upload"]
    assert sphinx["path"] == "docs/python-config/1.0.0"
    sphinx["path"] = "docs/python-config/latest"
    assert sphinx["path"] == "docs/python-config/latest"

    project["tools"]["mypy"] = {"strict": True}
    assert project["tools"]["mypy"]["strict"] is True

    text = dumps(doc)
    again = loads(text)

    assert again["PROJECT"]["description"] == "Updated description"
    assert "license" not in again["PROJECT"]
    assert again["PROJECT"]["readme"] == "README.md"
    assert again["PROJECT"]["version"] == "1.0.0"
    assert again["PROJECT"]["keywords"] == ["python", "config", "library"]
    assert again["PROJECT"]["tools"]["ruff"]["line-length"] == 100
    assert again["PROJECT"]["tools"]["mypy"] == {"strict": True}
    assert again["PROJECT"]["tools"]["sphinx-upload"]["path"] == "docs/python-config/latest"
    assert '"path": "docs/python-config/latest"' in text
