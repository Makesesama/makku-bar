from loguru import logger

# Configure logging based on dev flag
from .config import DEV
if DEV:
    # In dev mode, disable fabric logs but keep stylix and bar logs
    logger.disable("fabric")
else:
    # In production, disable all debug logs, only keep warnings and errors
    logger.disable("fabric")
    logger.disable("bar")
    logger.configure(handlers=[{"sink": lambda msg: print(msg, end=""), "level": "WARNING"}])

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
from .modules.stylix import get_colors_css_path
from .config import STYLIX


tray = SystemTray(name="system-tray", spacing=4)
river = get_river_connection()

dummy = Window(visible=False)
finder = FuzzyWindowFinder()

bar_windows = []

app = Application("bar", dummy, finder)

# Generate colors.css (either Stylix or default) in XDG config directory
colors_css_path = get_colors_css_path()
if colors_css_path:
    # Update main.css to import the generated colors.css
    import tempfile
    with open(get_relative_path("styles/main.css"), "r") as f:
        main_css = f.read()

    # Replace the colors.css import with our generated file path
    updated_main_css = main_css.replace(
        '@import url("./colors.css");',
        f'@import url("file://{colors_css_path}");'
    )

    # Write updated main.css to temp file and load it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False) as temp_main:
        temp_main.write(updated_main_css)
        temp_main_path = temp_main.name

    logger.info(f"[Bar] Loading CSS with colors from {colors_css_path}")
    app.set_stylesheet_from_file(temp_main_path)
else:
    logger.error("[Bar] Failed to generate colors.css, falling back to default")
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
