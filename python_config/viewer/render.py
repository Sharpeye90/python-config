"""Rich rendering helpers for the interactive config viewer."""

from rich.console import Console, Group
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from . import nav


def _make_console(no_color=False):
    return Console(force_terminal=not no_color, no_color=no_color, highlight=False)


def render_children_table(
    page_items,
    page,
    total_pages,
    selected_index,
    search_mode=False,
    search_results=None,
):
    """Build a Rich table for the current page of children."""

    if search_mode and search_results is not None:
        table = Table(title=f"Search results ({len(search_results)})", expand=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Match", style="bold")
        for index, (label, _child_path) in enumerate(search_results):
            marker = " \u25ba" if index == selected_index else ""
            table.add_row(str(index + 1), label + marker)
        return table

    table = Table(
        title=f"Children (page {page + 1}/{total_pages})",
        expand=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Type", style="cyan", width=8)
    table.add_column("Preview")

    for row_index, (label, type_name, preview, _child_path) in enumerate(page_items):
        marker = " \u25ba" if row_index == selected_index else ""
        quick = ""
        if row_index < 9:
            quick = f" [{row_index + 1}]"
        table.add_row(
            str(row_index + 1) + quick,
            label + marker,
            type_name,
            preview,
        )

    return table


def render_detail_panel(doc, path, label, show_source=False):
    """Build a Rich panel showing detail for the node at *path*."""

    value, assignment = nav.resolve(doc, path)
    lines = []

    if label:
        lines.append(Text(f"Node: {label}", style="bold"))

    lines.append(Text(f"Path: {nav.format_path(path)}", style="dim"))
    lines.append("")

    if show_source and assignment is not None:
        lines.append(Text(nav.preview_value(value), style="dim"))
        lines.append("")
        lines.append(Text("Source:", style="bold"))
        lines.append(nav.truncate_text(nav.assignment_source_text(assignment)))
        lines.append("")
        lines.append(Text("Press a to return to value", style="dim italic"))
    else:
        lines.append(Text("Value:", style="bold"))
        lines.append(
            Pretty(
                nav.truncate_for_display(value, **nav.VALUE_DISPLAY_EXPANDED),
                expand_all=True,
                indent_guides=True,
                max_string=300,
            )
        )
        lines.append("")
        lines.append(Text("Press s to expand value", style="dim italic"))
        if assignment is not None:
            lines.append(Text("Press a to view assignment source", style="dim italic"))

    metadata = nav.metadata_lines(assignment)
    if metadata:
        lines.append("")
        lines.append(Text("Metadata:", style="bold"))
        lines.extend(metadata)

    return Panel(Group(*lines), title="Detail", border_style="blue")


def render_help_bar(show_source_available=False):
    """Return help text for key bindings."""

    help_text = "[/] search  [n]ext  [p]prev  [Enter] open  [b] back  [s] expand"
    if show_source_available:
        help_text += "  [a] source"
    help_text += "  [q] quit"
    return Text(help_text, style="dim")


def build_pager_screen(label, path, lines, scroll, console_height):
    """Build a full-screen scrollable view of a value."""

    header = Panel(
        Text(f"{label} — {nav.format_path(path)}", style="bold"),
        border_style="green",
    )

    viewport_height = max(1, console_height - 6)
    visible, scroll, can_up, can_down = nav.pager_viewport(lines, scroll, viewport_height)
    body = Panel(
        Group(*[Text(line) for line in visible]),
        title="Value",
        border_style="blue",
    )

    hints = []
    if can_up:
        hints.append("[k/p] up")
    if can_down:
        hints.append("[j/n] down")
    hints.extend(["[s/b] close", "[q] quit"])

    footer = f"{'  '.join(hints)}  lines {scroll + 1}-{scroll + len(visible)}/{len(lines)}"
    return Group(header, body, Text(footer, style="dim"))


def render_pager_screen(console, label, path, lines, scroll, live=None):
    """Render or update the pager screen."""

    screen = build_pager_screen(
        label,
        path,
        lines,
        scroll,
        console.height,
    )

    if live is not None:
        live.update(screen, refresh=True)
        return

    console.print(screen)


def build_screen(
    config_path,
    doc,
    path,
    page_items,
    page,
    total_pages,
    selected_index,
    detail_label,
    search_mode=False,
    search_results=None,
    message=None,
    show_source=False,
):
    """Build the full viewer screen as a single renderable."""

    parts = [
        Panel(Text(f"python-config-view: {config_path}", style="bold"), border_style="green"),
        Text(f"Path: {nav.format_path(path)}", style="cyan"),
    ]

    if message:
        parts.append(Text(message, style="yellow"))

    parts.append(
        render_children_table(
            page_items,
            page,
            total_pages,
            selected_index,
            search_mode,
            search_results,
        )
    )

    show_source_available = False
    if detail_label and not search_mode:
        _value, assignment = nav.resolve(doc, path)
        parts.append(render_detail_panel(doc, path, detail_label, show_source=show_source))
        show_source_available = assignment is not None

    parts.append(Text(""))
    parts.append(render_help_bar(show_source_available=show_source_available))

    return Group(*parts)


def render_screen(
    console,
    config_path,
    doc,
    path,
    page_items,
    page,
    total_pages,
    selected_index,
    detail_label,
    search_mode=False,
    search_results=None,
    message=None,
    show_source=False,
    live=None,
):
    """Render or update the full viewer screen."""

    screen = build_screen(
        config_path,
        doc,
        path,
        page_items,
        page,
        total_pages,
        selected_index,
        detail_label,
        search_mode=search_mode,
        search_results=search_results,
        message=message,
        show_source=show_source,
    )

    if live is not None:
        live.update(screen, refresh=True)
        return

    console.print(screen)


def selectable_rows(page_items):
    """Return indices of selectable rows on the current page."""

    return list(range(len(page_items)))
