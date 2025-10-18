from bar.config import STYLIX
import tempfile
import os


def generate_stylix_variables():
    """Generate CSS variables from Stylix configuration for use with regular CSS files"""
    if not STYLIX.get("enable", False):
        return ""

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

    # Generate :vars block matching the original colors.css structure
    css_variables = f""":vars {{
    /* Base background colors */
    --background: #{colors["base00"]};
    --mid-bg: #{colors["base01"]};
    --light-bg: #{colors["base02"]};
    --dark-grey: #{colors["base03"]};
    --light-grey: #{colors["base04"]};
    --dark-fg: #{colors["base04"]};
    --mid-fg: #{colors["base05"]};
    --foreground: #{colors["base05"]};

    /* Accent colors mapped to original names */
    --pink: #{colors["base08"]};
    --orange: #{colors["base09"]};
    --gold: #{colors["base0A"]};
    --lime: #{colors["base0B"]};
    --turquoise: #{colors["base0C"]};
    --blue: #{colors["base0D"]};
    --violet: #{colors["base0E"]};
    --red: #{colors["base08"]};

    /* Derived colors matching original structure */
    --window-bg: alpha(var(--background), 0.9);
    --module-bg: alpha(var(--mid-bg), 0.8);
    --border-color: var(--light-bg);
    --ws-active: var(--pink);
    --ws-inactive: var(--blue);
    --ws-empty: var(--dark-grey);
    --ws-hover: var(--turquoise);
    --ws-urgent: var(--red);

    /* Additional Base16 colors for notifications */
    --border: #{colors["base02"]};
    --accent: #{colors["base0D"]};
    --warning: #{colors["base09"]};
    --error: #{colors["base08"]};
    --success: #{colors["base0B"]};

    /* Missing variables that notifications.css expects */
    --background-alt: #{colors["base01"]};
    --background-selected: #{colors["base02"]};
    --foreground-alt: #{colors["base04"]};
}}

"""

    return css_variables
