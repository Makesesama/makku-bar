from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.wayland import WaylandWindow as Window
from gi.repository import Gtk
from loguru import logger


class QuickMenuItem(Box):
    """Base class for quick menu items"""
    def __init__(self, title, icon_name=None, **kwargs):
        super().__init__(
            orientation="h",
            spacing=12,
            name="quick-menu-item",
            **kwargs
        )
        self.set_style("padding: 8px 12px; min-width: 280px;")

        # Icon and title on the left
        left_box = Box(orientation="h", spacing=8)
        if icon_name:
            icon = Image(icon_name=icon_name, icon_size=16)
            left_box.add(icon)

        self.title_label = Label(title)
        self.title_label.set_style("font-size: 14px;")
        left_box.add(self.title_label)

        self.add(left_box)

        # Derived classes can add controls to the right side


class QuickMenuToggle(QuickMenuItem):
    """A menu item with a toggle switch"""
    def __init__(self, title, icon_name=None, active=False, on_toggle=None, **kwargs):
        super().__init__(title, icon_name, **kwargs)

        # Create a custom toggle using a button with state tracking
        self._active = active
        self._on_toggle = on_toggle

        # Create toggle indicator box
        self.toggle_box = Box(
            orientation="h",
            spacing=0
        )
        self.toggle_box.set_style("min-width: 44px; min-height: 24px; border-radius: 12px; padding: 2px;")

        # Toggle indicator (circle)
        self.toggle_indicator = Label("")
        self.toggle_indicator.set_style("min-width: 20px; min-height: 20px; border-radius: 10px; background: white;")

        self.toggle_box.add(self.toggle_indicator)

        # Make it clickable
        self.toggle_button = Button(
            child=self.toggle_box,
            on_clicked=self._on_click
        )
        self.toggle_button.set_style("background: transparent; border: none; padding: 0;")

        # Add spacer to push toggle to the right
        spacer = Label("", h_expand=True)
        self.add(spacer)
        self.add(self.toggle_button)

        # Set initial state
        self._update_appearance()

    def _on_click(self, button):
        self._active = not self._active
        self._update_appearance()
        if self._on_toggle:
            self._on_toggle(self._active)

    def _update_appearance(self):
        if self._active:
            self.toggle_box.set_style_classes(["toggle-active"])
            self.toggle_box.set_style(
                "min-width: 44px; min-height: 24px; border-radius: 12px; padding: 2px; "
                "transition: all 0.2s;"
            )
            self.toggle_indicator.set_style(
                "min-width: 20px; min-height: 20px; border-radius: 10px; "
                "background: white; margin-left: 20px; transition: all 0.2s;"
            )
        else:
            self.toggle_box.set_style_classes(["toggle-inactive"])
            self.toggle_box.set_style(
                "min-width: 44px; min-height: 24px; border-radius: 12px; padding: 2px; "
                "transition: all 0.2s;"
            )
            self.toggle_indicator.set_style(
                "min-width: 20px; min-height: 20px; border-radius: 10px; "
                "background: white; margin-left: 0px; transition: all 0.2s;"
            )

    def set_active(self, active):
        self._active = active
        self._update_appearance()

    def get_active(self):
        return self._active


class QuickMenuButton(QuickMenuItem):
    """A menu item that acts as a button"""
    def __init__(self, title, icon_name=None, on_click=None, **kwargs):
        super().__init__(title, icon_name, **kwargs)

        if on_click:
            # Make the entire item clickable
            button_overlay = Button(
                child=Box(),  # Empty box as child
                on_clicked=on_click
            )
            button_overlay.set_style("background: transparent; border: none; padding: 0; margin: 0;")

        # Add arrow indicator on the right
        arrow = Label("›")
        arrow.set_style("font-size: 18px; opacity: 0.5;")
        spacer = Label("", h_expand=True)
        self.add(spacer)
        self.add(arrow)


