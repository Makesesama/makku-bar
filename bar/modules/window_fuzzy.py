from fabric.i3 import I3, I3MessageType
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.entry import Entry
from gi.repository import Gdk
from bar.services.fenster import get_i3_connection


class FuzzyWindowFinder(Window):
    def __init__(
        self,
        monitor: int = 0,
    ):
        super().__init__(
            name="finder",
            anchor="center",
            monitor=monitor,
            keyboard_mode="on-demand",
            type="popup",
            visible=False,
        )

        self._i3 = get_i3_connection()
        self._all_windows = []
        self._refresh_windows()

        self.viewport = Box(name="viewport", spacing=4, orientation="v")

        self.search_entry = Entry(
            name="search-entry",
            placeholder="Search Windows...",
            h_expand=True,
            editable=True,
            notify_text=self.notify_text,
            on_activate=lambda entry, *_: self.on_search_entry_activate(
                entry.get_text()
            ),
            on_key_press_event=self.on_search_entry_key_press,
        )
        self.picker_box = Box(
            name="picker-box",
            spacing=4,
            orientation="v",
            children=[self.search_entry, self.viewport],
        )

        self.add(self.picker_box)
        self.arrange_viewport("")

    def _refresh_windows(self):
        """Refresh the window list via GET_TREE"""
        self._all_windows = []
        tree_reply = I3.send_command("", I3MessageType.GET_TREE)
        if not (tree_reply.is_ok and isinstance(tree_reply.reply, dict)):
            return

        tree = tree_reply.reply
        # Traverse: root → outputs → workspaces → containers
        for output_node in tree.get("nodes", []):
            for ws_node in output_node.get("nodes", []):
                ws_num = ws_node.get("num", 0)
                for con in ws_node.get("nodes", []):
                    if con.get("type") == "con":
                        self._all_windows.append({
                            "id": con.get("id"),
                            "app_id": con.get("app_id", ""),
                            "title": con.get("name", ""),
                            "workspace": ws_num,
                        })
                for con in ws_node.get("floating_nodes", []):
                    if con.get("type") == "con":
                        self._all_windows.append({
                            "id": con.get("id"),
                            "app_id": con.get("app_id", ""),
                            "title": con.get("name", ""),
                            "workspace": ws_num,
                        })

    def show(self):
        """Override show to refresh windows before displaying"""
        self._refresh_windows()
        self.arrange_viewport(self.search_entry.get_text())
        super().show()

    def notify_text(self, entry, *_):
        text = entry.get_text()
        self.arrange_viewport(text)

    def on_search_entry_key_press(self, widget, event):
        if event.keyval in [Gdk.KEY_Escape, 103]:
            self.hide()
            return True
        return False

    def on_search_entry_activate(self, text):
        """Focus the first matching window"""
        filtered = self._filter_windows(text)
        if filtered:
            window_id = filtered[0].get("id")
            if window_id is not None:
                I3.send_command(f"[con_id={window_id}] focus")
            self.hide()

    def _filter_windows(self, query: str) -> list:
        """Filter windows based on query matching title or app_id"""
        if not query:
            return self._all_windows
        query_lower = query.lower()
        return [
            w for w in self._all_windows
            if query_lower in w.get("title", "").lower()
            or query_lower in w.get("app_id", "").lower()
        ]

    def arrange_viewport(self, query: str = ""):
        self.viewport.children = []  # Clear previous entries

        filtered = self._filter_windows(query)

        for window in filtered:
            title = window.get("title", "")
            app_id = window.get("app_id", "")
            ws_num = window.get("workspace", 0)
            display_text = f"[{ws_num}] {app_id}: {title}" if app_id else f"[{ws_num}] {title}"
            self.viewport.add(
                Box(name="slot-box", orientation="h", children=[Label(label=display_text)])
            )
