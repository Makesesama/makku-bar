import logging
from dataclasses import dataclass, field
from typing import Dict, List

from fabric.core.service import Service, Signal, Property
from pywayland.client import Display
from pywayland.protocol.wayland import WlOutput, WlSeat
from ..generated.river_status_unstable_v1 import (
    ZriverStatusManagerV1,
    ZriverOutputStatusV1,
    ZriverSeatStatusV1,
)

logger = logging.getLogger(__name__)


@dataclass
class OutputState:
    id: int
    output: WlOutput
    status: ZriverOutputStatusV1 = None
    focused_tags: List[int] = field(default_factory=list)
    view_tags: List[int] = field(default_factory=list)


class River(Service):
    @Property(bool, "readable", "is-ready", default_value=False)
    def ready(self) -> bool:
        return self._ready

    @Signal
    def ready(self):
        return self.notify("ready")

    @Signal("event", flags="detailed")
    def event(self, event: object): ...

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ready = False
        self.display = None
        self.registry = None
        self.outputs: Dict[int, OutputState] = {}
        self.status_mgr = None
        self.seat = None
        self.seat_status: ZriverSeatStatusV1 = None
        self.ready.emit()

    def on_start(self):
        print("✅ River.on_start called")

        logger.info("[RiverService] Starting River service...")
        self.display = Display()
        self.display.connect()
        self.registry = self.display.get_registry()

        self.registry.dispatcher["global"] = self._on_global
        self.registry.dispatcher["global_remove"] = lambda *_: None

        self.display.roundtrip()

        if self.seat and self.status_mgr:
            self.seat_status = self.status_mgr.get_river_seat_status(self.seat)

        for id, output_state in self.outputs.items():
            status = self.status_mgr.get_river_output_status(output_state.output)
            output_state.status = status
            status.dispatcher["focused_tags"] = self._make_focused_handler(id)
            status.dispatcher["view_tags"] = self._make_view_handler(id)

        self.display.roundtrip()

        self._ready = True
        self.ready.emit()
        logger.info("[RiverService] Ready. Monitoring tags.")

    def on_tick(self):
        # Periodic poll
        self.display.roundtrip()

    def _on_global(self, registry, name, interface, version):
        if interface == "wl_output":
            output = registry.bind(name, WlOutput, version)
            self.outputs[name] = OutputState(id=name, output=output)

        elif interface == "wl_seat":
            self.seat = registry.bind(name, WlSeat, version)

        elif interface == "zriver_status_manager_v1":
            self.status_mgr = registry.bind(name, ZriverStatusManagerV1, version)

    def _make_focused_handler(self, output_id):
        def handler(_, bitfield):
            tags = self._decode_bitfield(bitfield)
            self.outputs[output_id].focused_tags = tags
            logger.debug(f"[RiverService] Output {output_id} focused: {tags}")
            self.emit(f"event::focused_tags::{output_id}", tags)

        return handler

    def _make_view_handler(self, output_id):
        def handler(_, array):
            tags = self._decode_array_bitfields(array)
            self.outputs[output_id].view_tags = tags
            logger.debug(f"[RiverService] Output {output_id} views: {tags}")
            self.emit(f"event::view_tags::{output_id}", tags)

        return handler

    def _decode_bitfield(self, bits: int) -> List[int]:
        return [i for i in range(32) if bits & (1 << i)]

    def _decode_array_bitfields(self, array) -> List[int]:
        tags = set()
        for bits in array:
            tags.update(self._decode_bitfield(bits))
        return sorted(tags)
