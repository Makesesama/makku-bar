import psutil
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from bar.modules.player import Player
from bar.modules.vinyl import VinylButton
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.system_tray.widgets import SystemTray
from fabric.river.widgets import (
    RiverWorkspaces,
    RiverWorkspaceButton,
    RiverActiveWindow,
    get_river_connection,
)
from fabric.utils import (
    invoke_repeater,
)
from fabric.widgets.circularprogressbar import CircularProgressBar

from bar.config import VINYL


class StatusBar(Window):
    def __init__(
        self,
        display: int,
        tray: SystemTray | None = None,
        monitor: int = 1,
        river_service=None,
    ):
        super().__init__(
            name="bar",
            layer="top",
            anchor="left top right",
            margin="0px 0px -2px 0px",
            exclusivity="auto",
            visible=False,
            all_visible=False,
            monitor=monitor,
        )
        if river_service:
            self.river = river_service
        else:
            self.river = get_river_connection()

        self.workspaces = RiverWorkspaces(
            display,
            name="workspaces",
            spacing=4,
            buttons_factory=lambda ws_id: RiverWorkspaceButton(id=ws_id, label=None),
            river_service=self.river,
        )
        self.date_time = DateTime(name="date-time", formatters="%d %b - %H:%M")
        self.system_tray = tray

        self.active_window = RiverActiveWindow(
            name="active-window",
            max_length=50,
            style="color: #ffffff; font-size: 14px; font-weight: bold;",
        )

        self.ram_progress_bar = CircularProgressBar(
            name="ram-progress-bar", pie=True, size=24
        )
        self.cpu_progress_bar = CircularProgressBar(
            name="cpu-progress-bar", pie=True, size=24
        )

        self.progress_label = Label(
            "", style="margin: 0px 6px 0px 0px; font-size: 12px"
        )
        self.progress_bars_overlay = Overlay(
            child=self.ram_progress_bar,
            overlays=[self.cpu_progress_bar, self.progress_label],
        )
        self.player = Player()
        self.vinyl = None
        if VINYL["enable"]:
            self.vinyl = VinylButton()

        self.status_container = Box(
            name="widgets-container",
            spacing=4,
            orientation="h",
            children=self.progress_bars_overlay,
        )

        end_container_children = []

        if self.vinyl:
            end_container_children.append(self.vinyl)

        if self.system_tray:
            end_container_children.append(self.system_tray)

        end_container_children.append(self.date_time)
        end_container_children.append(self.status_container)

        self.children = CenterBox(
            name="bar-inner",
            start_children=Box(
                name="start-container",
                spacing=6,
                orientation="h",
                children=[
                    Label(name="nixos-label", markup=""),
                    self.workspaces,
                ],
            ),
            center_children=Box(
                name="center-container",
                spacing=4,
                orientation="h",
                children=[self.active_window],
            ),
            end_children=Box(
                name="end-container",
                spacing=4,
                orientation="h",
                children=end_container_children,
            ),
        )

        invoke_repeater(1000, self.update_progress_bars)

        self.show_all()

    def update_progress_bars(self):
        self.ram_progress_bar.value = psutil.virtual_memory().percent / 100
        self.cpu_progress_bar.value = psutil.cpu_percent() / 100
        return True
