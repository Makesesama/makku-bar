import json
import subprocess
from datetime import datetime
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.wayland import WaylandWindow as Window
from loguru import logger


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

    def update_events(self):
        """Fetch today's events from khal"""
        try:
            result = subprocess.run(
                [
                    "khal",
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

                # Filter events for today - both past and upcoming
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%m-%d")

                past_events = []
                upcoming_events = []

                for event in all_events:
                    event_date = (
                        event.get("start", "").split()[0] if event.get("start") else ""
                    )
                    event_start_time = (
                        event.get("start", "").split()[1] if event.get("start") else ""
                    )
                    event_end_time = (
                        event.get("end", "").split()[1] if event.get("end") else ""
                    )

                    # Only process events from today
                    if event_date == current_date:
                        if not event_end_time:  # All-day events
                            upcoming_events.append(event)
                        elif event_end_time > current_time:  # Haven't ended yet
                            upcoming_events.append(event)
                        elif event_end_time <= current_time:  # Already ended
                            past_events.append(event)

                # Sort past events by start time (most recent first)
                past_events.sort(key=lambda e: e.get("start", ""), reverse=True)

                # Take up to 3 most recent past events and up to 5 upcoming events
                selected_past = past_events[:3]
                selected_upcoming = upcoming_events[:5]

                # Combine: past events first, then upcoming events
                self.events = selected_past + selected_upcoming
                logger.info(f"[Calendar] Found {len(self.events)} upcoming events")
                for i, event in enumerate(self.events):
                    logger.info(
                        f"[Calendar] Event {i+1}: {event.get('title', 'No title')} at {event.get('start', 'No time')}"
                    )
                self.emit_events_changed(self.events)

        except subprocess.CalledProcessError as e:
            logger.error(f"[Calendar] Failed to fetch events: {e}")
            self.events = []
        except Exception as e:
            logger.error(f"[Calendar] Error processing events: {e}")
            self.events = []


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
            no_events_label = Label("No upcoming events today", name="no-events")
            self.events_box.add(no_events_label)
            return

        # Check current time for determining past vs upcoming
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        for i, event in enumerate(events):
            logger.info(f"[Calendar] Processing event {i+1} for display")
            title = event.get("title", "No title")
            start_time = event.get("start", "").split()[1] if event.get("start") else ""
            end_time = event.get("end", "").split()[1] if event.get("end") else ""
            location = event.get("location", "")

            # Determine if event is in the past
            is_past = end_time and end_time <= current_time

            # Format time display
            time_str = ""
            if start_time and end_time:
                time_str = f"{start_time} - {end_time}"
            elif start_time:
                time_str = start_time

            logger.info(
                f"[Calendar] Creating widget for: {title} ({time_str}) - {'Past' if is_past else 'Upcoming'}"
            )

            # Create event item with horizontal layout - time on left, content on right
            event_status = "past" if is_past else "upcoming"
            event_box = Box(
                name="event-item",
                orientation="h",  # Horizontal layout
                spacing=12,
                style_classes=[f"event-item", event_status],
            )

            # Left side: Time display (fixed width for alignment)
            time_display = time_str if time_str else "All day"
            time_label = Label(
                time_display,
                name="event-time",
                style_classes=["event-time", event_status],
                style="min-width: 100px;"  # Fixed width for consistent alignment
            )

            # Right side: Content (title and location)
            content_box = Box(
                name="event-content",
                orientation="v",
                spacing=2
            )

            # Title with status prefix
            title_prefix = "✓ " if is_past else ""
            title_label = Label(
                f"{title_prefix}{title}",
                name="event-title",
                style_classes=["event-title", event_status],
            )
            content_box.add(title_label)

            if location:
                location_label = Label(
                    f"📍 {location}",
                    name="event-location",
                    style_classes=["event-location", event_status],
                )
                content_box.add(location_label)

            # Add time and content to the main event box
            event_box.add(time_label)
            event_box.add(content_box)

            self.events_box.add(event_box)
            logger.info(f"[Calendar] Added event widget to events_box")

        # Force refresh the popup display
        self.events_box.show_all()
        logger.info(f"[Calendar] Finished updating popup")


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
