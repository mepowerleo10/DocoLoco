from typing import Callable, cast

import gi

from ..config import default_config
from ..models.base import DocSet
from ..providers.base import DocumentationProvider

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("provider_page"))
class ProviderPage(Adw.NavigationPage):
    __gtype_name__ = "ProviderPage"

    back_btn = cast(Gtk.Button, Gtk.Template.Child())
    title = cast(Gtk.Label, Gtk.Template.Child())
    docsets_box = cast(Gtk.FlowBox, Gtk.Template.Child())
    contents_box = cast(Gtk.Box, Gtk.Template.Child())

    def __init__(
        self,
        provider: DocumentationProvider,
        on_back_callback: Callable[[None], None] = None,
    ):
        super().__init__(title=provider.name)

        self.provider = provider
        self.title.set_label(provider.name)

        if provider.type == DocumentationProvider.Type.PRELOADED:
            self.build_docset_buttons(provider)
        else:
            self.contents_box.remove(self.docsets_box)

            self.create_status_page()

            provider.query_results_model.connect(
                "items-changed", self._on_query_list_model_items_changed
            )

            self.build_query_results_section()

        self.back_btn.connect("activate", self.on_click_back)
        self.back_btn.connect(
            "clicked", self.on_click_back, on_back_callback
        )  # 'activate' does not work...

    def create_status_page(self):
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("system-search-symbolic")
        self.status_page.set_title("Search DocSets")
        self.status_page.set_description("Press Ctrl+P to start searching")
        self.contents_box.append(self.status_page)

        if self.provider.query_results_model.get_n_items() != 0:
            self.status_page.set_visible(False)

    def build_docset_buttons(self, provider: DocumentationProvider):
        for doc in provider.docs.values():
            box = Gtk.Box(spacing=6)

            icon = Gtk.Image()
            icon.set_from_gicon(doc.icon)
            box.append(icon)

            label = Gtk.Label(label=doc.title)
            box.append(label)

            action_params = GLib.Variant("(ssi)", (provider.name, doc.name, 0))
            button = Gtk.Button(
                # label=doc.title,
                action_name="win.change_docset",
                action_target=action_params,
            )
            button.set_child(box)
            self.docsets_box.append(button)

    def build_query_results_section(self):
        view_factory = Gtk.SignalListItemFactory()
        view_factory.connect("setup", self._setup_query_result)
        view_factory.connect("bind", self._bind_query_result)

        search_selection_model = Gtk.SingleSelection(
            model=self.provider.query_results_model
        )
        search_selection_model.autoselect = False

        results_view = Gtk.ListView()
        results_view.set_show_separators(True)
        results_view.set_model(search_selection_model)
        results_view.set_factory(view_factory)
        results_view.connect("activate", self._on_result_activate)
        self.contents_box.append(results_view)

    def _setup_query_result(self, factory, obj):
        list_item = cast(Gtk.ListItem, obj)
        box = Gtk.Box()
        label = Gtk.Label()

        box.append(label)
        box.get_style_context().add_class("result-line")
        list_item.set_child(box)

    def _bind_query_result(self, factory, obj):
        list_item = cast(Gtk.ListItem, obj)
        box = cast(Gtk.Box, list_item.get_child())
        label = cast(Gtk.Label, box.get_first_child())

        docset = cast(DocSet, list_item.get_item())
        label.set_label(docset.description)

    def _on_result_activate(self, list_view, pos: int):
        doc: DocSet = self.provider.query_results_model.get_item(pos)
        action_params = GLib.Variant("(ssi)", (self.provider.name, doc.name, pos))
        self.activate_action("win.change_docset", action_params)

    def on_click_back(self, button, callback: Callable[[None], None] = None):
        if callback:
            callback()

    def _on_query_list_model_items_changed(self, model: Gio.ListStore, *args):
        if model.get_n_items() == 0:
            self.status_page.set_visible(True)
        else:
            self.status_page.set_visible(False)

    def filter_or_find(self, value: str, filter_func: Callable[[Gtk.Widget], bool]):
        if self.provider.type == DocumentationProvider.Type.QUERYABLE:
            self.provider.query(value)
        else:
            self.docsets_box.set_filter_func(filter_func)
