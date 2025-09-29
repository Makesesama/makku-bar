import json
import subprocess
import shutil
from datetime import datetime, date
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.wayland import WaylandWindow as Window
from loguru import logger
from bar.config import CALENDAR

# Try to import khal as a Python library
try:
    from khal.cli.main import main_khal
    from khal.settings import get_config
    from khal.khalendar import CalendarCollection
    KHAL_AVAILABLE = True
    logger.info("[Calendar] Using khal as Python library")
except ImportError:
    KHAL_AVAILABLE = False
    logger.info("[Calendar] khal Python library not available, falling back to subprocess")


class CalendarService:
    def __init__(self, update_interval=300000):  # 5 minutes default
        self.events = []
        self.callbacks = []
        self._update_interval = update_interval
        self._timer_id = None

        # Initial load
        self.update_events()
        # Start periodic updates
        self.start_monitoring()

    def connect(self, signal_name, callback):
        """Simple callback system to replace signals"""
        if signal_name == "events-changed":
            self.callbacks.append(callback)

    def emit_events_changed(self, events):
        """Emit events changed to all callbacks"""
        for callback in self.callbacks:
            callback(self, events)

    def start_monitoring(self):
        """Start periodic event updates"""
        if self._timer_id is None:
            from fabric.utils import invoke_repeater

            self._timer_id = invoke_repeater(
                self._update_interval, self._periodic_update
            )
            logger.info(
                f"[Calendar] Started periodic updates every {self._update_interval/1000/60:.1f} minutes"
            )

    def stop_monitoring(self):
        """Stop periodic event updates"""
        if self._timer_id is not None:
            from gi.repository import GLib

            GLib.source_remove(self._timer_id)
            self._timer_id = None
            logger.info("[Calendar] Stopped periodic updates")

    def _periodic_update(self):
        """Periodic update callback"""
        logger.info("[Calendar] Performing periodic events update")
        self.update_events()
        return True  # Keep the timer running

    def get_cached_events(self):
        """Get cached events without triggering update"""
        return self.events

    def update_events_python_api(self):
        """Fetch today's events using khal Python API"""
        try:
            # Get khal configuration
            config = get_config()

            # Create calendar collection
            collection = CalendarCollection.from_calendars(
                calendars=config['calendars'],
                dbpath=config['sqlite']['path'],
                locale=config['locale'],
                color=config['default']['print_new'],
                unicode_symbols=config['default']['unicode_symbols'],
                default_calendar=config['default']['default_calendar'],
                readonly=True
            )

            # Get today's events
            today = date.today()
            events = collection.get_events_on(today)

            # Format events to match our expected structure
            formatted_events = []
            for event in events:
                formatted_event = {
                    'title': str(event.summary),
                    'start': event.start.strftime('%m-%d %H:%M') if hasattr(event.start, 'strftime') else '',
                    'end': event.end.strftime('%m-%d %H:%M') if hasattr(event.end, 'strftime') else '',
                    'location': str(event.location) if event.location else ''
                }
                formatted_events.append(formatted_event)

            # Sort by start time
            formatted_events.sort(key=lambda e: e.get('start', ''))

            self.events = formatted_events
            logger.info(f"[Calendar] Found {len(self.events)} events using Python API")
            self.emit_events_changed(self.events)

        except Exception as e:
            logger.error(f"[Calendar] Error using khal Python API: {e}")
            # Fall back to subprocess method
            self.update_events_subprocess()

    def update_events_subprocess(self):
        """Fetch today's events using khal subprocess (fallback)"""
        # Get khal path from config
        khal_path = CALENDAR.get("khal_path", "khal")

        # Check if khal is available
        if not shutil.which(khal_path):
            logger.warning(f"[Calendar] khal not found at '{khal_path}'. Please install khal or configure the correct path.")
            self.events = []
            self.emit_events_changed(self.events)
            return

        try:
            result = subprocess.run(
                [
                    khal_path,
                    "list",
                    "--json",
                    "title",
                    "--json",
                    "start",
                    "--json",
                    "end",
                    "--json",
                    "location",
                    "today",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                all_events = []

                for line in lines:
                    if line.strip():
                        try:
                            events = json.loads(line)
                            all_events.extend(events)
                        except json.JSONDecodeError:
                            continue

                self.events = all_events
                logger.info(f"[Calendar] Found {len(self.events)} events using subprocess")
                self.emit_events_changed(self.events)
            else:
                self.events = []
                self.emit_events_changed(self.events)

        except subprocess.CalledProcessError as e:
            logger.error(f"[Calendar] Failed to fetch events: {e}")
            self.events = []
            self.emit_events_changed(self.events)
        except Exception as e:
            logger.error(f"[Calendar] Error processing events: {e}")
            self.events = []
            self.emit_events_changed(self.events)

    def update_events(self):
        """Fetch today's events from khal"""
        # Check if calendar is enabled
        if not CALENDAR.get("enable", True):
            logger.info("[Calendar] Calendar is disabled in config")
            self.events = []
            self.emit_events_changed(self.events)
            return

        # Try Python API first, fall back to subprocess
        if KHAL_AVAILABLE:
            logger.info("[Calendar] Using khal Python API")
            self.update_events_python_api()
        else:
            logger.info("[Calendar] Using khal subprocess")
            self.update_events_subprocess()


class CalendarPopup(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="calendar-popup",
            layer="top",
            anchor="top right",
            margin="10px 10px 0px 0px",  # Just a few pixels under the bar
            exclusivity="none",
            visible=False,
            all_visible=False,
            **kwargs,
        )


        # Events container
        self.events_box = Box(
            name="events-box",
            orientation="v",
            spacing=6,
            style="min-width: 450px; min-height: 200px;",
        )

        # Add a test label to make sure popup is working
        test_label = Label("Calendar Events", name="calendar-title")

        container = Box(
            orientation="v", spacing=4, children=[test_label, self.events_box]
        )

        self.children = container

        # Set explicit size - much bigger
        self.set_size_request(500, 400)

    def update_events_display(self, events):
        """Update the events display"""
        logger.info(f"[Calendar] Updating popup with {len(events)} events")

        # Clear existing children first
        self.events_box.children = []

        if not events:
            logger.info("[Calendar] No events, showing 'no events' message")
            no_events_label = Label("No events today", name="no-events")
            self.events_box.add(no_events_label)
            return

        # Check current time for time indicator placement
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_time_added = False

        for i, event in enumerate(events):
            logger.info(f"[Calendar] Processing event {i+1} for display")
            title = event.get("title", "No title")
            start_time = event.get("start", "").split()[1] if event.get("start") else ""
            end_time = event.get("end", "").split()[1] if event.get("end") else ""
            location = event.get("location", "")

            # Check if we should add current time indicator before this event
            if not current_time_added and start_time and start_time > current_time:
                self.add_current_time_indicator(current_time)
                current_time_added = True

            # Format time display
            time_str = ""
            if start_time and end_time:
                time_str = f"{start_time} - {end_time}"
            elif start_time:
                time_str = start_time

            logger.info(f"[Calendar] Creating widget for: {title} ({time_str})")

            # Create event item with horizontal layout - time on left, content on right
            event_box = Box(
                name="event-item",
                orientation="h",  # Horizontal layout
                spacing=12,
                style_classes=["event-item"],
            )

            # Left side: Time display (fixed width for alignment)
            time_display = time_str if time_str else "All day"
            time_label = Label(
                time_display,
                name="event-time",
                style_classes=["event-time"],
                style="min-width: 100px;"  # Fixed width for consistent alignment
            )

            # Right side: Content (title and location)
            content_box = Box(
                name="event-content",
                orientation="v",
                spacing=2
            )

            # Title (no more status prefix)
            title_label = Label(
                title,
                name="event-title",
                style_classes=["event-title"],
            )
            content_box.add(title_label)

            if location:
                location_label = Label(
                    f"📍 {location}",
                    name="event-location",
                    style_classes=["event-location"],
                )
                content_box.add(location_label)

            # Add time and content to the main event box
            event_box.add(time_label)
            event_box.add(content_box)

            self.events_box.add(event_box)
            logger.info(f"[Calendar] Added event widget to events_box")

        # Add current time indicator at the end if not added yet
        if not current_time_added:
            self.add_current_time_indicator(current_time)

        # Force refresh the popup display
        self.events_box.show_all()
        logger.info(f"[Calendar] Finished updating popup")

    def add_current_time_indicator(self, current_time):
        """Add a current time indicator to the events list"""
        time_indicator = Box(
            name="current-time-indicator",
            orientation="h",
            spacing=8,
            style_classes=["current-time-indicator"],
        )

        # Current time label
        time_label = Label(
            current_time,
            name="current-time-label",
            style_classes=["current-time-label"],
            style="min-width: 100px; font-weight: bold;"
        )

        # Line indicator
        line_label = Label(
            "━━━ NOW",
            name="current-time-line",
            style_classes=["current-time-line"],
        )

        time_indicator.add(time_label)
        time_indicator.add(line_label)

        self.events_box.add(time_indicator)
        logger.info(f"[Calendar] Added current time indicator at {current_time}")


class CalendarWidget(Button):
    def __init__(self, **kwargs):
        super().__init__(
            name="calendar-widget",
            child=Image(icon_name="x-office-calendar-symbolic", icon_size=16),
            on_clicked=self.toggle_events,
            **kwargs,
        )

        self.service = CalendarService()
        self.service.connect("events-changed", self.update_events_display)

        # Create popup window
        self.popup = CalendarPopup()
        self.popup_visible = False
        logger.info("[Calendar] Calendar widget initialized with popup")

        # Initial update
        self.update_events_display(self.service, self.service.events)

    def toggle_events(self, button=None):
        """Toggle the visibility of the events popup"""
        logger.info(f"[Calendar] Button clicked, popup_visible: {self.popup_visible}")

        if self.popup_visible:
            logger.info("[Calendar] Hiding popup")
            self.popup.set_visible(False)
            self.popup_visible = False
        else:
            logger.info("[Calendar] Showing popup")
            # Refresh events when opening
            self.service.update_events()
            self.popup.set_visible(True)
            self.popup.show_all()
            self.popup_visible = True

    def update_events_display(self, service, events):
        """Update the events display in popup"""
        self.popup.update_events_display(events)
