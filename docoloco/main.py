import sys
import gi

from .window import Window

from .registry import initialize_providers, registered_providers

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import GLib, Adw  # noqa: E402


class DocoLoco(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.mepowerleo10.DocoLoco")
        GLib.set_application_name("Doco Loco")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        self.win = Window(app, registered_providers[0].docs)
        self.win.set_application(self)
        self.win.present()


def main(argv=None) -> int:
    """Start DocoLoco from the command line"""

    if argv is None:
        argv = sys.argv

    initialize_providers()

    app = DocoLoco()
    return app.run(argv)
