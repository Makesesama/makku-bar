from fabric.core.service import Property
from fabric.widgets.button import Button
from fabric.widgets.box import Box
from fabric.widgets.eventbox import EventBox
from fabric.utils.helpers import bulk_connect
from .service import River


from gi.repository import Gdk

_connection: River | None = None


def get_river_connection() -> River:
    global _connection
    if not _connection:
        _connection = River()
    return _connection


class RiverWorkspaceButton(Button):
    @Property(int, "readable")
    def id(self) -> int:
        return self._id

    @Property(bool, "read-write", default_value=False)
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        (self.remove_style_class if not value else self.add_style_class)("active")

    @Property(bool, "read-write", default_value=False)
    def empty(self) -> bool:
        return self._empty

    @empty.setter
    def empty(self, value: bool):
        self._empty = value
        (self.remove_style_class if not value else self.add_style_class)("empty")

    def __init__(self, id: int, label: str = None, **kwargs):
        super().__init__(label or str(id), **kwargs)
        self._id = id
        self._active = False
        self._empty = True


class RiverWorkspaces(EventBox):
    def __init__(self, output_id: int, max_tags: int = 9, **kwargs):
        super().__init__(events="scroll")
        self.output_id = output_id
        self.max_tags = max_tags
        self.service = get_river_connection()
        self._box = Box(**kwargs)
        self.children = self._box

        self._buttons = {i: RiverWorkspaceButton(i) for i in range(max_tags)}
        for btn in self._buttons.values():
            btn.connect("clicked", self.on_workspace_click)
            self._box.add(btn)

        # hook into River signals
        self.service.connect(f"event::focused_tags::{output_id}", self.on_focus_change)
        self.service.connect(f"event::view_tags::{output_id}", self.on_view_change)
        if self.service.ready:
            self.on_ready(None)
        else:
            self.service.connect("event::ready", self.on_ready)

        self.connect("scroll-event", self.on_scroll)

    def on_ready(self, _):
        print(self.service.outputs)

    def on_focus_change(self, _, tags: list[int]):
        print(tags)
        for i, btn in self._buttons.items():
            btn.active = i in tags

    def on_view_change(self, _, tags: list[int]):
        print(tags)
        for i, btn in self._buttons.items():
            btn.empty = i not in tags

    def on_workspace_click(self, btn: RiverWorkspaceButton):
        import subprocess

        subprocess.run(["riverctl", "tag", str(btn.id)])
        return

    def on_scroll(self, _, event: Gdk.EventScroll):
        direction = event.direction  # UP or DOWN
        cmd = "tag +1" if direction == Gdk.ScrollDirection.DOWN else "tag -1"
        import subprocess

        subprocess.run(["riverctl", *cmd.split()])
