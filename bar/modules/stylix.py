from bar.config import STYLIX
import tempfile
import os


def generate_stylix_css():
    """Generate CSS using Stylix colors if enabled"""
    if not STYLIX.get("enable", False):
        return None

    colors = STYLIX.get("colors", {})
    fonts = STYLIX.get("fonts", {})

    # Default colors if Stylix is not properly configured
    default_colors = {
        "base00": "1e1e2e",  # background
        "base01": "313244",  # lighter background
        "base02": "45475a",  # selection background
        "base03": "585b70",  # comments
        "base04": "bac2de",  # dark foreground
        "base05": "cdd6f4",  # foreground
        "base06": "f5e0dc",  # light foreground
        "base07": "b4befe",  # light background
        "base08": "f38ba8",  # red
        "base09": "fab387",  # orange
        "base0A": "f9e2af",  # yellow
        "base0B": "a6e3a1",  # green
        "base0C": "94e2d5",  # cyan
        "base0D": "89b4fa",  # blue
        "base0E": "cba6f7",  # purple
        "base0F": "f2cdcd",  # brown
    }

    # Use Stylix colors or fallback to defaults
    for key in default_colors:
        if key not in colors:
            colors[key] = default_colors[key]

    # Default font
    font_family = fonts.get("sansSerif", "sans-serif")
    font_sizes = fonts.get("sizes", {})
    # Use desktop font size for the bar, fallback to applications, then default
    font_size = font_sizes.get("desktop", font_sizes.get("applications", 14))

    # Calculate relative font sizes
    small_font = max(int(font_size * 0.85), 10)  # Minimum 10px
    large_font = int(font_size * 1.1)

    # Debug logging
    from loguru import logger
    logger.info(f"[Stylix] Using font sizes - Base: {font_size}px, Small: {small_font}px, Large: {large_font}px")

    # Generate GTK CSS with Stylix colors
    css_content = f"""/* Stylix-generated theme */

/* Apply Stylix font */
* {{
    font-family: "{font_family}", sans-serif;
    font-size: {font_size}px;
}}

/* Bar styling */
#bar-inner {{
    padding: 4px;
    border-bottom: solid 2px;
    border-color: #{colors["base02"]};
    background-color: #{colors["base00"]};
}}

#center-container {{
    color: #{colors["base05"]};
}}

.active-window {{
    color: #{colors["base05"]};
    font-weight: bold;
}}

/* Battery */
#battery-widget {{
    background-color: #{colors["base01"]};
    padding: 4px 8px;
    border-radius: 12px;
}}

#bat-icon {{
    color: #{colors["base0D"]};
    margin-right: 2px;
}}

#bat-label {{
    color: #{colors["base05"]};
    font-size: {font_size}px;
}}

#bat-label.battery-low {{
    color: #{colors["base08"]};
    font-weight: bold;
}}

/* Progress bars */
#cpu-progress-bar,
#ram-progress-bar,
#volume-progress-bar {{
    color: transparent;
    background-color: transparent;
}}

#cpu-progress-bar {{
    border: solid 0px alpha(#{colors["base0E"]}, 0.8);
}}

#ram-progress-bar,
#volume-progress-bar {{
    border: solid 0px #{colors["base0D"]};
}}

/* Widgets container */
#widgets-container {{
    background-color: #{colors["base01"]};
    padding: 2px;
    border-radius: 16px;
}}

/* NixOS label */
#nixos-label {{
    color: #{colors["base0D"]};
}}

/* Date time */
#date-time {{
    color: #{colors["base05"]};
    background-color: #{colors["base01"]};
    padding: 4px 8px;
    border-radius: 12px;
}}

#date-time-button {{
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    box-shadow: none;
}}

/* Calendar popup */
#calendar-popup {{
    background-color: #{colors["base00"]};
    border: solid 2px #{colors["base02"]};
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    animation: slide-down 200ms ease-out;
}}

@keyframes slide-down {{
    from {{
        opacity: 0;
        margin-top: -20px;
    }}
    to {{
        opacity: 1;
        margin-top: 10px;
    }}
}}

#calendar-title {{
    color: #{colors["base05"]};
    font-weight: bold;
    font-size: {large_font}px;
    margin-bottom: 8px;
}}

#events-box {{
    background-color: #{colors["base00"]};
    border: solid 1px #{colors["base02"]};
    border-radius: 8px;
    padding: 16px;
}}

#no-events {{
    color: #{colors["base03"]};
}}

/* Calendar event items */
.event-item {{
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px 0px;
    transition: background-color 0.15s ease;
}}

#event-content {{
    margin-left: 8px;
}}

.event-item.upcoming {{
    background-color: #{colors["base01"]};
}}

.event-item.past {{
    background-color: #{colors["base01"]};
    opacity: 0.6;
}}

.event-title {{
    font-weight: bold;
    font-size: {font_size}px;
}}

.event-title.upcoming {{
    color: #{colors["base05"]};
}}

.event-title.past {{
    color: #{colors["base04"]};
}}

.event-time {{
    font-size: {small_font}px;
}}

.event-time.upcoming {{
    color: #{colors["base04"]};
}}

.event-time.past {{
    color: #{colors["base03"]};
}}

.event-location {{
    font-size: {small_font}px;
}}

.event-location.upcoming {{
    color: #{colors["base03"]};
}}

.event-location.past {{
    color: #{colors["base03"]};
    opacity: 0.8;
}}

/* Tooltips */
tooltip {{
    border: solid 2px;
    border-color: #{colors["base02"]};
    background-color: #{colors["base00"]};
    color: #{colors["base05"]};
    border-radius: 16px;
}}

tooltip>* {{
    padding: 2px 4px;
}}

/* Workspaces */
#workspaces {{
    background-color: #{colors["base01"]};
    padding: 6px 6px;
    border-radius: 16px;
}}

#workspaces>button {{
    background-color: #{colors["base05"]};
    border-radius: 100px;
    padding: 0px 4px;
    transition: padding 0.05s steps(8);
}}

#workspaces>button.active {{
    background-color: #{colors["base0D"]};
    padding: 0px 16px;
    border-radius: 100px;
}}

#workspaces>button>label {{
    font-size: 0px;
}}

#workspaces>button.empty:not(.active) {{
    background-color: #{colors["base03"]};
}}

#workspaces>button.urgent {{
    background-color: #{colors["base08"]};
}}
"""

    # Write to temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".css", prefix="stylix_")
    try:
        with os.fdopen(temp_fd, "w") as f:
            f.write(css_content)
        return temp_path
    except Exception:
        os.close(temp_fd)
        return None


def get_stylix_css_path():
    """Get the path to the Stylix CSS file"""
    return generate_stylix_css()
