from datetime import datetime
from typing import List, Dict, Optional, Callable
from fabric.notifications import Notifications
from loguru import logger


class Notification:
    def __init__(self, id: int, app_name: str, summary: str, body: str = "",
                 app_icon: str = "", urgency: int = 1, actions: List = None,
                 timeout: int = -1, timestamp: datetime = None):
        self.id = id
        self.app_name = app_name
        self.summary = summary
        self.body = body
        self.app_icon = app_icon
        self.urgency = urgency
        self.actions = actions or []
        self.timeout = timeout
        self.timestamp = timestamp or datetime.now()
        self.dismissed = False

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'app_name': self.app_name,
            'summary': self.summary,
            'body': self.body,
            'app_icon': self.app_icon,
            'urgency': self.urgency,
            'actions': self.actions,
            'timeout': self.timeout,
            'timestamp': self.timestamp.isoformat(),
            'dismissed': self.dismissed
        }


class NotificationService:
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.notifications: List[Notification] = []
        self.current_notification: Optional[Notification] = None
        self.fabric_notifications = Notifications()

        # Simple callback system instead of GObject signals
        self.callbacks = {
            "current-notification-changed": [],
            "notification-added": [],
            "history-changed": []
        }

        # Connect to fabric notification signals
        self.fabric_notifications.connect("notification-added", self._on_notification_added)
        self.fabric_notifications.connect("notification-closed", self._on_notification_dismissed)

        logger.info("[Notifications] Service initialized")
        logger.info(f"[Notifications] Connected to fabric notifications: {self.fabric_notifications}")
        logger.info(f"[Notifications] Available signals: {self.fabric_notifications.get_signal_names()}")

    def connect(self, signal_name: str, callback: Callable):
        """Connect callback to signal"""
        if signal_name in self.callbacks:
            self.callbacks[signal_name].append(callback)

    def _emit(self, signal_name: str, *args):
        """Emit signal to all connected callbacks"""
        if signal_name in self.callbacks:
            for callback in self.callbacks[signal_name]:
                callback(self, *args)

    def _on_notification_added(self, notifications_service, notification_id: int):
        """Handle new notification from fabric"""
        logger.info(f"[Notifications] Signal received: notification-added with ID {notification_id}")
        try:
            notification_data = self.fabric_notifications.get_notification_from_id(notification_id)
            logger.info(f"[Notifications] Raw notification data: {notification_data}")

            if not notification_data:
                logger.warning(f"[Notifications] Could not get notification data for ID {notification_id}")
                return

            # notification_data is a Fabric Notification object, not a dict
            notification = Notification(
                id=notification_id,
                app_name=getattr(notification_data, 'app_name', 'Unknown'),
                summary=getattr(notification_data, 'summary', ''),
                body=getattr(notification_data, 'body', ''),
                app_icon=getattr(notification_data, 'app_icon', ''),
                urgency=getattr(notification_data, 'urgency', 1),
                actions=getattr(notification_data, 'actions', []),
                timeout=getattr(notification_data, 'timeout', -1)
            )

            self._add_notification(notification)
            logger.info(f"[Notifications] Added notification: {notification.summary}")

        except Exception as e:
            logger.error(f"[Notifications] Error handling notification: {e}")
            import traceback
            logger.error(f"[Notifications] Traceback: {traceback.format_exc()}")

    def _on_notification_dismissed(self, notifications_service, notification_id: int):
        """Handle notification dismissal from fabric"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.dismissed = True
                if self.current_notification and self.current_notification.id == notification_id:
                    self.current_notification = None
                    self._emit("current-notification-changed", None)
                logger.info(f"[Notifications] Dismissed notification: {notification.summary}")
                break

    def _add_notification(self, notification: Notification):
        """Add a notification to history and set as current"""
        # Add to beginning of list (most recent first)
        self.notifications.insert(0, notification)

        # Limit history size
        if len(self.notifications) > self.max_history:
            self.notifications = self.notifications[:self.max_history]

        # Set as current notification if none exists
        if not self.current_notification or self.current_notification.dismissed:
            self.current_notification = notification
            self._emit("current-notification-changed", notification)

        # Emit signals for UI updates
        self._emit("notification-added", notification)
        self._emit("history-changed", self.notifications)

    def get_current_notification(self) -> Optional[Notification]:
        """Get the current notification being displayed"""
        return self.current_notification

    def get_notification_history(self) -> List[Notification]:
        """Get all notifications in history (most recent first)"""
        return self.notifications.copy()

    def get_unread_count(self) -> int:
        """Get count of unread/undismissed notifications"""
        return len([n for n in self.notifications if not n.dismissed])

    def dismiss_current_notification(self):
        """Dismiss the current notification"""
        if self.current_notification:
            self.fabric_notifications.close_notification(self.current_notification.id)
            self.current_notification.dismissed = True
            self.current_notification = None
            self._emit("current-notification-changed", None)

    def dismiss_notification(self, notification_id: int):
        """Dismiss a specific notification by ID"""
        self.fabric_notifications.close_notification(notification_id)

    def show_next_notification(self):
        """Show the next undismissed notification"""
        for notification in self.notifications:
            if not notification.dismissed:
                self.current_notification = notification
                self._emit("current-notification-changed", notification)
                return

        # No undismissed notifications
        self.current_notification = None
        self._emit("current-notification-changed", None)

    def clear_history(self):
        """Clear all notification history"""
        self.notifications.clear()
        self.current_notification = None
        self._emit("current-notification-changed", None)
        self._emit("history-changed", [])