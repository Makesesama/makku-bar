from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.image import Image
from fabric.widgets.button import Button
from fabric.widgets.revealer import Revealer
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.utils import get_relative_path
from bar.services.notifications import NotificationService, Notification
from loguru import logger
from typing import Optional


class NotificationWidget(Box):
    """A single notification widget like in fabric example"""

    def __init__(self, notification: Notification, **kwargs):
        super().__init__(
            name="notification",
            orientation="v",
            spacing=8,
            **kwargs
        )

        self._notification = notification

        # Create header with app icon and summary
        header_container = Box(spacing=8, orientation="h")

        # App icon
        app_icon = Image(
            name="notification-icon",
            icon_size=20,
            icon_name="dialog-information-symbolic"
        )

        # Summary label using fabric pattern
        summary_label = Label(
            label=notification.summary,
            name="notification-summary"
        ).build().add_style_class("summary").unwrap()

        header_container.children = [app_icon, summary_label]

        # Body if exists
        if notification.body:
            body_label = Label(
                label=notification.body,
                name="notification-body"
            ).build().add_style_class("body").unwrap()

            self.children = [header_container, body_label]
        else:
            self.children = [header_container]


class NotificationBubble(Window):
    """A notification bubble that appears as a popup window"""

    def __init__(self):
        super().__init__(
            name="notification-bubble-window",
            layer="top",  # Same layer as bar
            anchor="top center",  # Center of screen at top
            margin="0px 0px 0px 0px",  # No margin - position right at bar edge
            exclusivity="ignore",  # Don't affect other windows
            visible=True,  # Always visible
            all_visible=True,
        )

        # Create viewport container like fabric example
        self.viewport = Box(
            name="notification-viewport",
            size=2,  # so it's not ignored by the compositor
            spacing=4,
            orientation="v"
        )

        self.children = self.viewport

        # Start with no size (invisible when no notification)
        self.set_size_request(0, 42)  # Zero width but bar height
        self._is_expanded = False

        # Start with viewport collapsed
        self.viewport.set_visible(True)  # Always visible for animations
        self.viewport.add_style_class("collapsed")

        self.current_notification: Optional[Notification] = None
        self.dismiss_callback = None
        self.auto_dismiss_timeout = None

    def show_notification(self, notification: Notification):
        """Display a notification in the bubble"""
        self.current_notification = notification
        logger.info(
            f"[NotificationBubble] Attempting to show notification: {notification.summary}"
        )

        # Clear existing notifications from viewport
        for child in self.viewport.children[:]:
            self.viewport.remove(child)

        # Create new NotificationWidget and add to viewport
        notification_widget = NotificationWidget(notification)
        self.viewport.add(notification_widget)

        # Expand to overlay mode with larger size
        self._expand_notification()

        logger.info(f"[NotificationBubble] Added NotificationWidget to viewport")
        logger.info(f"[NotificationBubble] Viewport children: {len(self.viewport.children)}")

        # Cancel any existing timeout
        if self.auto_dismiss_timeout:
            from gi.repository import GLib

            GLib.source_remove(self.auto_dismiss_timeout)
            self.auto_dismiss_timeout = None

        # Show the bubble - use same pattern as calendar
        logger.info(
            f"[NotificationBubble] Showing notification: {notification.summary}"
        )

        # Show window and all child widgets like calendar does
        self.set_visible(True)
        self.show_all()

        # Force refresh like calendar does
        self.viewport.show_all()

        # Debug window properties
        logger.info(f"[NotificationBubble] Window visible: {self.get_visible()}")
        logger.info(f"[NotificationBubble] Viewport visible: {self.viewport.get_visible()}")
        logger.info(f"[NotificationBubble] Expanded state: {self._is_expanded}")

        # Set auto-dismiss timeout (5 seconds)
        from gi.repository import GLib
        self.auto_dismiss_timeout = GLib.timeout_add_seconds(5, self._auto_dismiss)

    def _expand_notification(self):
        """Expand notification to appear as part of bar"""
        if not self._is_expanded:
            # Animate viewport expansion
            self.viewport.remove_style_class("collapsed")
            self.viewport.add_style_class("expanded")
            # Stay on same layer and position, just expand size
            self.set_size_request(350, -1)  # Expand width for notification
            self._is_expanded = True
            logger.info("[NotificationBubble] Expanded as part of bar")

    def _contract_notification(self):
        """Contract notification back to invisible state"""
        if self._is_expanded:
            # Animate viewport collapse
            self.viewport.remove_style_class("expanded")
            self.viewport.add_style_class("collapsed")

            # Delay the window resize until after animation completes
            from gi.repository import GLib
            def _finish_contract():
                self.set_size_request(0, 42)  # Zero width = invisible
                return False  # Don't repeat

            GLib.timeout_add(300, _finish_contract)  # Match CSS animation duration
            self._is_expanded = False
            logger.info("[NotificationBubble] Contracted to invisible state")

    def hide_notification(self):
        """Hide the notification bubble"""
        # Cancel auto-dismiss timeout if active
        if self.auto_dismiss_timeout:
            from gi.repository import GLib

            GLib.source_remove(self.auto_dismiss_timeout)
            self.auto_dismiss_timeout = None

        # Start the contract animation first
        self._contract_notification()

        # Clear viewport after animation completes
        from gi.repository import GLib
        def _finish_hide():
            for child in self.viewport.children[:]:
                self.viewport.remove(child)
            self.current_notification = None
            return False  # Don't repeat

        GLib.timeout_add(300, _finish_hide)  # Match CSS animation duration
        logger.info("[NotificationBubble] Contracted notification bubble")

    def _auto_dismiss(self):
        """Auto-dismiss the notification after timeout"""
        logger.info("[NotificationBubble] Auto-dismissing notification")
        if self.current_notification and self.dismiss_callback:
            self.dismiss_callback(self.current_notification.id)
        else:
            self.hide_notification()
        self.auto_dismiss_timeout = None
        return False  # Don't repeat the timeout

    def set_dismiss_callback(self, callback):
        """Set callback for when notification is dismissed"""
        self.dismiss_callback = callback

    def _on_close_clicked(self, button):
        """Handle close button click"""
        if self.current_notification and self.dismiss_callback:
            self.dismiss_callback(self.current_notification.id)


