from __future__ import unicode_literals

from ._compat import _BASIC_TYPES, _VALID_TYPES
from .exceptions import _ValidationError


def _validate_value(option, value, valid_types=_VALID_TYPES):
    """Validates an option value."""

    value_type = type(value)

    if value_type not in valid_types:
        raise _ValidationError(option,
            "{option} has an invalid value type ({type}). Allowed types: {valid_types}.",
            option=option, type=value_type.__name__,
            valid_types=", ".join(t.__name__ for t in valid_types))

    if value_type is dict:
        value = _validate_dict(option, value)
    elif value_type is list:
        value = _validate_list(option, value)
    elif value_type is tuple:
        value = _validate_tuple(option, value)
    elif value_type is set:
        value = _validate_set(option, value)
    elif value_type is bytes:
        try:
            value = value.decode()
        except UnicodeDecodeError as e:
            raise _ValidationError(option, "{0} has an invalid value: {1}.", option, e)

    return value


def _validate_dict(option, dictionary):
    """Validates a dictionary."""

    for key, value in tuple(dictionary.items()):
        valid_key = _validate_value("A {0}'s key".format(option),
            key, valid_types=_BASIC_TYPES)

        valid_value = _validate_value("{0}[{1}]".format(option, repr(key)), value)

        if valid_key is not key:
            del dictionary[key]
            dictionary[valid_key] = valid_value
        elif valid_value is not value:
            dictionary[valid_key] = valid_value

    return dictionary


def _validate_list(option, sequence):
    """Validates a list."""

    for index, value in enumerate(sequence):
        valid_value = _validate_value("{0}[{1}]".format(option, index), value)
        if valid_value is not value:
            sequence[index] = valid_value

    return sequence


def _validate_tuple(option, sequence):
    """Validates a tuple."""

    return [
        _validate_value("{0}[{1}]".format(option, index), value)
        for index, value in enumerate(sequence)
    ]


def _validate_set(option, sequence):
    """Validates a set."""

    return [
        _validate_value("A {0}'s key".format(option), value)
        for value in sequence
    ]
