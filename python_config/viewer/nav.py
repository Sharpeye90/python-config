"""Navigation model for the interactive config viewer."""

import textwrap
from typing import Tuple, Union


PathSegment = Union["VarKey", "DictKey", "ListIndex"]
ChildRow = Tuple[str, str, str, Tuple[PathSegment, ...]]


class VarKey:
    """Top-level assignment name."""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"VarKey({self.name!r})"


class DictKey:
    """Key within a dict value."""

    __slots__ = ("key",)

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return f"DictKey({self.key!r})"


class ListIndex:
    """Index within a list value."""

    __slots__ = ("index",)

    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f"ListIndex({self.index})"


def format_path(path):
    """Return a breadcrumb string for *path*."""

    if not path:
        return "(root)"

    parts = []
    for segment in path:
        if isinstance(segment, VarKey):
            parts.append(segment.name)
        elif isinstance(segment, DictKey):
            parts.append(str(segment.key))
        elif isinstance(segment, ListIndex):
            parts.append(f"[{segment.index}]")
    return " \u203a ".join(parts)


def resolve(doc, path):
    """Return ``(value, assignment)`` at *path*.

    *assignment* is set only when *path* is a single :class:`VarKey`.
    """

    if not path:
        return None, None

    first = path[0]
    if not isinstance(first, VarKey):
        raise ValueError("path must start with VarKey")

    assignment = doc.getvar(first.name)
    value = assignment.value

    for segment in path[1:]:
        if isinstance(segment, DictKey):
            value = value[segment.key]
        elif isinstance(segment, ListIndex):
            value = value[segment.index]
        else:
            raise ValueError(f"unexpected path segment: {segment!r}")

    if len(path) == 1:
        return value, assignment

    return value, None


def _type_name(value):
    if value is None:
        return "none"

    return type(value).__name__


def preview_value(value, max_len=60):
    """Short one-line preview of *value*."""

    if isinstance(value, dict):
        return f"dict({len(value)} keys)"

    if isinstance(value, list):
        return f"list[{len(value)}]"

    return truncate_text(repr(value), max_len)


def list_children(doc, path):
    """Return navigable child rows at *path*.

    Each row is ``(label, type_name, preview, child_path)`` where *child_path*
    is the full path including the new segment.
    """

    if not path:
        children = []
        for item in doc.items:
            if item.name.startswith("_") or not item.name.isupper():
                continue
            child_path = path + (VarKey(item.name),)
            children.append(
                (
                    item.name,
                    _type_name(item.value),
                    preview_value(item.value),
                    child_path,
                )
            )
        return children

    value, _assignment = resolve(doc, path)

    if isinstance(value, dict):
        return [
            (
                str(key),
                _type_name(nested),
                preview_value(nested),
                path + (DictKey(key),),
            )
            for key, nested in value.items()
        ]

    if isinstance(value, list):
        return [
            (
                f"[{index}]",
                _type_name(nested),
                preview_value(nested),
                path + (ListIndex(index),),
            )
            for index, nested in enumerate(value)
        ]

    return []


def paginate(items, page, page_size):
    """Return ``(page_items, page_index, total_pages)``."""

    total = len(items)
    if total == 0:
        return [], 0, 1

    total_pages = (total + page_size - 1) // page_size
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    end = min(start + page_size, total)
    return items[start:end], page, total_pages


def search(doc, path, query):
    """Search navigable children at *path* matching *query* (case-insensitive).

    Returns a list of ``(label, child_path)`` matches.
    """

    needle = query.lower()
    if not needle:
        return []

    matches = []
    for label, _type_name, _preview, child_path in list_children(doc, path):
        if needle in label.lower():
            matches.append((label, child_path))
    return matches


def assignment_source_text(assignment):
    """Return serialized assignment text for a top-level *assignment*."""

    from ..literals import literal_to_ast
    from ..serialize import _assignment_stmt, unparse

    stmt = _assignment_stmt(assignment.name, literal_to_ast(assignment.value))
    return unparse(stmt)


VALUE_DISPLAY_EXPANDED = {"max_items": 30, "max_depth": 8}
VALUE_DISPLAY_COMPACT = {"max_items": 10, "max_depth": 4}


def truncate_for_display(value, max_items=10, max_depth=4):
    """Return a truncated copy of *value* suitable for pretty-printing."""
    if max_depth <= 0:
        return "..."

    if isinstance(value, dict):
        items = list(value.items())
        result = {}
        for key, nested in items[:max_items]:
            result[key] = truncate_for_display(nested, max_items, max_depth - 1)
        remaining = len(items) - max_items
        if remaining > 0:
            result["..."] = f"{remaining} more keys"
        return result

    if isinstance(value, list):
        result = [
            truncate_for_display(nested, max_items, max_depth - 1) for nested in value[:max_items]
        ]
        remaining = len(value) - max_items
        if remaining > 0:
            result.append(f"... {remaining} more items")
        return result

    return value


def format_detail_value(value, max_items=5, max_line_len=120):
    """Format *value* as plain text for tests and non-Rich callers."""

    import pprint

    display = truncate_for_display(value, max_items=max_items, max_depth=4)
    return pprint.pformat(display, width=max_line_len, compact=False)


def truncate_text(text, max_len=2000):
    """Truncate long *text* for display."""

    return textwrap.shorten(text or "", width=max_len)


def metadata_lines(assignment):
    """Return metadata lines for a top-level *assignment*."""

    if assignment is None or assignment.docstring is None:
        return []

    return ["Docstring:", assignment.docstring]
