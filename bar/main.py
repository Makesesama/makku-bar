from loguru import logger

# Configure logging based on dev flag
from .config import DEV
if DEV:
    # In dev mode, disable fabric logs but keep stylix and bar logs
    logger.disable("fabric")
else:
    # In production, disable fabric logs but keep bar logs for debugging
    import sys
    logger.disable("fabric")
    logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO", "format": "{time} | {level} | {name}:{function}:{line} - {message}"}])

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
from .modules.stylix import generate_stylix_variables
from .config import STYLIX


tray = SystemTray(name="system-tray", spacing=4)
river = get_river_connection()

dummy = Window(visible=False)
finder = FuzzyWindowFinder()

bar_windows = []

app = Application("bar", dummy, finder)

# Load CSS with unified system
# Read main.css which includes all imports
try:
    main_css_path = get_relative_path("styles/main.css")
    with open(main_css_path, 'r') as f:
        main_css = f.read()
except FileNotFoundError:
    logger.error("[Bar] main.css not found!")
    main_css = ""

# Remove notifications.css import from main.css since we'll add it manually at the end
main_css = main_css.replace('@import url("./notifications.css");', '/* notifications.css added manually at end */')

# Read notifications.css separately so we can add it AFTER the universal reset
try:
    notifications_css_path = get_relative_path("styles/notifications.css")
    with open(notifications_css_path, 'r') as f:
        notifications_css = f.read()
except FileNotFoundError:
    logger.warning("[Bar] notifications.css not found!")
    notifications_css = ""

if STYLIX.get("enable", False):
    logger.info("[Bar] Using Stylix CSS variables")

    # Generate Stylix variables and replace colors.css
    stylix_vars = generate_stylix_variables()
    logger.info(f"[Bar] Generated {len(stylix_vars)} characters of Stylix variables")

    original_css = main_css
    main_css = main_css.replace('@import url("./colors.css");', '/* colors.css replaced by Stylix variables */')

    if original_css == main_css:
        logger.warning("[Bar] colors.css import not found or not replaced!")
    else:
        logger.info("[Bar] Successfully replaced colors.css import")

    # Combine: Stylix variables + notifications CSS (before reset) + main CSS + notifications CSS (after reset)
    combined_css = stylix_vars + "\n\n/* === NOTIFICATION STYLES BEFORE RESET === */\n" + notifications_css + "\n\n" + main_css + "\n\n/* === NOTIFICATION STYLES AFTER RESET === */\n" + notifications_css
    logger.info(f"[Bar] Combined CSS length: {len(combined_css)} characters")
else:
    logger.info("[Bar] Using default CSS with original colors.css")
    # Combine: notifications CSS (before reset) + main CSS + notifications CSS (after reset)
    combined_css = "\n\n/* === NOTIFICATION STYLES BEFORE RESET === */\n" + notifications_css + "\n\n" + main_css + "\n\n/* === NOTIFICATION STYLES AFTER RESET === */\n" + notifications_css

# Debug: Write combined CSS to file for inspection
debug_css_path = "/tmp/makku_bar_combined.css"
try:
    with open(debug_css_path, 'w') as f:
        f.write(combined_css)
    logger.info(f"[Bar] Debug: Combined CSS written to {debug_css_path}")
except Exception as e:
    logger.warning(f"[Bar] Could not write debug CSS: {e}")

# Always use compile_css for consistent processing
app.set_stylesheet_from_string(combined_css, compile=True, base_path=get_relative_path("styles"))


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

        # Add notification windows for first monitor only
        if i == 0 and bar.notification_manager:
            sidebar = bar.notification_manager.get_sidebar()
            bubble = bar.notification_manager.get_bubble()
            app.add_window(sidebar)
            app.add_window(bubble)

    return False


def main():
    if river.ready:
        spawn_bars()
    else:
        river.connect("notify::ready", lambda sender, pspec: spawn_bars())

    app.run()


if __name__ == "__main__":
    main()
