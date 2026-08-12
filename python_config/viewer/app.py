"""Interactive application loop for the config viewer."""

import click
from rich.live import Live

from . import nav, render


class ViewerApp:
    """Browse-only interactive viewer for a loaded :class:`ConfigDocument`."""

    def __init__(
        self,
        doc,
        config_path,
        page_size=20,
        no_color=False,
        input_fn=None,
        prompt_fn=None,
        console=None,
    ):
        self.doc = doc
        self.config_path = config_path
        self.page_size = page_size
        self.console = console or render._make_console(no_color=no_color)
        self.input_fn = input_fn or click.getchar
        self.prompt_fn = prompt_fn or click.prompt
        self.path = ()
        self.page = 0
        self.selected_index = 0
        self.search_mode = False
        self.search_results = []
        self.message = None
        self.show_source = False
        self.pager_mode = False
        self.pager_scroll = 0
        self.pager_lines = []
        self.pager_path = ()
        self.pager_label = ""

    def _reset_detail_state(self):
        self.show_source = False
        self.pager_mode = False
        self.pager_scroll = 0
        self.pager_lines = []
        self.pager_path = ()
        self.pager_label = ""

    def _detail_assignment(self, page_items):
        if not page_items and self.path:
            detail_path = self.path
        else:
            detail_path = self._detail_path(page_items)
        _value, assignment = nav.resolve(self.doc, detail_path)
        return assignment

    def _all_children(self):
        return nav.list_children(self.doc, self.path)

    def _current_page_items(self):
        children = self._all_children()
        return nav.paginate(children, self.page, self.page_size)

    def _selectable_indices(self, page_items):
        return render.selectable_rows(page_items)

    def _clamp_selection(self, page_items):
        selectable = self._selectable_indices(page_items)
        if not selectable:
            self.selected_index = 0
            return
        if self.selected_index not in selectable:
            self.selected_index = selectable[0]

    def _detail_label(self, page_items):
        selectable = self._selectable_indices(page_items)
        if self.selected_index not in selectable:
            return None
        label, _type_name, _preview, child_path = page_items[self.selected_index]
        if child_path:
            return label
        return None

    def _detail_path(self, page_items):
        selectable = self._selectable_indices(page_items)
        if self.selected_index not in selectable:
            return self.path
        _label, _type_name, _preview, child_path = page_items[self.selected_index]
        return child_path or self.path

    def _resolve_detail(self, page_items):
        if not page_items and self.path:
            detail_path = self.path
            last = self.path[-1]
            if hasattr(last, "name"):
                detail_label = last.name
            elif hasattr(last, "key"):
                detail_label = str(last.key)
            elif hasattr(last, "index"):
                detail_label = f"[{last.index}]"
            else:
                detail_label = nav.format_path(self.path)
        else:
            detail_path = self._detail_path(page_items)
            detail_label = self._detail_label(page_items)

        return detail_path, detail_label

    def _draw(self, page_items, page, total_pages, live=None):
        detail_path, detail_label = self._resolve_detail(page_items)

        render.render_screen(
            self.console,
            self.config_path,
            self.doc,
            detail_path,
            page_items,
            page,
            total_pages,
            self.selected_index,
            detail_label,
            search_mode=self.search_mode,
            search_results=self.search_results,
            message=self.message,
            show_source=self.show_source,
            live=live,
        )
        self.message = None

    def _draw_pager(self, live=None):
        render.render_pager_screen(
            self.console,
            self.pager_label,
            self.pager_path,
            self.pager_lines,
            self.pager_scroll,
            live=live,
        )

    def _enter_pager(self, page_items):
        detail_path, detail_label = self._resolve_detail(page_items)
        if not detail_path:
            return

        value, _assignment = nav.resolve(self.doc, detail_path)
        self.pager_path = detail_path
        self.pager_label = detail_label or nav.format_path(detail_path)
        self.pager_lines = nav.value_pager_lines(value, width=self.console.width)
        self.pager_scroll = 0
        self.pager_mode = True
        self.show_source = False

    def _exit_pager(self):
        self.pager_mode = False
        self.pager_scroll = 0
        self.pager_lines = []

    def _scroll_pager(self, delta):
        if not self.pager_lines:
            return

        viewport_height = max(1, self.console.height - 6)
        _visible, scroll, _can_up, _can_down = nav.pager_viewport(
            self.pager_lines,
            self.pager_scroll + delta,
            viewport_height,
        )
        self.pager_scroll = scroll

    def _handle_pager_key(self, key, live):
        if key in ("q", "Q"):
            return True
        if key in ("s", "S", "b", "B", "\x1b"):
            self._exit_pager()
            return False
        if key in ("j", "J", "n", "N"):
            self._scroll_pager(1)
            self._draw_pager(live=live)
            return False
        if key in ("k", "K", "p", "P"):
            self._scroll_pager(-1)
            self._draw_pager(live=live)
            return False
        return False

    def _read_key(self):
        try:
            key = self.input_fn()
        except (EOFError, KeyboardInterrupt):
            return "q"
        if not key:
            return ""
        if key == "\x03":
            return "q"
        return key

    def _open_selected(self, page_items):
        selectable = self._selectable_indices(page_items)
        if self.selected_index not in selectable:
            return

        _label, type_name, _preview, child_path = page_items[self.selected_index]
        if type_name in ("dict", "list"):
            self.path = child_path
            self.page = 0
            self.selected_index = 0
            self._reset_detail_state()

    def _go_back(self):
        if self.search_mode:
            self.search_mode = False
            self.search_results = []
            return

        if self.path:
            self.path = self.path[:-1]
            self.page = 0
            self.selected_index = 0
            self._reset_detail_state()

    def _start_search(self, live=None):
        if live is not None:
            live.stop()
        try:
            query = self.prompt_fn("Search", default="")
        finally:
            if live is not None:
                live.start(refresh=True)

        self.search_results = nav.search(self.doc, self.path, query)
        if not self.search_results:
            self.message = f"No matches for {query!r}"
            self.search_mode = False
            return

        self.search_mode = True
        self.selected_index = 0

    def _open_search_result(self):
        if not self.search_results:
            return

        if self.selected_index < 0 or self.selected_index >= len(self.search_results):
            return

        _label, child_path = self.search_results[self.selected_index]
        self.path = child_path
        self.page = 0
        self.selected_index = 0
        self.search_mode = False
        self.search_results = []
        self._reset_detail_state()

    def _move_selection(self, page_items, delta):
        selectable = self._selectable_indices(page_items)
        if not selectable:
            return

        try:
            position = selectable.index(self.selected_index)
        except ValueError:
            position = 0

        position = max(0, min(len(selectable) - 1, position + delta))
        self.selected_index = selectable[position]
        self._reset_detail_state()

    def _handle_number_key(self, page_items, number):
        index = number - 1
        selectable = self._selectable_indices(page_items)
        if index < len(selectable):
            self.selected_index = selectable[index]
            self._reset_detail_state()

    def _toggle_source(self, page_items):
        if self._detail_assignment(page_items) is None:
            self.message = "Assignment source is available only for top-level variables"
            return
        self.show_source = not self.show_source

    def _toggle_pager(self, page_items):
        if self.pager_mode:
            self._exit_pager()
            return
        self._enter_pager(page_items)

    def run(self):
        """Run the interactive loop until the user quits."""

        use_screen = self.console.is_terminal
        with Live(
            "",
            console=self.console,
            auto_refresh=False,
            screen=use_screen,
        ) as live:
            self._run_loop(live)

    def _run_loop(self, live):
        while True:
            if self.pager_mode:
                self._draw_pager(live=live)
                if self._handle_pager_key(self._read_key(), live):
                    return
                continue

            if self.search_mode:
                self._draw([], 0, 1, live=live)
                key = self._read_key()
                if key in ("q", "Q"):
                    return
                if key in ("b", "B", "\x1b"):
                    self._go_back()
                    continue
                if key in ("\r", "\n"):
                    self._open_search_result()
                    continue
                if key in ("n", "N", "j", "J"):
                    self.selected_index = min(
                        len(self.search_results) - 1,
                        self.selected_index + 1,
                    )
                    continue
                if key in ("p", "P", "k", "K"):
                    self.selected_index = max(0, self.selected_index - 1)
                    continue
                if key.isdigit():
                    number = int(key)
                    if 1 <= number <= len(self.search_results):
                        self.selected_index = number - 1
                    continue
                continue

            page_items, page, total_pages = self._current_page_items()
            self._clamp_selection(page_items)
            self._draw(page_items, page, total_pages, live=live)

            key = self._read_key()
            if key in ("q", "Q"):
                return
            if key in ("b", "B", "\x1b"):
                self._go_back()
                continue
            if key == "/":
                self._start_search(live=live)
                continue
            if key in ("s", "S"):
                self._toggle_pager(page_items)
                continue
            if key in ("a", "A"):
                self._toggle_source(page_items)
                continue
            if key in ("n", "N", "j", "J"):
                selectable = self._selectable_indices(page_items)
                if selectable and self.selected_index >= selectable[-1]:
                    if page + 1 < total_pages:
                        self.page += 1
                        self.selected_index = 0
                        self._reset_detail_state()
                    else:
                        self._move_selection(page_items, 1)
                else:
                    self._move_selection(page_items, 1)
                continue
            if key in ("p", "P", "k", "K"):
                selectable = self._selectable_indices(page_items)
                if selectable and self.selected_index <= selectable[0]:
                    if page > 0:
                        self.page -= 1
                        self.selected_index = 0
                        self._reset_detail_state()
                    else:
                        self._move_selection(page_items, -1)
                else:
                    self._move_selection(page_items, -1)
                continue
            if key in ("\r", "\n"):
                self._open_selected(page_items)
                continue
            if key.isdigit():
                number = int(key)
                if 1 <= number <= 9:
                    self._handle_number_key(page_items, number)
                continue


def run_viewer(
    doc,
    config_path,
    page_size=20,
    no_color=False,
    input_fn=None,
    prompt_fn=None,
    console=None,
):
    """Start the viewer for *doc* loaded from *config_path*."""

    app = ViewerApp(
        doc,
        config_path,
        page_size=page_size,
        no_color=no_color,
        input_fn=input_fn,
        prompt_fn=prompt_fn,
        console=console,
    )
    app.run()
