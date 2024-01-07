import sys
from .config import APPLICATION_ID

import gi

from .registry import get_registry
from .window import MainWindow

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib  # noqa: E402


class DocoLoco(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APPLICATION_ID)
        GLib.set_application_name("Doco Loco")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(app)
        self.win.set_application(self)
        self.win.present()


def main(argv=None) -> int:
    """Start DocoLoco from the command line"""

    if argv is None:
        argv = sys.argv

    get_registry().initialize_providers()

    app = DocoLoco()
    return app.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
