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
    font_size = fonts.get("sizes", {}).get("applications", 14)

    css_content = f"""
/* Stylix-generated colors */
:root {{
    --window-bg: #{colors["base00"]};
    --module-bg: #{colors["base01"]};
    --border-color: #{colors["base02"]};
    --foreground: #{colors["base05"]};
    --red: #{colors["base08"]};
    --orange: #{colors["base09"]};
    --yellow: #{colors["base0A"]};
    --green: #{colors["base0B"]};
    --cyan: #{colors["base0C"]};
    --blue: #{colors["base0D"]};
    --violet: #{colors["base0E"]};
    --purple: #{colors["base0E"]};
    --brown: #{colors["base0F"]};
}}

/* Apply Stylix font */
* {{
    font-family: "{font_family}", sans-serif;
    font-size: {font_size}px;
}}

/* Workspace styling */
.workspace-button {{
    background-color: #{colors["base01"]};
    color: #{colors["base05"]};
    border: 1px solid #{colors["base02"]};
    border-radius: 4px;
    padding: 4px 8px;
    margin: 2px;
}}

.workspace-button.active {{
    background-color: #{colors["base0D"]};
    color: #{colors["base00"]};
}}

.workspace-button.urgent {{
    background-color: #{colors["base08"]};
    color: #{colors["base00"]};
}}

/* Bar styling */
#bar-inner {{
    background-color: #{colors["base00"]};
    border-bottom: 2px solid #{colors["base02"]};
}}

/* System tray */
#system-tray {{
    background-color: #{colors["base01"]};
    border-radius: 4px;
}}

/* Date time */
#date-time {{
    color: #{colors["base05"]};
    background-color: #{colors["base01"]};
    padding: 4px 8px;
    border-radius: 4px;
}}

/* Progress bars */
#cpu-progress-bar {{
    color: #{colors["base0E"]};
}}

#ram-progress-bar,
#volume-progress-bar {{
    color: #{colors["base0D"]};
}}

/* Battery */
#battery-widget {{
    background-color: #{colors["base01"]};
    border-radius: 4px;
}}

#bat-icon {{
    color: #{colors["base0D"]};
}}

#bat-label {{
    color: #{colors["base05"]};
}}

#bat-label.battery-low {{
    color: #{colors["base08"]};
}}

/* Active window */
.active-window {{
    color: #{colors["base05"]};
}}

/* NixOS label */
#nixos-label {{
    color: #{colors["base0D"]};
}}

/* Widgets container */
#widgets-container {{
    background-color: #{colors["base01"]};
    border-radius: 4px;
}}

/* Tooltip */
tooltip {{
    background-color: #{colors["base00"]};
    border: 2px solid #{colors["base02"]};
    color: #{colors["base05"]};
}}
"""

    # Write to temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.css', prefix='stylix_')
    try:
        with os.fdopen(temp_fd, 'w') as f:
            f.write(css_content)
        return temp_path
    except Exception:
        os.close(temp_fd)
        return None


def get_stylix_css_path():
    """Get the path to the Stylix CSS file"""
    return generate_stylix_css()