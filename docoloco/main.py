import sys

import gi

from .registry import get_registry
from .window import ApplicationWindow

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib  # noqa: E402


class DocoLoco(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.mepowerleo10.DocoLoco")
        GLib.set_application_name("Doco Loco")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = ApplicationWindow(app)
        self.win.set_application(self)
        self.win.present()


def main(argv=None) -> int:
    """Start DocoLoco from the command line"""

    if argv is None:
        argv = sys.argv

    get_registry().initialize_providers()

    app = DocoLoco()
    return app.run(argv)
