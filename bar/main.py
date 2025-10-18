from loguru import logger

# Configure logging based on dev flag
from .config import DEV, LOG_LEVEL
if DEV:
    # In dev mode, disable fabric logs but keep stylix and bar logs
    logger.disable("fabric")
else:
    # In production, disable fabric logs but keep bar logs with configurable level
    import sys
    logger.disable("fabric")
    logger.configure(handlers=[{"sink": sys.stderr, "level": LOG_LEVEL, "format": "{time} | {level} | {name}:{function}:{line} - {message}"}])

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
from .modules.stylix import get_stylix_css_path
from .config import STYLIX


tray = SystemTray(name="system-tray", spacing=4)
river = get_river_connection()

dummy = Window(visible=False)
finder = FuzzyWindowFinder()

bar_windows = []
notmuch_widget = None

app = Application("bar", dummy, finder)

# Load CSS - use Stylix if enabled, otherwise use default
if STYLIX.get("enable", False):
    stylix_css_path = get_stylix_css_path()
    if stylix_css_path:
        logger.info("[Bar] Using Stylix CSS")
        # Load base styles first for structure
        app.set_stylesheet_from_file(get_relative_path("styles/main.css"))
        # Then apply Stylix theme colors
        app.set_stylesheet_from_file(stylix_css_path)
    else:
        logger.warning("[Bar] Stylix enabled but CSS generation failed, falling back to default")
        app.set_stylesheet_from_file(get_relative_path("styles/main.css"))
else:
    logger.info("[Bar] Using default CSS")
    app.set_stylesheet_from_file(get_relative_path("styles/main.css"))


def spawn_bars():
    global notmuch_widget
    logger.info("[Bar] Spawning bars after river ready")
    outputs = river.outputs

    if not outputs:
        logger.warning("[Bar] No outputs found — skipping bar spawn")
        return

    output_ids = sorted(outputs.keys())

    for i, output_id in enumerate(output_ids):
        bar = StatusBar(display=output_id, tray=tray if i == 0 else None, monitor=i)
        bar_windows.append(bar)
        if i == 0 and bar.notmuch:
            notmuch_widget = bar.notmuch

    return False


def main():
    if river.ready:
        spawn_bars()
    else:
        river.connect("notify::ready", lambda sender, pspec: spawn_bars())

    app.run()


if __name__ == "__main__":
    main()
