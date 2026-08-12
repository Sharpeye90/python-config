import ast

from .common import constant_value, is_constant_node


_ALLOWED_CONSTANT_TYPES = (bool, int, float, str, type(None))


class AstValidationError(Exception):
    """Error raised on AST validation step."""


def _validate_formatted_value(node):
    """Validate an f-string field.

    Only plain interpolation is allowed: no format spec (``:.2f``) and no
    conversion flag (``!r``). The expression inside the braces may reference
    option names defined earlier in the same file.
    """

    if node.format_spec is not None:
        raise AstValidationError("f-string format specs are not supported")

    # conversion: -1 means none (default str)
    if node.conversion not in (-1, ord("s"), ""):
        raise AstValidationError("f-string conversion flags are not supported")

    validate_config_expr(node.value, allow_names=True)


def validate_config_expr(node, allow_names=False):
    """Check that an AST expression is allowed in a config value.

    Recursively accepts constants, unary ``-``, binary ``+`` ``-`` ``*`` ``/``,
    containers of those expressions, and f-strings (``ast.JoinedStr``).

    :param node: AST node for the right-hand side of an assignment or a nested part of it.
    :param allow_names: If ``False`` (default), bare names (``ast.Name``) are rejected. Used for
                        top-level assignment values and dict keys, so ``OTHER + 1`` at the
                        root of ``X = ...`` is invalid.

                        If ``True``, bare names are allowed. This is enabled only inside
                        f-string braces (e.g. ``f"{VAR1}:{VAR2}"``), where ``VAR1`` must refer
                        to another option assigned earlier in the file. Names are not
                        evaluated here; :func:`python_config.literals.literal_from_ast` resolves
                        them using a per-file namespace during parsing.

    :raises AstValidationError: If the expression uses a disallowed construct.
    """

    if allow_names and isinstance(node, ast.Name):
        return

    if is_constant_node(node):
        if not isinstance(constant_value(node), _ALLOWED_CONSTANT_TYPES):
            raise AstValidationError(
                "unsupported constant type: {0}".format(type(constant_value(node)).__name__)
            )
        return

    if isinstance(node, ast.JoinedStr):
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                continue

            if isinstance(part, ast.FormattedValue):
                _validate_formatted_value(part)
                continue

            if isinstance(part, ast.Str):
                continue

            raise AstValidationError("disallowed f-string part: {0}".format(type(part).__name__))
        return

    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, ast.USub):
            raise AstValidationError("only unary minus is allowed on literals")
        if not is_constant_node(node.operand) or not isinstance(
            constant_value(node.operand), (int, float)
        ):
            raise AstValidationError("unary minus may only be applied to numeric literals")
        return

    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            raise AstValidationError("only +, -, *, / are allowed")
        validate_config_expr(node.left, allow_names=allow_names)
        validate_config_expr(node.right, allow_names=allow_names)
        return

    if isinstance(node, ast.List):
        for element in node.elts:
            validate_config_expr(element, allow_names=allow_names)
        return

    if isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values):
            if key is not None:
                validate_config_expr(key, allow_names=False)
            validate_config_expr(value, allow_names=allow_names)
        return

    raise AstValidationError("disallowed expression: {0}".format(type(node).__name__))


def validate_assignment(stmt):
    """Validate a single-target assignment and return the option name.

    The right-hand side must be a config expression without bare names at the
    top level (names may still appear inside f-string braces).
    """

    if len(stmt.targets) != 1:
        raise AstValidationError("only single-target assignments are allowed")

    target = stmt.targets[0]
    if not isinstance(target, ast.Name):
        raise AstValidationError("assignment target must be a simple name")

    validate_config_expr(stmt.value, allow_names=False)

    return target.id
