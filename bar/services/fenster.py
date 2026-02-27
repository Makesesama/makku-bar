"""
Fenster/Sway IPC connection helper.

Provides a singleton I3 connection configured for Fenster's SWAYSOCK.
"""

import os
from fabric.i3 import I3


_connection: I3 | None = None


def get_i3_connection() -> I3:
    """Get the singleton I3 connection, configured for Fenster."""
    global _connection
    if _connection is None:
        swaysock = os.environ.get("SWAYSOCK")
        if swaysock:
            I3.SOCKET_PATH = swaysock
        elif not I3.SOCKET_PATH:
            runtime_dir = os.environ.get(
                "XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"
            )
            fallback = os.path.join(runtime_dir, "fenster.sock")
            if os.path.exists(fallback):
                I3.SOCKET_PATH = fallback
        _connection = I3()
    return _connection