class QuickMenuSection(Box):
    """A section in the quick menu with optional title"""
    def __init__(self, title=None, **kwargs):
        super().__init__(
            orientation="v",
            spacing=4,
            name="quick-menu-section",
            **kwargs
        )

        if title:
            title_label = Label(
                title,
                name="section-title"
            )
            title_label.set_style("font-size: 12px; opacity: 0.6; padding: 8px 12px 4px 12px; font-weight: bold;")
            self.add(title_label)

        self.items_box = Box(orientation="v", spacing=2)
        self.add(self.items_box)

    def add_item(self, item):
        self.items_box.add(item)


class QuickMenu(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="quick-menu",
            layer="overlay",  # Changed from 'top' to 'overlay' for better shadow support
            anchor="top right",
            margin="40px 10px 0px 0px",
            exclusivity="none",
            visible=False,
            all_visible=False,
            style_classes=["popup-window"],
            **kwargs,
        )

        # Main container
        self.main_box = Box(
            orientation="v",
            spacing=8,
            name="quick-menu-container"
        )
        # Remove redundant styling since it's handled in stylix.css
        pass

        # Title
        title_box = Box(
            orientation="h",
            spacing=8
        )
        title_box.set_style("padding: 12px;")
        title = Label("Quick Menu")
        title.set_style("font-size: 16px; font-weight: bold;")
        title_box.add(title)

        self.main_box.add(title_box)
        # Add a simple divider line
        divider = Label("")
        divider.set_style("min-height: 1px; background: rgba(255,255,255,0.1); margin: 0px 12px;")
        self.main_box.add(divider)

        # Sections container
        self.sections_container = Box(
            orientation="v",
            spacing=8
        )
        self.sections_container.set_style("padding: 8px 0px;")
        self.main_box.add(self.sections_container)

        self.children = self.main_box
        self.set_size_request(360, -1)

        # Store references to dynamic items
        self.vinyl_toggle = None
        self.sections = {}

    def add_section(self, section_id, title=None):
        """Add a new section to the menu"""
        section = QuickMenuSection(title=title)
        self.sections[section_id] = section
        self.sections_container.add(section)

        # Add separator before section if not the first
        if len(self.sections) > 1:
            separator = Label("")
            separator.set_style("min-height: 1px; background: rgba(255,255,255,0.1); margin: 4px 12px;")
            self.sections_container.add(separator)

        return section

    def setup_audio_section(self, vinyl_service=None):
        """Setup the audio controls section"""
        audio_section = self.add_section("audio", None)  # No section title since it's the only section

        # Vinyl passthrough toggle
        if vinyl_service:
            self.vinyl_toggle = QuickMenuToggle(
                title="Vinyl Passthrough",
                icon_name="folder-music-symbolic",
                active=vinyl_service.active,
                on_toggle=lambda active: self._on_vinyl_toggle(active, vinyl_service)
            )
            audio_section.add_item(self.vinyl_toggle)

            # Store reference to vinyl service
            self.vinyl_service = vinyl_service

    def _on_vinyl_toggle(self, active, vinyl_service):
        """Handle vinyl toggle"""
        logger.info(f"[QuickMenu] Vinyl toggled: {active}")
        vinyl_service.active = active

    def setup_system_section(self):
        """Setup system controls section"""
        # Removed for now - can add system controls later
        pass

    def update_vinyl_state(self, active):
        """Update vinyl toggle state from external source"""
        if self.vinyl_toggle:
            self.vinyl_toggle.set_active(active)


class QuickMenuOpener(Button):
    """Button to open the quick menu"""
    def __init__(self, icon_name="open-menu-symbolic", **kwargs):
        super().__init__(
            name="quick-menu-button",
            child=Image(icon_name=icon_name, icon_size=16),
            on_clicked=self.toggle_menu,
            **kwargs
        )

        self.menu = QuickMenu()
        self.menu_visible = False

    def toggle_menu(self, button=None):
        """Toggle the quick menu visibility"""
        if self.menu_visible:
            logger.info("[QuickMenu] Hiding menu")
            self.menu.set_visible(False)
            self.menu_visible = False
        else:
            logger.info("[QuickMenu] Showing menu")
            self.menu.set_visible(True)
            self.menu.show_all()
            self.menu_visible = True

    def get_menu(self):
        """Get the menu instance for configuration"""
        return self.menu