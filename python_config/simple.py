"""Load-wise backward compatible implementation.

NOTE: except of changed `load(path, contents=None)` -> `load(path)` signature.
"""

import pathlib

from . import parse
from .exceptions import (
    FileReadingError,
    FileWritingError,
    ParsingError,
    ValidationError,
    _ValidationError,
)
from .models import ConfigDocument
from .serialize import serialize_config
from .validation import _validate_public_items, _validate_value


def load(path):
    """Loads a configuration file."""

    try:
        with open(path) as config_file:
            contents = config_file.read()
    except OSError as e:
        raise FileReadingError(path, e)

    return _loads(contents, path=path)


def loads(contents):
    """Load a configuration from string."""

    return _loads(contents)


def _loads(contents, path=None):
    """Common loading function that handles path."""

    try:
        document = parse.parse_config(contents)
    except Exception as e:
        raise ParsingError(path or "<string>", e)

    return _validate_public_items(document, path or "<string>")


def dumps(obj):
    """Serialize a configuration dict to a string.

    Validation on write is necessary to ensure it can be loaded in the future.
    """

    validated = {}
    for key, value in obj.items():
        name = key.upper()
        try:
            validated[key] = _validate_value(name, value)
        except _ValidationError as e:
            raise ValidationError("<string>", e)

    document = ConfigDocument.from_dict(validated)
    return serialize_config(document)


def dump(out, obj):
    """Serialize a configuration dict and write it to a file-like object."""

    # String to Path
    if isinstance(out, str):
        out = pathlib.Path(out)

    # Path processing ends here
    if isinstance(out, pathlib.PurePath):
        try:
            out.write_text(dumps(obj))
            return
        except EnvironmentError as e:
            raise FileWritingError(out, e)

    # Opened file is the last option
    if not hasattr(out, "write"):
        raise FileWritingError(out, IOError("out must be string, pathlib object or opened file"))

    try:
        out.write(dumps(obj))
    except EnvironmentError as e:
        path = getattr(out, "name", "")
        raise FileWritingError(path, e)
