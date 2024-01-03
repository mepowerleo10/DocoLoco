from enum import Enum
from typing import Callable, cast
from .models.base import Section

import gi

from .config import default_config
from .models import Doc, DocSet

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402


class FilterType(Enum):
    DOCSET = 1
    SECTION = 2
    DOC = 3


class SearchResult(GObject.Object):
    __gtype_name__ = "SearchResult"

    def __init__(
        self,
        type: FilterType,
        title: str,
        icon_name: str,
        has_child: bool,
        on_select: Callable,
        callback_args,
    ) -> None:
        super().__init__()

        self.type = type
        self.title = title
        self.icon_name = icon_name
        self.has_child = has_child
        self.on_select = on_select
        self.callback_args = callback_args


@Gtk.Template(filename=default_config.ui("locator"))
class Locator(Adw.Bin):
    __gtype_name__ = "Locator"

    entry = cast(Gtk.Entry, Gtk.Template.Child("locator_entry"))
    results_view: Gtk.ListView = Gtk.Template.Child()
    popover: Gtk.Popover = Gtk.Template.Child()
    search_selection_model: Gtk.SingleSelection = None
    docset_btn: Gtk.Button = Gtk.Template.Child()
    docset_label: Gtk.Label = Gtk.Template.Child()
    docset_icon: Gtk.Image = Gtk.Template.Child()
    section_btn: Adw.SplitButton = Gtk.Template.Child()
    search_box = cast(Gtk.Box, Gtk.Template.Child())

    # docset: DocSet = None

    def __init__(self, docset: DocSet = None):
        super().__init__()

        self.docset = docset
        self.section: Section = None

        self.search_result_model = Gio.ListStore(item_type=SearchResult)

        self.entry.connect("activate", lambda _: self.toggle_focus())
        self.entry.connect("changed", lambda _: self.search_changed())

        view_factory = Gtk.SignalListItemFactory()
        view_factory.connect("setup", self.setup_search_result)
        view_factory.connect("bind", self.bind_search_result)

        self.search_selection_model = Gtk.SingleSelection(
            model=self.search_result_model
        )
        self.search_selection_model.autoselect = False
        self.results_view.set_model(self.search_selection_model)
        self.results_view.set_factory(view_factory)
        self.results_view.connect("activate", lambda _, i: self.entry_activated(pos=i))
        self.popover.set_parent(self.search_box)

    def setup_search_result(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image()
        label = Gtk.Label()

        box.append(icon)
        box.append(label)
        list_item.set_child(box)

    def bind_search_result(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = cast(Gtk.Box, list_item.get_child())
        result = cast(SearchResult, list_item.get_item())

        icon = cast(Gtk.Image(), box.get_first_child())
        icon.set_from_icon_name(result.icon_name)
        label = cast(Gtk.Label(), box.get_last_child())
        label.set_label(result.title)

    def search_changed(self):
        text: str = self.entry.get_text()

        if not (text or self.popover.is_visible()):
            return

        text = text.strip().lower()
        self.search_result_model.remove_all()
        results = (
            self.docset.search(text, self.section.title)
            if self.section
            else self.docset.search(text)
        )
        for item in results:
            self.search_result_model.append(
                SearchResult(
                    FilterType.DOC,
                    item.name,
                    item.icon_name,
                    False,
                    on_select=self.on_select_doc,
                    callback_args={"url": item.url},
                )
            )

        self.popover.set_visible(True)

    def entry_activated(self, pos: int = None, result: Doc = None):
        pos = pos if pos else self.search_selection_model.get_selected()
        result: SearchResult = self.search_result_model.get_item(pos)

        if result:
            result.on_select(**result.callback_args)

    def on_select_doc(self, url: str):
        variant = GLib.Variant.new_string(url)
        self.activate_action("win.open_page", variant)
        self.toggle_focus()

    def set_docset(self, docset: DocSet):
        self.docset = docset

        if docset:
            self.docset_label.set_label(docset.title)
            self.docset_icon.set_from_gicon(docset.icon)
            self.entry.set_placeholder_text(
                "Press Ctrl+P to search sections and symbols"
            )

            menu = Gio.Menu()
            for name, count in self.docset.symbol_counts.items():
                menu.append(name, f"win.change_filter({GLib.Variant.new_string(name)})")

            self.section_btn.set_menu_model(menu)
        else:
            self.docset_label.set_label("DocSet")
            self.docset_icon.set_from_icon_name("accessories-dictionary-symbolic")
            self.entry.set_placeholder_text("Press Ctrl+P to filter docsets")

    def toggle_focus(self, *args):
        self.popover.set_visible(not self.popover.get_visible())
        self.entry.grab_focus()

    def on_click_docset_btn(self, *args):
        if self.docset:
            variant = GLib.Variant.new_string(self.docset.index_file_path.as_uri())
            self.activate_action("win.open_page", variant)

    def change_filter(self, name: str):
        icon: Gtk.Image = self.section_btn.get_child().get_first_child()
        label: Gtk.Label = self.section_btn.get_child().get_last_child()

        self.section = Section(name, self.docset.symbol_counts[name])
        icon.set_from_icon_name(self.section.icon_name)
        label.set_label(self.section.title)
