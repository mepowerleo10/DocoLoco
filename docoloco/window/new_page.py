from typing import cast
from ..providers.base import DocumentationProvider

import gi

from ..config import default_config
from ..registry import get_registry
from .provider_widget import ProviderWidget
from .providers_list_widget import ProvidersListWidget

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, GObject  # noqa: E402


@Gtk.Template(filename=default_config.ui("new_page"))
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    navigation_view = cast(Adw.NavigationView, Gtk.Template.Child())
    title = GObject.Property(
        type=str, flags=GObject.ParamFlags.READWRITE
    )

    def __init__(self):
        super().__init__()

        page = Adw.NavigationPage()

        providers_list = ProvidersListWidget(
            get_registry().providers, self.open_provider_page
        )
        page.set_child(providers_list)
        page.set_title("Choose Provider")
        page.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)
        self.navigation_view.add(page)

    def filter_item(self, title: str):
        title = title.strip().lower()

        def filter_func(box: Gtk.FlowBoxChild, *args):
            label = box.get_child().get_child().get_last_child()
            return title in label.get_label().lower()

        self.flowbox.set_filter_func(filter_func, None)

    def open_provider_page(self, provider: DocumentationProvider):
        page = Adw.NavigationPage()
        provider_docs = ProviderWidget(provider, lambda _: self.navigation_view.pop())
        page.set_title(provider.name)
        page.set_child(provider_docs)
        page.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)

        self.navigation_view.push(page)
