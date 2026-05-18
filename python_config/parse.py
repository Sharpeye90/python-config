import ast

from .ast_validate import AstValidationError, validate_assignment
from .common import docstring_value, is_docstring_expr
from .literals import LiteralError, literal_from_ast
from .models import Assignment, ConfigDocument


class ParseError(Exception):
    pass


def _preamble(source, tree):
    """Return source text before the first top-level statement in *tree*."""

    if not tree.body:
        return source

    lines = source.splitlines(keepends=True)

    return "".join(lines[: tree.body[0].lineno - 1])


def parse_config(source):
    """Parse config source into a :class:`~python_config.models.ConfigDocument`.

    Assignments are processed in source order. Each right-hand side is validated,
    then evaluated with a namespace of prior option names so f-strings can
    reference earlier options (e.g. ``f"{HOST}:{PORT}"`` after ``HOST`` and
    ``PORT`` are assigned). Arithmetic and f-string expressions are folded to
    literal values at load time; dumps always emits literals.
    """

    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise ParseError("syntax error: {0}".format(exc))

    if not isinstance(tree, ast.Module):
        raise ParseError("expected a module")

    body = tree.body
    module_docstring = None
    if body and is_docstring_expr(body[0]):
        module_docstring = docstring_value(body[0])
        body = body[1:]

    items = []
    namespace = {}
    for stmt in body:
        if isinstance(stmt, ast.Assign):
            try:
                name = validate_assignment(stmt)
            except AstValidationError as exc:
                raise ParseError(str(exc))

            try:
                value = literal_from_ast(stmt.value, namespace)
            except LiteralError as exc:
                raise ParseError(str(exc))

            namespace[name] = value
            items.append(
                Assignment(
                    name=name,
                    value=value,
                    docstring=None,
                )
            )
            continue

        if is_docstring_expr(stmt):
            if not items or items[-1].docstring is not None:
                raise ParseError("docstring must immediately follow an assignment")
            items[-1].docstring = docstring_value(stmt)
            continue

        raise ParseError("unsupported top-level statement: {0}".format(type(stmt).__name__))

    preamble = _preamble(source, tree)
    if module_docstring is not None:
        # Canonicalize preamble trailing newlines when a module docstring
        # follows. Serializer may emit an empty line separator for readability,
        # but we keep the stored preamble ending stable for round-trips.
        if preamble:
            preamble = preamble.rstrip("\n") + "\n"

    return ConfigDocument(
        preamble=preamble,
        module_docstring=module_docstring,
        items=items,
    )
