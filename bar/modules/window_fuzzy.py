import operator
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.entry import Entry
from fabric.utils import idle_add
from gi.repository import Gdk


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

        self._all_windows = ["Test", "Uwu", "Tidal"]

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

    def notify_text(self, entry, *_):
        text = entry.get_text()
        self.arrange_viewport(text)  # Update list on typing
        print(text)

    def on_search_entry_key_press(self, widget, event):
        # if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right):
        #     self.move_selection_2d(event.keyval)
        #     return True
        print(event.keyval)
        if event.keyval in [Gdk.KEY_Escape, 103]:
            self.hide()
            return True
        return False

    def on_search_entry_activate(self, text):
        print(f"activate {text}")

    def arrange_viewport(self, query: str = ""):
        self.viewport.children = []  # Clear previous entries

        filtered = [w for w in self._all_windows if query.lower() in w.lower()]

        for window in filtered:
            self.viewport.add(
                Box(name="slot-box", orientation="h", children=[Label(label=window)])
            )
