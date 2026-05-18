class Error(Exception):
    """The base class for all exceptions that the module raises."""

    def __init__(self, error, *args, **kwargs):
        super().__init__(error.format(*args, **kwargs) if args or kwargs else error)


class FileReadingError(Error):
    """Error while reading a configuration file."""

    def __init__(self, path, error):
        super().__init__(f"Error while reading '{path}' configuration file: {error.strerror}.")
        self.errno = error.errno


class FileWritingError(Error):
    """Error while writing a configuration file."""

    def __init__(self, path, error):
        super().__init__(f"Error while writing '{path}' configuration file: {error.strerror}.")
        self.errno = error.errno


class ParsingError(Error):
    """Error while parsing a configuration file."""

    def __init__(self, path, error):
        super().__init__(f"Error while parsing '{path}' configuration file: {error}.")


class ValidationError(Error):
    """Error during validation of a configuration file."""

    def __init__(self, path, error):
        super().__init__(f"Error while validating '{path}' configuration file: {error}.")
        self.option_name = error.option_name


class _ValidationError(Error):
    """Same as ValidationError, but for internal usage."""

    def __init__(self, option_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.option_name = option_name
