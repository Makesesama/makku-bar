from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.box import Box
from fabric.widgets.label import Label


class FuzzyWindowFinder(Window):
    def __init__(
        self,
        monitor: int = 1,
    ):
        super().__init__(
            name="finder",
            layer="overlay",
            anchor="center",
            margin="0px 0px -2px 0px",
            exclusivity="auto",
            visible=False,
            all_visible=False,
            monitor=monitor,
        )

        self.children = Box(
            name="list-windows", children=[Label(name="one-window", markup="Hallo lol")]
        )
