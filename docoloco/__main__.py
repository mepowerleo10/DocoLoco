import sys
from typing import cast

from docoloco.config import APPLICATION_ID, default_config
from .window.preferences import PreferencesWindow

import gi

from .registry import get_registry
from .window import MainWindow

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gio, GLib  # noqa: E402


class DocoLoco(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APPLICATION_ID)
        GLib.set_application_name("Doco Loco")
        self.connect("activate", self.on_activate)

        actions = [
            ("settings", None, self.show_preferences),
            ("about", None, self.show_about),
        ]

        for action in actions:
            name, shortcut, closure = action
            g_action = Gio.SimpleAction(name=name)
            g_action.connect("activate", closure)
            self.add_action(g_action)

            if shortcut:
                self.set_accels_for_action(f"app.{name}", shortcut)

    def on_activate(self, app):
        self.win = MainWindow(app)
        self.win.set_application(self)
        self.win.present()

    def show_preferences(self, *args):
        preferences_window = PreferencesWindow(parent_window=self.win)
        preferences_window.present()

    def show_about(self, *args):
        builder = Gtk.Builder.new_from_file(filename=default_config.template("about"))
        about = cast(Adw.AboutWindow, builder.get_object("about"))
        about.set_transient_for(self.win)
        about.present()


def main(argv=None) -> int:
    """Start DocoLoco from the command line"""

    if argv is None:
        argv = sys.argv

    get_registry().initialize_providers()

    app = DocoLoco()
    return app.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