class NotificationIndicator(Button):
    """A clickable indicator that shows notification count and opens sidebar"""

    def __init__(self):
        super().__init__(name="notification-indicator", on_clicked=self._on_clicked)

        self.icon = Image(
            name="notification-indicator-icon",
            icon_name="preferences-system-notifications-symbolic",
            icon_size=16,
        )

        self.count_label = Label(name="notification-count", label="", visible=False)

        # Container for icon and count
        self.indicator_box = Box(
            name="notification-indicator-box",
            orientation="h",
            spacing=4,
            children=[self.icon, self.count_label],
        )

        self.child = self.indicator_box
        self.unread_count = 0
        self.toggle_callback = None

    def update_count(self, count: int):
        """Update the notification count display"""
        self.unread_count = count

        if count > 0:
            self.count_label.label = str(count) if count < 100 else "99+"
            self.count_label.set_visible(True)
            self.icon.icon_name = "preferences-system-notifications-symbolic"
        else:
            self.count_label.set_visible(False)
            self.icon.icon_name = "preferences-system-notifications-symbolic"

    def set_toggle_callback(self, callback):
        """Set callback for when sidebar toggle is requested"""
        self.toggle_callback = callback

    def _on_clicked(self, button):
        """Handle indicator click to open sidebar"""
        logger.info(f"[NotificationIndicator] Clicked!")
        if self.toggle_callback:
            logger.info(f"[NotificationIndicator] Calling toggle callback")
            self.toggle_callback()
        else:
            logger.warning(f"[NotificationIndicator] No toggle callback set!")


