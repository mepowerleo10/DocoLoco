from typing import Callable, cast

import gi

from docoloco.config import default_config
from docoloco.providers import DocumentationProvider, FilterableProviderView

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.template("provider_page"))
class ProviderPage(Adw.NavigationPage):
    __gtype_name__ = "ProviderPage"

    back_btn = cast(Gtk.Button, Gtk.Template.Child())
    title = cast(Gtk.Label, Gtk.Template.Child())
    contents_box = cast(Gtk.Box, Gtk.Template.Child())

    def __init__(
        self,
        provider: DocumentationProvider,
        on_back_callback: Callable[[None], None] = None,
    ):
        super().__init__(title=provider.name)

        self.provider = provider
        self.title.set_label(provider.name)

        self.view = provider.get_view()
        self.contents_box.append(self.view)

        self.back_btn.connect("activate", self.on_click_back)
        self.back_btn.connect(
            "clicked", self.on_click_back, on_back_callback
        )  # 'activate' does not work...

    def on_click_back(self, button, callback: Callable[[None], None] = None):
        if callback:
            callback()

    def filter_or_find(self, value: str, filter_func: Callable[[Gtk.Widget], bool]):
        filterable_view = cast(FilterableProviderView, self.view)
        filterable_view.filter_or_find(value)
