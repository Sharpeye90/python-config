A library for reading Python configuration files
================================================

About
-----

This library reads configuration files that are represented as Python modules
with restricted syntax. It uses the AST for parsing.
Values can be written back with ``dump`` and ``dumps``.

Two APIs are available:

* ``python_config.load(s)`` / ``dump(s)`` — read and write a **dict** (lowercase keys).

* ``python_config.document.load(s)`` / ``dump(s)`` — read and write a
  :class:`~python_config.document.ConfigDocument`. Use this to change option
  values from code and save the file back. Top-level options use uppercase names
  (e.g. ``doc["LOG_LEVEL"] = 5``). Nested ``list`` and ``dict`` values are
  plain Python objects; in-place mutations are reflected on dump.

Supported value types are:
- ``bool``,
- ``int``,
- ``float``,
- ``str``,
- ``list``,
- ``dict`` (with string keys).

Only **uppercase** names that do not start with ``_`` are exposed through the dict API.

Expressions in source files are **evaluated on load**:

* Arithmetic (e.g. ``COUNT = 1 + 2 * 3``)
* F-strings that reference earlier options (e.g. ``ENDPOINT = f"{HOST}:{PORT}"``)

``dump`` and ``dumps`` always emit **literal values** with aggressive formatting applied.
Hand-edited spacing and expression forms are not preserved on save.

Preamble comments, a module-level docstring, and per-assignment docstrings are
preserved through the document API.

.. NOTE::

   If you want to validate the configuration values, take a look at
   https://github.com/KonishchevDmitry/object-validator project or just use Pydantic.

Tests
-----

It's recommended to test against python3.6. Assuming here you have .venv36 for this.

.. source:: bash

   poe test

   # python 3.6
   .venv36/bin/pytest -s -vvv tests/