class NotificationHistorySidebar(Window):
    """A sidebar window showing notification history"""

    def __init__(self):
        super().__init__(
            name="notification-sidebar",
            layer="overlay",
            anchor="top right",
            margin="40px 8px 8px 8px",  # Top margin to avoid bar
            exclusivity="normal",
            visible=False,
            all_visible=False,
        )

        # Header with title and clear button
        self.header = Box(
            name="notification-header",
            orientation="h",
            spacing=8,
            children=[
                Label(name="notification-sidebar-title", label="Notifications"),
                Button(
                    name="notification-clear-all",
                    child=Label("Clear All"),
                    on_clicked=self._on_clear_all,
                ),
            ],
        )

        # Scrollable list of notifications
        self.notification_list = Box(
            name="notification-list", orientation="v", spacing=4
        )

        # Main container
        self.main_box = Box(
            name="notification-sidebar-content",
            orientation="v",
            spacing=8,
            children=[self.header, self.notification_list],
        )

        self.child = self.main_box
        self.set_size_request(350, 500)
        self.dismiss_callback = None
        self.clear_callback = None

    def update_notifications(self, notifications):
        """Update the sidebar with new notification list"""
        # Clear existing children
        for child in self.notification_list.children[:]:
            self.notification_list.remove(child)

        # Add new notification items
        for notification in notifications[:20]:  # Limit to 20 most recent
            item = self._create_notification_item(notification)
            self.notification_list.add(item)

        logger.info(
            f"[NotificationSidebar] Updated with {len(notifications)} notifications"
        )

    def _create_notification_item(self, notification: Notification) -> Box:
        """Create a widget for a single notification in the history"""
        # Time display
        time_str = notification.timestamp.strftime("%H:%M")

        # App name and time
        header_label = Label(
            name="notification-item-header",
            label=f"{notification.app_name} • {time_str}",
        )

        # Summary
        summary_label = Label(
            name="notification-item-summary",
            label=notification.summary,
            max_width_chars=40,
            ellipsize="end",
        )

        # Body (if exists)
        children = [header_label, summary_label]
        if notification.body:
            body_label = Label(
                name="notification-item-body",
                label=notification.body,
                max_width_chars=45,
                ellipsize="end",
            )
            children.append(body_label)

        # Dismiss button
        dismiss_button = Button(
            name="notification-item-dismiss",
            child=Image(icon_name="window-close-symbolic", icon_size=12),
            on_clicked=lambda btn, notif_id=notification.id: self._on_dismiss_clicked(
                notif_id
            ),
        )

        # Content box
        content_box = Box(
            name="notification-item-content",
            orientation="v",
            spacing=2,
            children=children,
        )

        # Main item container
        item_box = Box(
            name="notification-item",
            orientation="h",
            spacing=8,
            children=[content_box, dismiss_button],
        )

        # Add styling based on status
        if notification.dismissed:
            item_box.add_style_class("dismissed")

        return item_box

    def set_dismiss_callback(self, callback):
        """Set callback for when a notification is dismissed"""
        self.dismiss_callback = callback

    def set_clear_callback(self, callback):
        """Set callback for when clear all is requested"""
        self.clear_callback = callback

    def _on_dismiss_clicked(self, notification_id):
        """Handle dismiss button click"""
        if self.dismiss_callback:
            self.dismiss_callback(notification_id)

    def _on_clear_all(self, button):
        """Handle clear all button click"""
        if self.clear_callback:
            self.clear_callback()

    def toggle_visibility(self):
        """Toggle sidebar visibility"""
        current_visibility = self.get_visible()
        new_visibility = not current_visibility
        logger.info(
            f"[NotificationSidebar] Toggling visibility: {current_visibility} -> {new_visibility}"
        )
        self.set_visible(new_visibility)
        logger.info(
            f"[NotificationSidebar] Visibility after toggle: {self.get_visible()}"
        )


class NotificationManager:
    """Main notification manager that coordinates bubble, indicator, and sidebar"""

    def __init__(self):
        # Initialize components
        logger.info("[NotificationManager] Initializing notification components...")
        self.service = NotificationService()
        logger.info("[NotificationManager] NotificationService created")

        self.bubble = NotificationBubble()
        self.indicator = NotificationIndicator()
        self.sidebar = NotificationHistorySidebar()
        logger.info("[NotificationManager] Widgets created")

        # Connect signals from service
        self.service.connect(
            "current-notification-changed", self._on_current_notification_changed
        )
        self.service.connect("history-changed", self._on_history_changed)

        # Set callbacks for widgets
        self.bubble.set_dismiss_callback(self._on_bubble_dismiss)
        self.indicator.set_toggle_callback(self._on_sidebar_toggle)
        self.sidebar.set_dismiss_callback(self._on_sidebar_dismiss)
        self.sidebar.set_clear_callback(self._on_clear_all)

        logger.info("[NotificationManager] Initialized successfully")

    def get_indicator(self) -> NotificationIndicator:
        """Get the notification indicator for placement in the bar"""
        return self.indicator

    def get_sidebar(self) -> NotificationHistorySidebar:
        """Get the notification sidebar window"""
        return self.sidebar

    def get_bubble(self) -> NotificationBubble:
        """Get the notification bubble window"""
        return self.bubble

    def _on_current_notification_changed(self, service, notification):
        """Handle current notification change"""
        logger.info(
            f"[NotificationManager] Current notification changed: {notification.summary if notification else None}"
        )

        if notification:
            logger.info(f"[NotificationManager] Showing notification bubble")
            self.bubble.show_notification(notification)
        else:
            logger.info(f"[NotificationManager] Hiding notification bubble")
            self.bubble.hide_notification()

    def _on_history_changed(self, service, notifications):
        """Handle notification history change"""
        unread_count = self.service.get_unread_count()
        logger.info(
            f"[NotificationManager] History changed: {len(notifications)} total, {unread_count} unread"
        )

        self.indicator.update_count(unread_count)
        self.sidebar.update_notifications(notifications)

    def _on_bubble_dismiss(self, notification_id):
        """Handle bubble dismiss request"""
        self.service.dismiss_notification(notification_id)
        # Show next notification if available
        self.service.show_next_notification()

    def _on_sidebar_toggle(self):
        """Handle sidebar toggle request"""
        logger.info(f"[NotificationManager] Sidebar toggle requested")
        self.sidebar.toggle_visibility()

    def _on_sidebar_dismiss(self, notification_id):
        """Handle sidebar dismiss request"""
        self.service.dismiss_notification(notification_id)

    def _on_clear_all(self):
        """Handle clear all request"""
        self.service.clear_history()
        self.sidebar.set_visible(False)
