"""
Fenster widgets for workspace and window management via sway IPC.
"""

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
        self._i3.send_command(f"workspace {self._workspace_num}")

    def set_focused(self, focused: bool):
        if focused:
            self.add_style_class("focused")
        else:
            self.remove_style_class("focused")

    def set_visible_on_output(self, visible: bool):
        if visible:
            self.add_style_class("visible")
        else:
            self.remove_style_class("visible")

    def set_has_windows(self, has_windows: bool):
        if has_windows:
            self.add_style_class("has-windows")
        else:
            self.remove_style_class("has-windows")


class FensterWorkspaces(Box):
    """Container widget showing all workspaces"""

    def __init__(
        self,
        output: str | None = None,
        i3: I3 | None = None,
        buttons_factory=None,
        **kwargs,
    ):
        super().__init__(
            name=kwargs.pop("name", "workspaces"),
            spacing=kwargs.pop("spacing", 4),
            orientation="h",
            **kwargs,
        )

        self._output = output
        self._i3 = i3 or get_i3_connection()
        self._buttons_factory = buttons_factory or self._default_button_factory
        self._buttons = {}

        bulk_connect(
            self._i3,
            {
                "event::workspace::focus": self._on_workspace_event,
                "event::workspace::init": self._on_workspace_event,
                "event::workspace::empty": self._on_workspace_event,
                "event::workspace::urgent": self._on_workspace_event,
                "event::window::new": self._on_window_event,
                "event::window::close": self._on_window_event,
            },
        )

        if self._i3.ready:
            self._refresh_workspaces()
        else:
            self._i3.connect("notify::ready", lambda *_: self._refresh_workspaces())

    def _default_button_factory(self, workspace_num: int) -> FensterWorkspaceButton:
        return FensterWorkspaceButton(workspace_num=workspace_num, i3=self._i3)

    def _on_workspace_event(self, _, event: I3Event):
        self._refresh_workspaces()

    def _on_window_event(self, _, event: I3Event):
        self._refresh_workspaces()

    def _refresh_workspaces(self):
        reply = I3.send_command("", I3MessageType.GET_WORKSPACES)
        if reply.is_ok and isinstance(reply.reply, list):
            self._update_workspaces(reply.reply)

    def _update_workspaces(self, workspaces: list):
        focused_ws = None
        workspace_nums = set()
        for ws in workspaces:
            ws_num = ws.get("num")
            if ws_num is not None:
                workspace_nums.add(ws_num)
                if ws.get("focused"):
                    focused_ws = ws_num

        # Remove buttons for workspaces that no longer exist
        for ws_num in list(self._buttons.keys()):
            if ws_num not in workspace_nums:
                button = self._buttons.pop(ws_num)
                self.remove(button)

        # Add/update buttons for current workspaces
        for ws in sorted(workspaces, key=lambda w: w.get("num", 0)):
            ws_num = ws.get("num")
            if ws_num is None:
                continue

            if ws_num not in self._buttons:
                button = self._buttons_factory(ws_num)
                self._buttons[ws_num] = button
                self.add(button)

            button = self._buttons[ws_num]
            button.set_focused(ws_num == focused_ws)

            ws_output = ws.get("output")
            is_visible = ws_output == self._output if self._output is not None else False
            button.set_visible_on_output(is_visible)

            window_count = ws.get("window_count", 0)
            button.set_has_windows(window_count > 0)

        # Sort buttons by workspace number
        sorted_buttons = sorted(self._buttons.values(), key=lambda b: b.workspace_num)
        for i, button in enumerate(sorted_buttons):
            self.reorder_child(button, i)

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
