from __future__ import unicode_literals


class Error(Exception):
    """The base class for all exceptions that the module raises."""

    def __init__(self, error, *args, **kwargs):
        super(Error, self).__init__(error.format(*args, **kwargs) if args or kwargs else error)


class FileReadingError(Error):
    """Error while reading a configuration file."""

    def __init__(self, path, error):
        super(FileReadingError, self).__init__(
            "Error while reading '{0}' configuration file: {1}.", path, error.strerror)
        self.errno = error.errno


class ParsingError(Error):
    """Error while parsing a configuration file."""

    def __init__(self, path, error):
        super(ParsingError, self).__init__(
            "Error while parsing '{0}' configuration file: {1}.", path, error)


class ValidationError(Error):
    """Error during validation of a configuration file."""

    def __init__(self, path, error):
        super(ValidationError, self).__init__(
            "Error while parsing '{0}' configuration file: {1}.", path, error)
        self.option_name = error.option_name


class _ValidationError(Error):
    """Same as ValidationError, but for internal usage."""

    def __init__(self, option_name, *args, **kwargs):
        super(_ValidationError, self).__init__(*args, **kwargs)
        self.option_name = option_name
