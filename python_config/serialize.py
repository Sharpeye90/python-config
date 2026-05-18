import ast

from .common import constant_value, is_constant_node
from .literals import literal_to_ast


def _assignment_stmt(name, value_ast):
    return ast.Assign(
        targets=[ast.Name(id=name, ctx=ast.Store())],
        value=value_ast,
    )


def _format_docstring(text):
    quote = "'''" if '"""' in text else '"""'
    return "{0}{1}{0}".format(quote, text)


def _serialize_assignment_block(item):
    value_ast = literal_to_ast(item.value)
    stmt = _assignment_stmt(item.name, value_ast)

    if hasattr(ast, "fix_missing_locations"):
        ast.fix_missing_locations(stmt)

    lines = []
    lines.append(unparse(stmt))

    if item.docstring is not None:
        lines.append(_format_docstring(item.docstring))

    return "\n".join(lines)


def serialize_config(document):
    """Serialize whole configuration object into string."""

    source = "\n\n".join(_serialize_assignment_block(item) for item in document.items)

    prefix = ""

    if document.preamble:
        # Ensure exactly one newline at the end of the preamble content,
        # then add an empty line before the module docstring (if present).
        prefix = document.preamble
        if not prefix.endswith("\n"):
            prefix = prefix + "\n"

        if document.module_docstring is not None:
            prefix = prefix + "\n"

    if document.module_docstring is not None:
        # Empty line between module docstring and the first assignment.
        prefix = prefix + _format_docstring(document.module_docstring) + "\n\n"

    if prefix:
        source = prefix + source

    if not source.endswith("\n"):
        source = source + "\n"

    return source


def _format_str_literal(value):
    quote = _choose_str_quote(value)
    return "{0}{1}{0}".format(quote, _escape_quoted_string(value, quote))


def _format_constant(value):
    if isinstance(value, str):
        return _format_str_literal(value)
    return repr(value)


def _indent(level):
    return "    " * level


def _choose_str_quote(value):
    if "\n" in value or "\r" in value:
        if '"""' not in value:
            return '"""'
        if "'''" not in value:
            return "'''"
    if '"' not in value:
        return '"'
    if "'" not in value:
        return "'"
    if '"""' not in value:
        return '"""'
    return "'''"


def _escape_quoted_string(value, quote):
    delimiter = quote[0]
    escaped = (
        value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    )
    return escaped.replace(delimiter, "\\" + delimiter)


def _unparse_list(node, level):
    if not node.elts:
        return "[]"

    inner = _indent(level + 1)
    lines = ["["]
    for element in node.elts:
        lines.append(inner + _unparse_expr(element, level + 1) + ",")
    lines.append(_indent(level) + "]")
    return "\n".join(lines)


def _unparse_dict(node, level):
    if not node.keys:
        return "{}"

    inner = _indent(level + 1)
    lines = ["{"]
    for key, value in zip(node.keys, node.values):
        line = _unparse_expr(key, 0) + ": " + _unparse_expr(value, level + 1)
        lines.append(inner + line + ",")
    lines.append(_indent(level) + "}")
    return "\n".join(lines)


def _unparse_expr(node, level=0):
    """Unparse a literal expression AST node to config source text."""

    if is_constant_node(node):
        return _format_constant(constant_value(node))

    if isinstance(node, ast.List):
        return _unparse_list(node, level)

    if isinstance(node, ast.Dict):
        return _unparse_dict(node, level)

    raise TypeError("cannot unparse node: {0}".format(type(node).__name__))


def _unparse_stmt(node):
    """Unparse a single assignment statement to config source text."""

    if isinstance(node, ast.Assign):
        if len(node.targets) != 1:
            raise TypeError("only single-target assignments supported")

        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise TypeError("only simple name targets supported")

        return "{0} = {1}".format(target.id, _unparse_expr(node.value))

    raise TypeError("cannot unparse statement: {0}".format(type(node).__name__))


def unparse(node):
    """Unparse an AST node to config source (assignment statement or expression).

    Uses project formatting (double-quoted strings, multiline containers, etc.),
    not stdlib ``ast.unparse``.
    """

    if isinstance(node, ast.stmt):
        return _unparse_stmt(node)

    return _unparse_expr(node)
