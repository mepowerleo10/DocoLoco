from typing import cast

import gi

from docoloco.config import default_config
from docoloco.registry import get_registry

from .providers_list_page import ProvidersListPage

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.template("new_page"))
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    navigation_view = cast(Adw.NavigationView, Gtk.Template.Child())

    def __init__(self):
        super().__init__()

        providers_list_page = ProvidersListPage(providers=get_registry().providers)
        self.navigation_view.add(providers_list_page)

    def filter_item(self, title: str):
        pass
