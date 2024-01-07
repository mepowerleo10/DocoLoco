from typing import cast

import gi

from docoloco.providers import DocSet, DocumentationProvider

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402


class ManDocsetsView(Gtk.Box):
    def __init__(self, provider: DocumentationProvider):
        super().__init__()
        self.set_hexpand(True)
        self.set_hexpand_set(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.provider = provider
        self.create_status_page()
        provider.query_results_model.connect(
            "items-changed", self._on_query_list_model_items_changed
        )
        self.build_query_results_section()

    def create_status_page(self):
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("system-search-symbolic")
        self.status_page.set_title("Search DocSets")
        self.status_page.set_description("Press Ctrl+P to start searching")
        self.append(self.status_page)

        if self.provider.query_results_model.get_n_items() != 0:
            self.status_page.set_visible(False)

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
        self.append(results_view)

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

    def _on_query_list_model_items_changed(self, model: Gio.ListStore, *args):
        if model.get_n_items() == 0:
            self.status_page.set_visible(True)
        else:
            self.status_page.set_visible(False)

    def filter_or_find(self, value: str):
        value = value.strip().lower()
        self.provider.query(value)

    def get_menu_widget(self) -> Gtk.Widget:
        settings_button = Gtk.Button()
        settings_button.set_icon_name("open-menu-symbolic")

        
        return settings_button
