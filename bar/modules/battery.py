import psutil
from gi.repository import GLib
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.icon import Icon
from fabric import Fabricator


class BatteryProvider:
    def __init__(self):
        self.bat_percent = 0.0
        self.bat_charging = None

        GLib.timeout_add_seconds(1, self._update)

    def _update(self):
        battery = psutil.sensors_battery()
        if battery is None:
            self.bat_percent = 0.0
            self.bat_charging = None
        else:
            self.bat_percent = battery.percent
            self.bat_charging = battery.power_plugged

        return True

    def get_battery(self):
        return (self.bat_percent, self.bat_charging)


class Battery(Box):
    def __init__(self, **kwargs):
        super().__init__(name="battery-widget", orientation="h", spacing=4, **kwargs)
        self.bat_provider = BatteryProvider()

        self.bat_icon = Icon(
            name="bat-icon",
            icon_name="battery-full-symbolic",
            icon_size=16
        )
        self.bat_label = Label(
            name="bat-label",
            label="100%"
        )

        self.bat_fabricator = Fabricator(
            poll_from=lambda: self.bat_provider.get_battery(),
            on_changed=self.update_battery,
            interval=1000,
            stream=False,
            default_value=(100, False),
        )

        self.children = [self.bat_icon, self.bat_label]
        self.show_all()

        GLib.idle_add(self.update_battery, None, self.bat_provider.get_battery())

    def _icon_lookup(self, bat, charging):
        if charging:
            return "battery-charging-symbolic"
        match bat:
            case _ if bat > 90:
                return "battery-full-symbolic"
            case _ if bat > 50:
                return "battery-good-symbolic"
            case _ if bat >= 20:
                return "battery-medium-symbolic"
            case _:
                return "battery-low-symbolic"

    def update_battery(self, sender, battery_data):
        value, charging = battery_data

        icon_name = self._icon_lookup(value, charging)
        self.bat_icon.set_property("icon-name", icon_name)

        self.bat_label.set_text(f"{int(value)}%")

        if value < 20 and not charging:
            self.bat_label.add_css_class("battery-low")
        else:
            self.bat_label.remove_css_class("battery-low")

        return True
