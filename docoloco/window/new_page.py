import re
from ..config import default_config
import gi
from typing import cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit

from ..registry import get_registry


@Gtk.Template(filename=default_config.ui("new_page"))
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    box = cast(Gtk.FlowBox, Gtk.Template.Child("docsets"))

    def __init__(self):
        super().__init__()

        docs = get_registry().entries
        for doc in docs.values():
            box = Gtk.Box(spacing=6)

            icon = Gtk.Image()
            icon.set_from_gicon(doc.icon)
            box.append(icon)

            label = Gtk.Label(label=doc.title)
            box.append(label)

            button = Gtk.Button(
                # label=doc.title,
                action_name="win.change_docset",
                action_target=GLib.Variant.new_string(doc.name),
            )
            button.set_child(box)
            self.box.append(button)
