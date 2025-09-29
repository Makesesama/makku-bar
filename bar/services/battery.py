import psutil
from fabric.core.service import Service, Signal
from fabric.utils import invoke_repeater


class BatteryService(Service):
    @Signal
    def battery_changed(self, percent: float, charging: bool) -> None:
        """Signal emitted when battery status changes"""
        pass

    def __init__(self, update_interval=10000, **kwargs):  # Check every 10 seconds
        super().__init__(**kwargs)
        self._percent = 0.0
        self._charging = False
        self._update_interval = update_interval
        self._timer_id = None

        # Start periodic updates
        self.start_monitoring()

    def start_monitoring(self):
        """Start monitoring battery status"""
        if self._timer_id is None:
            # Get initial values
            self._update_battery()
            # Set up periodic updates
            self._timer_id = invoke_repeater(self._update_interval, self._update_battery)

    def stop_monitoring(self):
        """Stop monitoring battery status"""
        if self._timer_id is not None:
            from gi.repository import GLib
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _update_battery(self):
        """Update battery status and emit signal if changed"""
        try:
            # Use the same pattern as the example
            bat_sen = psutil.sensors_battery()
            if not bat_sen:
                # No battery sensor available (desktop systems)
                new_percent = 100.0  # Assume plugged in
                new_charging = True
            else:
                new_percent = bat_sen.percent
                new_charging = bat_sen.power_plugged

            # Only emit signal if values changed
            percent_changed = abs(new_percent - self._percent) > 0.5
            charging_changed = new_charging != self._charging

            if percent_changed or charging_changed:
                self._percent = new_percent
                self._charging = new_charging
                self.battery_changed(new_percent, new_charging)

        except Exception as e:
            print(f"Error updating battery status: {e}")

        return True  # Keep the timer running

    @property
    def percent(self):
        """Get current battery percentage"""
        return self._percent

    @property
    def charging(self):
        """Get current charging status"""
        return self._charging