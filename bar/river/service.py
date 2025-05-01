import os
import threading
import time
from loguru import logger
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set

from fabric.core.service import Service, Signal, Property
from fabric.utils.helpers import idle_add

# Import pywayland components - ensure these imports are correct
from pywayland.client import Display
from pywayland.protocol.wayland import WlOutput, WlRegistry, WlSeat
from ..generated.river_status_unstable_v1 import ZriverStatusManagerV1


@dataclass
class OutputInfo:
    """Information about a River output"""

    name: int
    output: WlOutput
    status: Any = None  # ZriverOutputStatusV1
    tags_view: List[int] = field(default_factory=list)
    tags_focused: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class RiverEvent:
    """Event data from River compositor"""

    name: str
    data: List[Any]
    output_id: Optional[int] = None


class River(Service):
    """Connection to River Wayland compositor via river-status protocol"""

    @Property(bool, "readable", "is-ready", default_value=False)
    def ready(self) -> bool:
        return self._ready

    @Signal
    def ready(self):
        return self.notify("ready")

    @Signal("event", flags="detailed")
    def event(self, event: object): ...

    def __init__(self, **kwargs):
        """Initialize the River service"""
        super().__init__(**kwargs)
        self._ready = False
        self.outputs: Dict[int, OutputInfo] = {}
        self.river_status_mgr = None
        self.seat = None
        self.seat_status = None

        # Start the connection in a separate thread
        self.river_thread = threading.Thread(
            target=self._river_connection_task, daemon=True, name="river-status-service"
        )
        self.river_thread.start()

    def _river_connection_task(self):
        """Main thread that connects to River and listens for events"""
        try:
            # Create a new display connection - THIS IS WHERE THE ERROR OCCURS
            logger.info("[RiverService] Starting connection to River")

            # Let's add some more diagnostic info to help troubleshoot
            logger.debug(
                f"[RiverService] XDG_RUNTIME_DIR={os.environ.get('XDG_RUNTIME_DIR', 'Not set')}"
            )
            logger.debug(
                f"[RiverService] WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY', 'Not set')}"
            )

            # Create the display connection
            # with Display() as display:
            #     registry = display.get_registry()
            #     logger.debug("[RiverService] Registry obtained")

            # Discover globals

            display = Display("wayland-1")
            display.connect()
            logger.debug("[RiverService] Display connection created")

            # Get the registry
            registry = display.get_registry()
            logger.debug("[RiverService] Registry obtained")

            # Create state object to hold our data
            state = {
                "display": display,
                "registry": registry,
                "outputs": {},
                "river_status_mgr": None,
                "seat": None,
                "seat_status": None,
            }

            # Set up registry handlers - using more direct approach like your example
            def handle_global(registry, name, iface, version):
                logger.debug(
                    f"[RiverService] Global: {iface} (v{version}, name={name})"
                )
                if iface == "zriver_status_manager_v1":
                    state["river_status_mgr"] = registry.bind(
                        name, ZriverStatusManagerV1, version
                    )
                    logger.info("[RiverService] Found river status manager")
                elif iface == "wl_output":
                    output = registry.bind(name, WlOutput, version)
                    state["outputs"][name] = OutputInfo(name=name, output=output)
                    logger.info(f"[RiverService] Found output {name}")
                elif iface == "wl_seat":
                    state["seat"] = registry.bind(name, WlSeat, version)
                    logger.info("[RiverService] Found seat")

            def handle_global_remove(registry, name):
                if name in state["outputs"]:
                    logger.info(f"[RiverService] Output {name} removed")
                    del state["outputs"][name]
                    idle_add(
                        lambda: self.emit(
                            "event::output_removed",
                            RiverEvent("output_removed", [name]),
                        )
                    )

            # Set up the dispatchers
            registry.dispatcher["global"] = handle_global
            registry.dispatcher["global_remove"] = handle_global_remove

            # Discover globals
            logger.debug("[RiverService] Performing initial roundtrip")
            display.roundtrip()

            # Check if we found the river status manager
            if not state["river_status_mgr"]:
                logger.error("[RiverService] River status manager not found")
                return

            # Create view tags and focused tags handlers
            def make_view_tags_handler(output_id):
                def handler(_, tags):
                    decoded = self._decode_bitfields(tags)
                    state["outputs"][output_id].tags_view = decoded
                    logger.debug(
                        f"[RiverService] Output {output_id} view tags: {decoded}"
                    )
                    idle_add(lambda: self._emit_view_tags(output_id, decoded))

                return handler

            def make_focused_tags_handler(output_id):
                def handler(_, tags):
                    decoded = self._decode_bitfields(tags)
                    state["outputs"][output_id].tags_focused = decoded
                    logger.debug(
                        f"[RiverService] Output {output_id} focused tags: {decoded}"
                    )
                    idle_add(lambda: self._emit_focused_tags(output_id, decoded))

                return handler

            # Bind output status listeners
            for name, info in list(state["outputs"].items()):
                status = state["river_status_mgr"].get_river_output_status(info.output)
                status.dispatcher["view_tags"] = make_view_tags_handler(name)
                status.dispatcher["focused_tags"] = make_focused_tags_handler(name)
                info.status = status
                logger.info(f"[RiverService] Set up status for output {name}")

            # Initial data fetch
            logger.debug("[RiverService] Performing second roundtrip")
            display.roundtrip()

            # Update our outputs dictionary
            self.outputs.update(state["outputs"])
            self.river_status_mgr = state["river_status_mgr"]
            self.seat = state["seat"]
            self.seat_status = state.get("seat_status")

            # Mark service as ready
            idle_add(self._set_ready)

            # Main event loop
            logger.info("[RiverService] Entering main event loop")
            while True:
                display.roundtrip()
                time.sleep(0.01)  # Small sleep to prevent CPU spinning

        except Exception as e:
            logger.error(f"[RiverService] Error in River connection: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _set_ready(self):
        """Set the service as ready (called on main thread via idle_add)"""
        self._ready = True
        logger.info("[RiverService] Service ready")
        self.ready.emit()
        return False  # Don't repeat

    def _emit_view_tags(self, output_id, tags):
        """Emit view_tags events (called on main thread)"""
        event = RiverEvent("view_tags", tags, output_id)
        self.emit("event::view_tags", event)
        self.emit(f"event::view_tags::{output_id}", tags)
        return False  # Don't repeat

    def _emit_focused_tags(self, output_id, tags):
        """Emit focused_tags events (called on main thread)"""
        event = RiverEvent("focused_tags", tags, output_id)
        self.emit("event::focused_tags", event)
        self.emit(f"event::focused_tags::{output_id}", tags)
        return False  # Don't repeat

    @staticmethod
    def _decode_bitfields(bitfields) -> List[int]:
        """Decode River's tag bitfields into a list of tag indices"""
        tags: Set[int] = set()

        # Ensure we have an iterable
        if not hasattr(bitfields, "__iter__"):
            bitfields = [bitfields]

        for bits in bitfields:
            for i in range(32):
                if bits & (1 << i):
                    tags.add(i)

        return sorted(tags)

    def run_command(self, command, *args):
        """Run a riverctl command"""
        import subprocess

        cmd = ["riverctl", command] + [str(arg) for arg in args]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"[RiverService] Ran command: {' '.join(cmd)}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(
                f"[RiverService] Command failed: {' '.join(cmd)}, error: {e.stderr}"
            )
            return None

    def toggle_focused_tag(self, tag):
        """Toggle a tag in the focused tags"""
        tag_mask = 1 << int(tag)
        self.run_command("toggle-focused-tags", str(tag_mask))
