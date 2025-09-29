from gi.repository import GLib
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.image import Image
from bar.services.battery import BatteryService


class Battery(Box):
    def __init__(self, **kwargs):
        super().__init__(name="battery-widget", orientation="h", spacing=4, **kwargs)

        self.bat_icon = Image(
            name="bat-icon", icon_name="battery-full-symbolic", icon_size=16
        )

        self.bat_label = Label(name="bat-label", label="100%")

        # Create battery service with signal-based updates
        self.battery_service = BatteryService(update_interval=10000)  # Check every 10 seconds
        self.battery_service.connect("battery-changed", self.update_battery)

        self.children = [self.bat_icon, self.bat_label]
        self.show_all()

        # Initialize with current battery status
        initial_percent = self.battery_service.percent
        initial_charging = self.battery_service.charging
        GLib.idle_add(self.update_battery, None, initial_percent, initial_charging)

    def _icon_lookup(self, bat, charging):
        # Round to nearest 10 for level-based icons
        level = max(10, min(100, round(bat / 10) * 10))

        if charging:
            return f"battery-level-{level}-charging-symbolic"
        else:
            return f"battery-level-{level}-symbolic"

    def update_battery(self, service, percent, charging):
        """Update battery display when battery status changes"""
        icon_name = self._icon_lookup(percent, charging)
        self.bat_icon.set_property("icon-name", icon_name)

        self.bat_label.set_text(f"{int(percent)}%")

        if percent < 20 and not charging:
            self.bat_label.add_style_class("battery-low")
            self.bat_icon.add_style_class("battery-low")
        else:
            self.bat_label.remove_style_class("battery-low")
            self.bat_icon.remove_style_class("battery-low")
