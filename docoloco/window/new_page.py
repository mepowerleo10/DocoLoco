from typing import cast
from .provider_widget import ProviderWidget

import gi

from ..config import default_config
from ..registry import get_registry

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("new_page"))
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    providers_box = cast(Gtk.Box, Gtk.Template.Child())

    def __init__(self):
        super().__init__()

        for provider in get_registry().providers:
            provider_widget = ProviderWidget(provider)
            self.providers_box.append(provider_widget)

    def filter_item(self, title: str):
        title = title.strip().lower()

        def filter_func(box: Gtk.FlowBoxChild, *args):
            label = box.get_child().get_child().get_last_child()
            return title in label.get_label().lower()

        self.flowbox.set_filter_func(filter_func, None)
