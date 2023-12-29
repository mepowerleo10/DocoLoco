from typing import Callable, cast

import gi

from ..config import default_config
from ..providers.base import DocumentationProvider

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, GLib, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("provider_page"))
class ProviderPage(Adw.NavigationPage):
    __gtype_name__ = "ProviderPage"

    back_btn = cast(Gtk.Button, Gtk.Template.Child())
    title = cast(Gtk.Label, Gtk.Template.Child())
    docsets_box = cast(Gtk.FlowBox, Gtk.Template.Child())

    def __init__(
        self,
        provider: DocumentationProvider,
        on_back_callback: Callable[[None], None] = None,
    ):
        super().__init__(title=provider.name)

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

        self.back_btn.connect("activate", lambda _: print("yes"))

    def on_click_back(self, *args):
        # TODO: Quite frankly do not know why this callback does not work, will check on it tommorow probably...
        pass
