from .exceptions import ValidationError, _ValidationError


_BASIC_TYPES = (bool, int, float, str)
"""Python basic types."""

_COMPLEX_TYPES = (list, dict)
"""Python complex types."""

_VALID_TYPES = _BASIC_TYPES + _COMPLEX_TYPES
"""Option value must be one of these types."""


def _validate_public_items(document, path):
    """Validate public uppercase assignments and return a lowercase-key dict."""

    config = {}

    for item in document.items:
        if not item.name.startswith("_") and item.name.isupper():
            try:
                config[item.name.lower()] = _validate_value(item.name, item.value)
            except _ValidationError as e:
                raise ValidationError(path, e)

    return config


def _validate_document_items(document, path):
    """Validate public uppercase assignments in a document (in place)."""

    for item in document.items:
        if not item.name.startswith("_") and item.name.isupper():
            try:
                _validate_value(item.name, item.value)
            except _ValidationError as e:
                raise ValidationError(path, e)


def _validate_value(option, value, valid_types=_VALID_TYPES):
    """Validates an option value."""

    value_type = type(value)

    if value_type not in valid_types:
        raise _ValidationError(
            option,
            "{option} has an invalid value type ({type}). Allowed types: {valid_types}.",
            option=option,
            type=value_type.__name__,
            valid_types=", ".join(t.__name__ for t in valid_types),
        )

    if value_type is dict:
        value = _validate_dict(option, value)
    elif value_type is list:
        value = _validate_list(option, value)
    return value


def _validate_dict(option, dictionary):
    """Validates a dictionary."""

    for key, value in tuple(dictionary.items()):
        valid_key = _validate_value(
            "A {0}'s key".format(option),
            key,
            valid_types=_BASIC_TYPES,
        )

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
