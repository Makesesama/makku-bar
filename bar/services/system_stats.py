import psutil
from fabric.core.service import Service, Signal
from fabric.utils import invoke_repeater


class SystemStatsService(Service):
    @Signal
    def stats_changed(self, cpu_percent: float, memory_percent: float) -> None:
        """Signal emitted when system stats change"""
        pass

    def __init__(self, update_interval=3000, **kwargs):
        super().__init__(**kwargs)
        self._cpu_percent = 0.0
        self._memory_percent = 0.0
        self._update_interval = update_interval
        self._timer_id = None

        # Start periodic updates
        self.start_monitoring()

    def start_monitoring(self):
        """Start monitoring system stats"""
        if self._timer_id is None:
            # Get initial values
            self._update_stats()
            # Set up periodic updates
            self._timer_id = invoke_repeater(self._update_interval, self._update_stats)

    def stop_monitoring(self):
        """Stop monitoring system stats"""
        if self._timer_id is not None:
            from gi.repository import GLib

            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _update_stats(self):
        """Update system stats and emit signal if changed"""
        try:
            new_cpu = psutil.cpu_percent()
            new_memory = psutil.virtual_memory().percent

            # Only emit signal if values changed significantly (reduce noise)
            cpu_changed = abs(new_cpu - self._cpu_percent) > 1.0
            memory_changed = abs(new_memory - self._memory_percent) > 1.0

            if cpu_changed or memory_changed:
                self._cpu_percent = new_cpu
                self._memory_percent = new_memory
                self.stats_changed(new_cpu / 100, new_memory / 100)

        except Exception as e:
            print(f"Error updating system stats: {e}")

        return True  # Keep the timer running

    @property
    def cpu_percent(self):
        """Get current CPU percentage"""
        return self._cpu_percent / 100

    @property
    def memory_percent(self):
        """Get current memory percentage"""
        return self._memory_percent / 100
