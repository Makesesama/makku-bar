from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.core.service import Property
import subprocess


class VinylButton(Button):
    @Property(bool, "read-write", default_value=False)
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        # Update appearance based on state
        self._update_appearance()

        # Execute shell command based on new state
        if self._active:
            self._execute_active_command()
        else:
            self._execute_inactive_command()

    def __init__(
        self,
        active_command=[
            "pw-link alsa_input.pci-0000_12_00.6.analog-stereo:capture_FL alsa_output.usb-BEHRINGER_UMC1820_A71E9E3E-00.multichannel-output:playback_AUX0",
            "pw-link alsa_input.pci-0000_12_00.6.analog-stereo:capture_FR alsa_output.usb-BEHRINGER_UMC1820_A71E9E3E-00.multichannel-output:playback_AUX1",
        ],
        inactive_command=[
            "pw-link -d alsa_input.pci-0000_12_00.6.analog-stereo:capture_FL alsa_output.usb-BEHRINGER_UMC1820_A71E9E3E-00.multichannel-output:playback_AUX0",
            "pw-link -d alsa_input.pci-0000_12_00.6.analog-stereo:capture_FR alsa_output.usb-BEHRINGER_UMC1820_A71E9E3E-00.multichannel-output:playback_AUX1 ",
        ],
        **kwargs,
    ):
        # Initialize properties
        self._active = False
        self._active_command = active_command
        self._inactive_command = inactive_command

        # Set up the icon using GTK icon
        self.icon = Image(
            icon_name="folder-music-symbolic",
            icon_size=16,
            name="vinyl-icon",
        )

        # Initialize the Button with the icon as child
        super().__init__(
            name="vinyl-button",
            child=self.icon,
            on_clicked=self._on_clicked,
            **kwargs,
        )

        # Initialize appearance
        self._update_appearance()

    def _update_appearance(self):
        """Update CSS class based on active state"""
        if self._active:
            self.add_style_class("active")
        else:
            self.remove_style_class("active")

    def _on_clicked(self, button=None):
        """Handle button click event"""
        # Toggle active state
        self.active = not self.active

    def _execute_active_command(self):
        """Execute shell command when button is activated"""
        try:
            for cmd in self._active_command:
                subprocess.Popen(cmd, shell=True)
        except Exception as e:
            print(f"Error executing active command: {e}")

    def _execute_inactive_command(self):
        """Execute shell command when button is deactivated"""
        try:
            for cmd in self._inactive_command:
                subprocess.Popen(cmd, shell=True)
        except Exception as e:
            print(f"Error executing inactive command: {e}")
