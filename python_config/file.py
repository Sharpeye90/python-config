from __future__ import unicode_literals

import imp

from .exceptions import FileReadingError, ParsingError, ValidationError, _ValidationError
from .validation import _validate_value


def load(path, contents=None):
    """Loads a configuration file."""

    config_module = imp.new_module("config")
    config_module.__file__ = path

    if contents is None:
        try:
            with open(path) as config_file:
                contents = config_file.read()
        except EnvironmentError as e:
            raise FileReadingError(path, e)

    try:
        exec(compile(contents, path, "exec"), config_module.__dict__)
    except Exception as e:
        raise ParsingError(path, e)

    config = {}

    for option, value in config_module.__dict__.items():
        if not option.startswith("_") and option.isupper():
            try:
                config[option.lower()] = _validate_value(option, value)
            except _ValidationError as e:
                raise ValidationError(path, e)

    return config
