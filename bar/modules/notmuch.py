import os
import subprocess
import shutil

# Add common binary paths to PATH for user binaries
os.environ['PATH'] = '/run/current-system/sw/bin:/home/' + os.environ.get('USER', 'user') + '/.nix-profile/bin:' + os.environ.get('PATH', '')
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from loguru import logger
from bar.config import NOTMUCH


class NotmuchService:
    def __init__(self, update_interval=60000):  # 1 minute default
        self.unread_count = 0
        self.callbacks = []
        self._update_interval = update_interval
        self._timer_id = None

        # Initial load
        self.update_unread_count()
        # Start periodic updates
        self.start_monitoring()

    def connect(self, signal_name, callback):
        """Simple callback system to replace signals"""
        if signal_name == "unread-changed":
            self.callbacks.append(callback)

    def emit_unread_changed(self, count):
        """Emit unread changed to all callbacks"""
        for callback in self.callbacks:
            callback(self, count)

    def start_monitoring(self):
        """Start periodic unread count updates"""
        if self._timer_id is None:
            from fabric.utils import invoke_repeater

            self._timer_id = invoke_repeater(
                self._update_interval, self._periodic_update
            )
            logger.info(
                f"[Notmuch] Started periodic updates every {self._update_interval/1000} seconds"
            )

    def stop_monitoring(self):
        """Stop periodic unread count updates"""
        if self._timer_id is not None:
            from gi.repository import GLib

            GLib.source_remove(self._timer_id)
            self._timer_id = None
            logger.info("[Notmuch] Stopped periodic updates")

    def _periodic_update(self):
        """Periodic update callback"""
        logger.info("[Notmuch] Performing periodic unread count update")
        self.update_unread_count()
        return True  # Keep the timer running

    def get_cached_count(self):
        """Get cached unread count without triggering update"""
        return self.unread_count

    def update_unread_count(self):
        """Fetch unread email count from notmuch"""
        # Check if notmuch is enabled
        if not NOTMUCH.get("enable", True):
            logger.info("[Notmuch] Notmuch is disabled in config")
            self.unread_count = 0
            self.emit_unread_changed(self.unread_count)
            return

        # Get notmuch path from config
        notmuch_path = NOTMUCH.get("notmuch_path", "notmuch")

        # Check if notmuch is available
        if not shutil.which(notmuch_path):
            logger.warning(f"[Notmuch] notmuch not found at '{notmuch_path}'. Please install notmuch or configure the correct path.")
            self.unread_count = 0
            self.emit_unread_changed(self.unread_count)
            return

        try:
            # Get unread email count
            cmd = [notmuch_path, "count", "tag:unread"]
            logger.info(f"[Notmuch] Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"[Notmuch] Command stdout: '{result.stdout.strip()}'")
            logger.info(f"[Notmuch] Command stderr: '{result.stderr.strip()}'")

            if result.stdout.strip():
                self.unread_count = int(result.stdout.strip())
                logger.info(f"[Notmuch] Found {self.unread_count} unread emails")
                self.emit_unread_changed(self.unread_count)
            else:
                self.unread_count = 0
                self.emit_unread_changed(self.unread_count)

        except subprocess.CalledProcessError as e:
            logger.error(f"[Notmuch] Failed to fetch unread count: {e}")
            self.unread_count = 0
            self.emit_unread_changed(self.unread_count)
        except ValueError as e:
            logger.error(f"[Notmuch] Error parsing unread count: {e}")
            self.unread_count = 0
            self.emit_unread_changed(self.unread_count)
        except Exception as e:
            logger.error(f"[Notmuch] Error getting unread count: {e}")
            self.unread_count = 0
            self.emit_unread_changed(self.unread_count)


class NotmuchWidget(Button):
    def __init__(self, **kwargs):
        # Create the widget content
        self.icon = Image(icon_name="mail-unread-symbolic", icon_size=16)
        self.label = Label("0", name="unread-count")

        # Container for icon and label
        container = Box(
            orientation="h",
            spacing=4,
            children=[self.icon, self.label]
        )

        super().__init__(
            name="notmuch-widget",
            child=container,
            on_clicked=self.open_email_client,
            **kwargs,
        )

        # Initialize the service
        self.service = NotmuchService()
        self.service.connect("unread-changed", self.update_display)

        logger.info("[Notmuch] Notmuch widget initialized")

        # Initial update
        self.update_display(self.service, self.service.unread_count)

    def open_email_client(self, button=None):
        """Open notmuch in emacsclient"""
        emacsclient_command = NOTMUCH.get("emacsclient_command", "emacsclient")

        try:
            # Open emacsclient with notmuch function
            cmd = [emacsclient_command, "-c", "-e", "(notmuch)"]
            logger.info(f"[Notmuch] Running emacsclient command: {' '.join(cmd)}")
            subprocess.Popen(cmd, start_new_session=True)
            logger.info(f"[Notmuch] Successfully started emacsclient process")
        except Exception as e:
            logger.error(f"[Notmuch] Failed to open notmuch in emacsclient '{emacsclient_command}': {e}")

    def update_display(self, service, count):
        """Update the widget display with unread count"""
        # Only show count if there are unread emails
        if count > 0:
            self.label.set_text(str(count))
            self.label.set_visible(True)
            self.icon.set_from_icon_name("mail-unread-symbolic", 16)
            self.set_style_classes(["notmuch-widget", "has-unread"])
        else:
            self.label.set_text("")
            self.label.set_visible(False)
            self.icon.set_from_icon_name("mail-read-symbolic", 16)
            self.set_style_classes(["notmuch-widget", "no-unread"])

        logger.info(f"[Notmuch] Updated display: {count} unread emails")