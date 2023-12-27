from typing import cast

import gi

from ..config import default_config
from ..registry import get_registry

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, GLib, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("new_page"))
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    flowbox = cast(Gtk.FlowBox, Gtk.Template.Child("docsets"))

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
            self.flowbox.append(button)

    def filter_item(self, title: str):        
        title = title.strip().lower()

        def filter_func(box: Gtk.FlowBoxChild, *args):
            label = box.get_child().get_child().get_last_child()
            return title in label.get_label().lower()

        self.flowbox.set_filter_func(filter_func, None)
