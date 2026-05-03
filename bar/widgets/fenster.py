"""
Fenster widgets for workspace and window management via sway IPC.
"""

from gi.repository import GLib

from fabric.i3 import I3, I3Event, I3MessageType
from fabric.utils.helpers import bulk_connect
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from bar.services.fenster import get_i3_connection


class FensterWorkspaceButton(Button):
    """Button representing a single workspace"""

    def __init__(
        self,
        workspace_num: int,
        i3: I3 | None = None,
        label: str | None = None,
        **kwargs,
    ):
        self._workspace_num = workspace_num
        self._i3 = i3 or get_i3_connection()

        display_label = label if label is not None else str(workspace_num)

        super().__init__(
            name=f"workspace-button-{workspace_num}",
            child=Label(label=display_label),
            on_clicked=self._on_clicked,
            **kwargs,
        )

        self.add_style_class("workspace-button")

    @property
    def workspace_num(self) -> int:
        return self._workspace_num

    def _on_clicked(self, *args):
        self._i3.send_command(f"workspace number {self._workspace_num}")

    def _toggle_class(self, name: str, on: bool):
        if on:
            self.add_style_class(name)
        else:
            self.remove_style_class(name)

    def set_active(self, active: bool):
        self._toggle_class("active", active)

    def set_visible_other(self, visible: bool):
        self._toggle_class("visible", visible)

    def set_empty(self, empty: bool):
        self._toggle_class("empty", empty)

    def set_urgent(self, urgent: bool):
        self._toggle_class("urgent", urgent)


class FensterWorkspaces(Box):
    """Container widget showing a fixed set of workspace bubbles (1..N)."""

    def __init__(
        self,
        output: str | None = None,
        i3: I3 | None = None,
        buttons_factory=None,
        workspace_count: int = 9,
        **kwargs,
    ):
        super().__init__(
            name=kwargs.pop("name", "workspaces"),
            spacing=kwargs.pop("spacing", 4),
            orientation="h",
            **kwargs,
        )

        self._output = output
        self._workspace_count = workspace_count
        self._i3 = i3 or get_i3_connection()
        self._buttons_factory = buttons_factory or self._default_button_factory
        self._buttons: dict[int, FensterWorkspaceButton] = {}
        self._refresh_pending = False

        # Pre-create one button per workspace slot so position N always means workspace N.
        for n in range(1, workspace_count + 1):
            button = self._buttons_factory(n)
            self._buttons[n] = button
            self.add(button)

        bulk_connect(
            self._i3,
            {
                "event::workspace::focus": self._on_event,
                "event::workspace::init": self._on_event,
                "event::workspace::empty": self._on_event,
                "event::workspace::urgent": self._on_event,
                "event::workspace::move": self._on_event,
                "event::window::focus": self._on_event,
                "event::window::new": self._on_event,
                "event::window::close": self._on_event,
            },
        )

        if self._i3.ready:
            self._schedule_refresh()
        else:
            self._i3.connect("notify::ready", lambda *_: self._schedule_refresh())

    def _default_button_factory(self, workspace_num: int) -> FensterWorkspaceButton:
        return FensterWorkspaceButton(workspace_num=workspace_num, i3=self._i3)

    def _on_event(self, _, event: I3Event):
        self._schedule_refresh()

    def _schedule_refresh(self):
        # Defer to the next idle tick — fenster's internal state is not always
        # updated synchronously when an event fires, so querying GET_WORKSPACES
        # immediately can return the pre-event view.
        if self._refresh_pending:
            return
        self._refresh_pending = True
        GLib.idle_add(self._refresh_idle)

    def _refresh_idle(self):
        self._refresh_pending = False
        self._refresh_workspaces()
        return False

    def _refresh_workspaces(self):
        reply = I3.send_command("", I3MessageType.GET_WORKSPACES)
        if reply.is_ok and isinstance(reply.reply, list):
            self._update_workspaces(reply.reply)

    def _update_workspaces(self, workspaces: list):
        ws_by_num = {
            ws["num"]: ws for ws in workspaces if ws.get("num") is not None
        }

        for n, button in self._buttons.items():
            ws = ws_by_num.get(n)
            if ws is None:
                button.set_active(False)
                button.set_visible_other(False)
                button.set_urgent(False)
                button.set_empty(True)
                continue

            focused = bool(ws.get("focused"))
            visible = bool(ws.get("visible"))
            urgent = bool(ws.get("urgent"))
            window_count = ws.get("window_count", 0)

            button.set_active(focused)
            # Visible on its output but not the focused one → shown on another monitor.
            button.set_visible_other(visible and not focused)
            button.set_urgent(urgent)
            button.set_empty(window_count == 0)

        self.show_all()


class FensterActiveWindow(Label):
    """Label showing the title of the focused window"""

    def __init__(
        self,
        i3: I3 | None = None,
        max_length: int = 50,
        **kwargs,
    ):
        super().__init__(
            name=kwargs.pop("name", "active-window"),
            label="",
            **kwargs,
        )

        self._i3 = i3 or get_i3_connection()
        self._max_length = max_length

        bulk_connect(
            self._i3,
            {
                "event::window::focus": self._on_window_event,
                "event::window::title": self._on_window_event,
                "event::window::close": self._on_window_close,
            },
        )

        if self._i3.ready:
            self._initialize()
        else:
            self._i3.connect("notify::ready", lambda *_: self._initialize())

    def _initialize(self):
        tree_reply = I3.send_command("", I3MessageType.GET_TREE)
        if tree_reply.is_ok and isinstance(tree_reply.reply, dict):
            focused = self._find_focused(tree_reply.reply)
            if focused:
                self._set_title(focused.get("name", ""))
                return
        self.set_label("")

    def _find_focused(self, node: dict) -> dict | None:
        if node.get("focused") and node.get("type") == "con":
            return node
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            result = self._find_focused(child)
            if result:
                return result
        return None

    def _on_window_event(self, _, event: I3Event):
        container = event.data.get("container", {})
        self._set_title(container.get("name", ""))

    def _on_window_close(self, _, event: I3Event):
        self._initialize()

    def _set_title(self, title: str):
        if len(title) > self._max_length:
            title = title[: self._max_length - 3] + "..."
        self.set_label(title)
