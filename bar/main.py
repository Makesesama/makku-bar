from loguru import logger

from fabric import Application
from fabric.system_tray.widgets import SystemTray
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.river.widgets import (
    get_river_connection,
)
from fabric.utils import (
    get_relative_path,
)
from .modules.bar import StatusBar
from .modules.window_fuzzy import FuzzyWindowFinder


tray = SystemTray(name="system-tray", spacing=4)
river = get_river_connection()

dummy = Window(visible=False)
finder = FuzzyWindowFinder()

bar_windows = []

app = Application("bar", dummy, finder)
app.set_stylesheet_from_file(get_relative_path("styles/main.css"))


def spawn_bars():
    logger.info("[Bar] Spawning bars after river ready")
    outputs = river.outputs

    if not outputs:
        logger.warning("[Bar] No outputs found — skipping bar spawn")
        return

    output_ids = sorted(outputs.keys())

    for i, output_id in enumerate(output_ids):
        bar = StatusBar(display=output_id, tray=tray if i == 0 else None, monitor=i)
        bar_windows.append(bar)

    return False


def main():
    if river.ready:
        spawn_bars()
    else:
        river.connect("notify::ready", lambda sender, pspec: spawn_bars())

    app.run()


if __name__ == "__main__":
    main()
