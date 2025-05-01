#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from pywayland.client import Display
from pywayland.protocol.wayland import WlOutput, WlRegistry, WlSeat
from .generated.river_status_unstable_v1 import (
    ZriverStatusManagerV1,
    ZriverOutputStatusV1,
)


@dataclass
class OutputInfo:
    name: int
    output: WlOutput
    status: ZriverOutputStatusV1
    tags_view: list[int] = field(default_factory=list)
    tags_focused: list[int] = field(default_factory=list)


@dataclass
class State:
    display: Display
    registry: WlRegistry
    outputs: dict[int, OutputInfo] = field(default_factory=dict)
    river_status_mgr: ZriverStatusManagerV1 | None = None
    seat: WlSeat | None = None
    seat_status: ZriverSeatStatusV1 | None = None


def decode_bitfields(bitfields: list[int] | int) -> list[int]:
    tags = set()
    if isinstance(bitfields, int):
        bitfields = [bitfields]
    for bits in bitfields:
        for i in range(32):
            if bits & (1 << i):
                tags.add(i)
    return sorted(tags)


def handle_global(
    state: State, registry: WlRegistry, name: int, iface: str, version: int
) -> None:
    if iface == "zriver_status_manager_v1":
        state.river_status_mgr = registry.bind(name, ZriverStatusManagerV1, version)

    elif iface == "wl_output":
        output = registry.bind(name, WlOutput, version)
        state.outputs[name] = OutputInfo(name=name, output=output, status=None)
    elif iface == "wl_seat":
        seat = registry.bind(name, WlSeat, version)
        state.seat = seat


def handle_global_remove(state: State, registry: WlRegistry, name: int) -> None:
    if name in state.outputs:
        print(f"Output {name} removed.")
        del state.outputs[name]


def make_view_tags_handler(state: State, name: int) -> Callable:
    def handler(self, tags: list[int]) -> None:
        decoded = decode_bitfields(tags)
        state.outputs[name].tags_view = decoded
        print(f"[Output {name}] View tags: {decoded}")

    return handler


def make_focused_tags_handler(state: State, name: int) -> Callable:
    def handler(self, tags: int) -> None:
        decoded = decode_bitfields(tags)
        state.outputs[name].tags_focused = decoded
        print(f"[Output {name}] Focused tags: {decoded}")

    return handler


def main() -> None:
    with Display() as display:
        registry = display.get_registry()
        state = State(display=display, registry=registry)

        registry.dispatcher["global"] = lambda reg, name, iface, ver: handle_global(
            state, reg, name, iface, ver
        )
        registry.dispatcher["global_remove"] = lambda reg, name: handle_global_remove(
            state, reg, name
        )

        # Discover globals
        display.roundtrip()

        if not state.river_status_mgr:
            print("❌ River status manager not found.")
            return

        # Bind output status listeners
        for name, info in state.outputs.items():
            status = state.river_status_mgr.get_river_output_status(info.output)
            status.dispatcher["view_tags"] = make_view_tags_handler(state, name)
            status.dispatcher["focused_tags"] = make_focused_tags_handler(state, name)
            info.status = status

        if state.seat:
            state.seat_status = state.river_status_mgr.get_river_seat_status(state.seat)
            print("✅ Bound seat status")

        # Initial data
        display.roundtrip()

        print("🟢 Listening for tag changes. Press Ctrl+C to exit.")
        while True:
            display.roundtrip()


if __name__ == "__main__":
    main()
