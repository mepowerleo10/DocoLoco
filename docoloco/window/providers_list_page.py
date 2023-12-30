from typing import Callable, Dict, List, cast

import gi

from ..config import default_config
from ..providers.base import DocumentationProvider

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("providers_list_page"))
class ProvidersListPage(Adw.NavigationPage):
    __gtype_name__ = "ProvidersListPage"

    providers_list_box = cast(Gtk.ListBox, Gtk.Template.Child())

    def __init__(
        self,
        providers: Dict[str, DocumentationProvider],
        on_activate_row: Callable[[DocumentationProvider], None],
    ):
        super().__init__(title="Providers")
        self.on_activate_callback = on_activate_row

        for name, provider in providers.items():
            action_row = Adw.ActionRow()
            action_row.set_title(name)
            action_row.set_icon_name("accessories-dictionary-symbolic")

            button = Gtk.Button()
            action_row.set_activatable_widget(button)

            icon = Gtk.Image.new_from_icon_name(("go-next-symbolic"))
            action_row.add_suffix(icon)
            self.providers_list_box.append(action_row)

            action_row.connect("activated", self.on_activated, provider)

    def on_activated(self, action_row, provider):
        self.on_activate_callback(provider)
