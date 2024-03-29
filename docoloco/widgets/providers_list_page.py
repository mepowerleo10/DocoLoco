from typing import Callable, Dict, cast

import gi

from docoloco.config import default_config
from docoloco.providers import DocumentationProvider

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, GLib  # noqa: E402


@Gtk.Template(filename=default_config.template("providers_list_page"))
class ProvidersListPage(Adw.NavigationPage):
    __gtype_name__ = "ProvidersListPage"

    providers_list_box = cast(Gtk.ListBox, Gtk.Template.Child())

    def __init__(
        self,
        providers: Dict[str, DocumentationProvider],
        on_activate_row: Callable[[DocumentationProvider], None] = None,
    ):
        super().__init__(title="Providers")
        self.on_activate_callback = on_activate_row

        for id, provider in providers.items():
            action_row = Adw.ActionRow()
            action_row.set_title(provider.name)
            action_row.set_subtitle(id)

            icon = Gtk.Image()
            icon.set_from_gicon(provider.icon)
            action_row.add_prefix(icon)

            button = Gtk.Button()
            # button.connect("mnemonic-activate", self.on_provider_activate)
            action_row.set_activatable_widget(button)
            action_row.connect("activated", self.on_provider_activate, provider.id)

            self.providers_list_box.append(action_row)

    def on_provider_activate(self, _, provider_id):
        self.activate_action("win.focus_locator", GLib.Variant.new_string(f"{provider_id}: "))