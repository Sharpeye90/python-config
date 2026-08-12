import ast

from .common import constant_node, constant_value, is_constant_node


class LiteralError(Exception):
    pass


def _arithmetic_operand(value):
    if type(value) not in (int, float):
        raise LiteralError(
            "arithmetic operands must be int or float, got {0}".format(type(value).__name__)
        )
    return value


def _default_formatted_value(node, value):
    """Convert an interpolated value to text for an f-string field.

    Applies default ``str()`` conversion only; rejects format specs and
    ``!r`` / ``!s`` conversion flags on *node*.
    """

    if node.format_spec is not None:
        raise LiteralError("f-string format specs are not supported")

    if node.conversion not in (-1, ord("s"), ""):
        raise LiteralError("f-string conversion flags are not supported")

    return str(value)


def literal_from_ast(node, namespace=None):
    """Evaluate an AST literal expression to a Python value.

    .. NOTE:: Bare ``ast.Name`` nodes are only present in the tree after validation with
              ``allow_names=True`` (inside f-string braces). Top-level assignments do not pass names
              through validation.

    :param node: AST node (typically the right-hand side of an assignment).
    :param namespace: Mapping of option names (``VAR1``, ``HOST``, …) to values already
                      assigned earlier in the same config file. Used to resolve names inside
                      f-strings: ``f"{VAR1}"`` looks up ``namespace["VAR1"]``. If a name is
                      missing, raises :class:`LiteralError` (undefined forward reference).
                      Defaults to an empty dict.

    :raises LiteralError: If the node cannot be evaluated (unknown name, division by zero, etc.).

    :returns: The evaluated value (scalars, containers, folded arithmetic, evaluated f-strings).
    """

    if namespace is None:
        namespace = {}

    if isinstance(node, ast.Name):
        if node.id not in namespace:
            raise LiteralError(f"undefined name: {node.id}")
        return namespace[node.id]

    if is_constant_node(node):
        return constant_value(node)

    if isinstance(node, ast.JoinedStr):
        parts = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
            elif isinstance(part, ast.FormattedValue):
                inner = literal_from_ast(part.value, namespace)
                parts.append(_default_formatted_value(part, inner))
            elif isinstance(part, ast.Str):
                parts.append(part.s)
            else:
                raise LiteralError(f"cannot convert f-string part: {type(part).__name__}")
        return "".join(parts)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = literal_from_ast(node.operand, namespace)
        if not isinstance(value, (int, float)):
            raise LiteralError("unary minus requires a numeric operand")
        return -value

    if isinstance(node, ast.BinOp):
        left = _arithmetic_operand(literal_from_ast(node.left, namespace))
        right = _arithmetic_operand(literal_from_ast(node.right, namespace))

        if isinstance(node.op, ast.Add):
            return left + right

        if isinstance(node.op, ast.Sub):
            return left - right

        if isinstance(node.op, ast.Mult):
            return left * right

        if isinstance(node.op, ast.Div):
            try:
                return left / right
            except ZeroDivisionError:
                raise LiteralError("division by zero")

        raise LiteralError(f"unsupported binary operator: {type(node.op).__name__}")

    if isinstance(node, ast.List):
        return [literal_from_ast(element, namespace) for element in node.elts]

    if isinstance(node, ast.Dict):
        return {
            (literal_from_ast(key, namespace) if key is not None else None): literal_from_ast(
                value, namespace
            )
            for key, value in zip(node.keys, node.values)
        }

    raise LiteralError(f"cannot convert expression to value: {type(node).__name__}")


def literal_to_ast(value):
    """Build an AST literal expression from a Python value."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return constant_node(value)

    if isinstance(value, list):
        return ast.List(
            elts=[literal_to_ast(element) for element in value],
            ctx=ast.Load(),
        )

    if isinstance(value, dict):
        keys = []
        values = []
        for key, item in value.items():
            if key is None:
                keys.append(None)
            else:
                keys.append(literal_to_ast(key))
            values.append(literal_to_ast(item))
        return ast.Dict(keys=keys, values=values)

    raise LiteralError(f"unsupported value type: {type(value).__name__}")
