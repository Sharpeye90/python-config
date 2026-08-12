import ast
import sys


AST_CONSTANT = sys.version_info >= (3, 8)
"""Starting from python 3.8 ast.Constant is used for all constants."""


def constant_value(node):
    """Return the Python value of a constant AST node."""

    if AST_CONSTANT and isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Num):
        return node.n

    if isinstance(node, ast.Str):
        return node.s

    if isinstance(node, ast.Bytes):
        return node.s

    if isinstance(node, ast.NameConstant):
        return node.value

    raise TypeError("Not a constant node: {0}".format(type(node).__name__))


def is_constant_node(node):
    if AST_CONSTANT and isinstance(node, ast.Constant):
        return True

    return isinstance(node, (ast.Num, ast.Str, ast.Bytes, ast.NameConstant))


def is_docstring_expr(stmt):
    if not isinstance(stmt, ast.Expr):
        return False

    value = stmt.value
    if AST_CONSTANT and isinstance(value, ast.Constant):
        return isinstance(value.value, str)

    return isinstance(value, ast.Str)


def docstring_value(stmt):
    value = stmt.value
    if AST_CONSTANT and isinstance(value, ast.Constant):
        return value.value
    return value.s


def constant_node(value):
    """Build an AST literal node for a scalar constant."""

    if AST_CONSTANT:
        return ast.Constant(value=value)

    if value in (None, True, False):
        return ast.NameConstant(value=value)

    if isinstance(value, (int, float)):
        return ast.Num(n=value)

    if isinstance(value, str):
        return ast.Str(s=value)

    raise TypeError("unsupported constant type: {0}".format(type(value).__name__))
