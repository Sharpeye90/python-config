import pathlib

from . import parse
from .exceptions import (
    FileReadingError,
    FileWritingError,
    ParsingError,
)
from .models import Assignment, ConfigDocument
from .serialize import serialize_config
from .validation import _validate_document_items


def load(path):
    """Load a configuration file into a :class:`ConfigDocument`."""

    try:
        with open(path) as config_file:
            contents = config_file.read()
    except OSError as e:
        raise FileReadingError(path, e)

    return loads(contents, path=path)


def loads(contents, path=None):
    """Load configuration source into a :class:`ConfigDocument`."""

    try:
        document = parse.parse_config(contents)
    except Exception as e:
        raise ParsingError(path or "<string>", e)
    _validate_document_items(document, path or "<string>")
    return document


def dumps(document):
    """Serialize a :class:`ConfigDocument` to a configuration source string."""

    _validate_document_items(document, "<string>")
    return serialize_config(document)


def dump(out, document):
    """Serialize a :class:`ConfigDocument` and write it to a file-like object."""

    # String to Path
    if isinstance(out, str):
        out = pathlib.Path(out)

    # Path processing ends here
    if isinstance(out, pathlib.PurePath):
        try:
            out.write_text(dumps(document))
            return
        except EnvironmentError as e:
            raise FileWritingError(out, e)

    # Opened file is the last option
    if not hasattr(out, "write"):
        raise FileWritingError(out, IOError("out must be string, pathlib object or opened file"))

    try:
        out.write(dumps(document))
    except EnvironmentError as e:
        path = getattr(out, "name", "")
        raise FileWritingError(path, e)


__all__ = [
    "Assignment",
    "ConfigDocument",
    "dump",
    "dumps",
    "load",
    "loads",
]
