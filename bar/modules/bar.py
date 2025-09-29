import psutil
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.image import Image
from fabric.widgets.overlay import Overlay
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from bar.modules.player import Player
from bar.modules.vinyl import VinylButton
from bar.modules.battery import Battery
from bar.modules.calendar import CalendarService, CalendarPopup
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.system_tray.widgets import SystemTray
from fabric.river.widgets import (
    RiverWorkspaces,
    RiverWorkspaceButton,
    RiverActiveWindow,
    get_river_connection,
)
from fabric.widgets.circularprogressbar import CircularProgressBar
from bar.services.system_stats import SystemStatsService

from bar.config import VINYL, BATTERY, BAR_HEIGHT, WINDOW_TITLE


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
        # Create calendar components (refresh every 2 minutes)
        self.calendar_service = CalendarService(update_interval=120000)
        self.calendar_popup = CalendarPopup()
        self.calendar_popup_visible = False

        # Create clickable datetime widget
        from fabric.widgets.button import Button
        datetime_widget = DateTime(name="date-time", formatters="%d %b - %H:%M")
        self.date_time = Button(
            name="date-time-button",
            child=datetime_widget,
            on_clicked=self.toggle_calendar,
            style="background: transparent; border: none; padding: 0; margin: 0; box-shadow: none;"
        )

        # Connect calendar service to popup
        self.calendar_service.connect("events-changed", self.update_calendar_display)
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

        self.battery = None
        if BATTERY["enable"]:
            self.battery = Battery()

        self.status_container = Box(
            name="widgets-container",
            spacing=4,
            orientation="h",
            children=self.progress_bars_overlay,
        )

        end_container_children = []

        if self.vinyl:
            end_container_children.append(self.vinyl)

        end_container_children.append(self.status_container)
        if self.system_tray:
            end_container_children.append(self.system_tray)

        if self.battery:
            end_container_children.append(self.battery)

        end_container_children.append(self.date_time)

        center_children = []
        if WINDOW_TITLE["enable"]:
            center_children.append(self.active_window)

        self.children = CenterBox(
            name="bar-inner",
            start_children=Box(
                name="start-container",
                spacing=6,
                orientation="h",
                children=[
                    Image(name="nixos-label", icon_name="nix-snowflake-white", icon_size=20),
                    self.workspaces,
                ],
            ),
            center_children=Box(
                name="center-container",
                spacing=4,
                orientation="h",
                children=center_children,
            ),
            end_children=Box(
                name="end-container",
                spacing=4,
                orientation="h",
                children=end_container_children,
            ),
        )

        # Create system stats service with signal-based updates
        self.system_stats_service = SystemStatsService(update_interval=3000)
        self.system_stats_service.connect("stats-changed", self.update_progress_bars)

        # Set the bar height
        self.set_size_request(-1, BAR_HEIGHT)

        self.show_all()

    def __del__(self):
        """Cleanup when bar is destroyed"""
        if hasattr(self, 'calendar_service'):
            self.calendar_service.stop_monitoring()

    def update_progress_bars(self, service, cpu_percent, memory_percent):
        """Update progress bars when system stats change"""
        self.cpu_progress_bar.value = cpu_percent
        self.ram_progress_bar.value = memory_percent

    def toggle_calendar(self, button=None):
        """Toggle the calendar popup when datetime is clicked"""
        from loguru import logger
        logger.info(f"[Calendar] DateTime clicked, popup_visible: {self.calendar_popup_visible}")

        if self.calendar_popup_visible:
            logger.info("[Calendar] Hiding calendar popup")
            self.calendar_popup.set_visible(False)
            self.calendar_popup_visible = False
        else:
            logger.info("[Calendar] Showing calendar popup")
            # Use cached events - no need to refresh on click
            cached_events = self.calendar_service.get_cached_events()
            logger.info(f"[Calendar] Using {len(cached_events)} cached events")
            self.calendar_popup.update_events_display(cached_events)
            self.calendar_popup.set_visible(True)
            self.calendar_popup.show_all()
            self.calendar_popup_visible = True

    def update_calendar_display(self, service, events):
        """Update the calendar popup with events"""
        self.calendar_popup.update_events_display(events)
