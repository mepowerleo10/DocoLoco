from typing import cast
from ..providers.base import DocumentationProvider

import gi

from ..config import default_config
from ..registry import get_registry
from .provider_page import ProviderPage
from .providers_list_page import ProvidersListPage

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

        providers_list_page = ProvidersListPage(
            get_registry().providers, self.open_provider_page
        )
        self.navigation_view.add(providers_list_page)

    def filter_item(self, title: str):
        page = self.navigation_view.get_visible_page()
        if not isinstance(page, ProviderPage):
            return
        
        title = title.strip().lower()

        def filter_func(box: Gtk.FlowBoxChild, *args):
            label = box.get_child().get_child().get_last_child()
            return title in label.get_label().lower()

        provider_docs_page = cast(ProviderPage, page)
        provider_docs_page.docsets_box.set_filter_func(filter_func, None)

    def open_provider_page(self, provider: DocumentationProvider):
        provider_docs_page = ProviderPage(provider, lambda _: self.navigation_view.pop())

        self.navigation_view.push(provider_docs_page)
