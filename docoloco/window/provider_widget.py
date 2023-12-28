from typing import cast

import gi

from ..config import default_config
from ..providers.base import DocumentationProvider

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, GLib, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("provider"))
class ProviderWidget(Adw.Bin):
    __gtype_name__ = "ProviderWidget"

    title = cast(Gtk.Label, Gtk.Template.Child())
    docsets_box = cast(Gtk.FlowBox, Gtk.Template.Child())

    def __init__(self, provider: DocumentationProvider):
        super().__init__()

        self.provider = provider
        self.title.set_label(provider.name)

        for doc in provider.docs.values():
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
            self.docsets_box.append(button)
