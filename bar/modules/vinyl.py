from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.eventbox import EventBox
from fabric.widgets.overlay import Overlay
from fabric.core.service import Property
import subprocess


class VinylButton(Box):
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
        super().__init__(**kwargs)

        # Initialize properties
        self._active = False
        self._active_command = active_command
        self._inactive_command = inactive_command

        # Set up the icon
        self.icon = Label(
            label="",  # CD icon
            name="vinyl-icon",
            style="",
        )

        # Set up event box to handle clicks
        self.event_box = EventBox(
            events="button-press",
            child=Overlay(
                child=self.icon,
            ),
            name="vinyl-button",
        )

        # Connect click event
        self.event_box.connect("button-press-event", self._on_clicked)

        # Add to parent box
        self.add(self.event_box)

        # Initialize appearance
        self._update_appearance()

    def _update_appearance(self):
        """Update CSS class based on active state"""
        if self._active:
            self.add_style_class("active")
        else:
            self.remove_style_class("active")

    def _on_clicked(self, _, event):
        """Handle button click event"""
        if event.button == 1:  # Left click
            # Toggle active state
            self.active = not self.active
        return True

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
