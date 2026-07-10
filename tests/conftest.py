from pathlib import Path

import pytest

import python_config.document


def generate_huge_config():
    """Build an over-15k-line config source string for benchmark fixtures."""

    lines = []
    for index in range(1, 201):
        lines.append('VAR{0} = "val{0}"'.format(index))
        if index % 2 == 1:
            lines.append('"""Docstring for VAR{0}."""'.format(index))

    lines.append("MEGASTRUCT = {")
    lines.append('    "sub1": [')

    for index in range(1, 3001):
        lines.append(
            '        {{"name": "sub1-{0}", "val": "val1-{0}", "index": {0}}},'.format(index)
        )
    lines.append("    ],")
    lines.append('    "sub2": {')
    lines.append('        "sub2-sub1": {')
    lines.append('            "somethings": [')

    for index in range(1, 12001):
        lines.append(
            '                {{"name": "sub2-sub1-{0}", "val": "val1-{0}", "index": {0}}},'.format(
                index
            )
        )
    lines.append("            ],")
    lines.append("        },")
    lines.append("    },")
    lines.append("}")

    return "\n".join(lines) + "\n"


@pytest.fixture(scope="session")
def confpath():
    """Return the path to testing configuration file."""

    return Path(__file__).parent / "pyproject_like.conf"


@pytest.fixture(scope="session")
def confdoc(confpath):
    """Return parsed testing configuration file."""

    return python_config.document.load(confpath)


@pytest.fixture(scope="session")
def huge_conf_path(tmpdir_factory):
    """Return path to a generated huge config file."""

    source = generate_huge_config()
    assert source.count("\n") >= 15000

    path = tmpdir_factory.mktemp("huge").join("huge.conf")
    path.write(source)

    return Path(str(path))
