from dataclasses import dataclass, field
from typing import List, Optional

from .exceptions import ValidationError, _ValidationError
from .validation import _validate_value


_UNSET = object()
"""Guard object to be able to distinguish user-provided None."""


@dataclass(eq=False)
class Assignment:
    """Assignment that may be documented.

    Examples:
    VAR = 67

    VAR_WITH_DOCSTRING = 42
    '''Number of somethings to handle the job.'''
    """

    name: str
    value: object
    docstring: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, Assignment):
            return NotImplemented

        return (
            self.name == other.name
            and self.value == other.value
            and self.docstring == other.docstring
        )

    def __ne__(self, other):
        result = self.__eq__(other)

        if result is NotImplemented:
            return NotImplemented

        return not result


@dataclass(eq=False)
class ConfigDocument:
    """Full config file meaningful content is represented by this model."""

    preamble: str = ""
    """Will be inserted as header."""

    module_docstring: Optional[str] = None
    """Module-level docstring after the preamble and before assignments."""

    items: List[Assignment] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, ConfigDocument):
            return NotImplemented

        return (
            self.preamble == other.preamble
            and self.module_docstring == other.module_docstring
            and self.items == other.items
        )

    def __ne__(self, other):
        result = self.__eq__(other)

        if result is NotImplemented:
            return NotImplemented

        return not result

    @classmethod
    def from_dict(cls, obj):
        """Create ConfigDocument from dict."""

        items = [Assignment(name=key.upper(), value=value) for key, value in obj.items()]
        return cls(items=items)

    def to_dict(self):
        """Dump to dict (for all uppercase key names)."""

        result = {}

        for item in self.items:
            if not item.name.startswith("_") and item.name.isupper():
                result[item.name.lower()] = item.value

        return result

    def names(self):
        """List names."""

        return [item.name for item in self.items]

    def getvar(self, name):
        """Return the :class:`Assignment` for a top-level option."""

        for item in self.items:
            if item.name == name:
                return item

        raise KeyError(name)

    def setvar(self, name, value=_UNSET, *, docstring=_UNSET):
        """Create or update a top-level assignment."""

        if value is _UNSET and docstring is _UNSET:
            raise TypeError("setvar() requires at least one of value or docstring")

        # Find or create a corresponding Assignment.
        try:
            item = self.getvar(name)
        except KeyError:
            if value is _UNSET:
                raise TypeError("setvar() value is required when creating a new assignment")

            item = Assignment(name=name, value=None)
            self.items.append(item)

        # Update value and/or docstring when provided.
        if value is not _UNSET:
            try:
                item.value = _validate_value(name, value)
            except _ValidationError as e:
                raise ValidationError("<runtime>", e)

        if docstring is not _UNSET:
            item.docstring = docstring

    def __getitem__(self, name):
        return self.getvar(name).value

    def __setitem__(self, name, value):
        self.setvar(name, value)

    def __delitem__(self, name):
        for index, item in enumerate(self.items):
            if item.name == name:
                del self.items[index]
                return
        raise KeyError(name)

    def __contains__(self, item):
        return item in self.names()

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default
