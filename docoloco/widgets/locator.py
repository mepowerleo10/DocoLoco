from typing import cast

import gi

from ..config import default_config
from ..models import Doc, DocSet, Section
from ..search import SearchProvider, SearchResult

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.template("locator"))
class Locator(Adw.Bin):
    __gtype_name__ = "Locator"

    entry = cast(Gtk.Entry, Gtk.Template.Child())
    results_view: Gtk.ListView = Gtk.Template.Child()
    popover: Gtk.Popover = Gtk.Template.Child()
    search_selection_model: Gtk.SingleSelection = None
    search_box = cast(Gtk.Box, Gtk.Template.Child())

    docset_btn = cast(Gtk.Button, Gtk.Template.Child())
    section_btn = cast(Adw.SplitButton, Gtk.Template.Child())

    def __init__(self):
        super().__init__()

        self.search_provider = SearchProvider()

        self.search_result_model.connect(
            "items-changed", self.on_search_result_items_changed
        )

        self.entry.connect("activate", self.toggle_focus)
        self.entry.connect("changed", self.search_changed)
        self.entry.connect("icon-press", self.on_icon_pressed)

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
        self.popover.set_parent(self.entry)

    def setup_search_result(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        icon = Gtk.Image()
        label = Gtk.Label()

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_box.append(icon)
        title_box.append(label)
        title_box.set_hexpand(True)
        title_box.set_hexpand_set(True)
        box.append(title_box)

        arrow = Gtk.Image()
        arrow.set_from_icon_name("go-next-symbolic")
        box.append(arrow)
        box.add_css_class("result-line")
        list_item.set_child(box)

    def bind_search_result(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = cast(Gtk.Box, list_item.get_child())
        title_box = cast(Gtk.Box, box.get_first_child())
        result = cast(SearchResult, list_item.get_item())

        icon = cast(Gtk.Image, title_box.get_first_child())
        if isinstance(result.icon, str):
            icon.set_from_icon_name(result.icon)
        else:
            icon.set_from_gicon(result.icon)

        label = cast(Gtk.Label, title_box.get_last_child())
        label.set_label(result.title)

        arrow = cast(Gtk.Image, box.get_last_child())
        if result.has_child:
            arrow.show()
        else:
            arrow.hide()

    def search_changed(self, *_):
        text: str = self.entry.get_text()
        text = text.strip().lower()
        self.search_provider.search(text)

    def entry_activated(self, pos: int = None, result: Doc = None):
        pos = pos if pos else self.search_selection_model.get_selected()
        result: SearchResult = self.search_result_model.get_item(pos)

        if result:
            action_name, action_args = result.action_name, result.action_args
            self.activate_action(action_name, action_args)
            self.entry.grab_focus()

    @property
    def docset(self) -> DocSet:
        return self.search_provider.docset

    @docset.setter
    def docset(self, docset: DocSet):
        self.search_provider.docset = docset

        if docset:
            self.entry.set_placeholder_text(
                "Press Ctrl+P to search sections and symbols"
            )
            self.docset_btn.set_visible(True)
            icon = cast(Gtk.Image, self.docset_btn.get_child())
            icon.set_from_gicon(docset.icon)
            self.docset_btn.set_tooltip_text(docset.title)
        else:
            self.entry.set_placeholder_text("Press Ctrl+P to filter docsets")
            self.docset_btn.set_visible(False)

    @property
    def section(self) -> Section:
        return self.search_provider.section

    @section.setter
    def section(self, section: Section):
        self.search_provider.section = section

        if section:
            menu = Gio.Menu()
            # menu.append("All", f"win.change_section({GLib.Variant.new_string('All')})")
            for name, count in self.docset.symbol_counts.items():
                menu.append(
                    name, f"win.change_section({GLib.Variant.new_string(name)})"
                )

            self.section_btn.set_label(section.title)
            self.section_btn.set_visible(True)
            self.section_btn.set_menu_model(menu)
        else:
            self.section_btn.set_visible(False)

    def toggle_focus(self, *args):
        if not self.entry.get_focus_child():
            self.entry.grab_focus()
        
        self.on_search_result_items_changed()

    def on_search_result_items_changed(self, *args):
        if self.search_result_model.get_n_items() > 0 and self.entry.get_focus_child():
            self.popover.set_visible(True)

    def change_section(self, name: str):
        self.section = (
            None if "All" in name else Section(name, self.docset.symbol_counts[name])
        )

        self.search_changed()

    def on_icon_pressed(self, entry, icon_position: Gtk.EntryIconPosition, *data):
        if icon_position == Gtk.EntryIconPosition.SECONDARY:
            text = cast(str, self.entry.get_text())
            if text.strip():
                self.entry.set_text("")
            else:
                self.clear_filters()

    def clear_filters(self, *_):
        if self.section:
            self.section = None
        elif self.docset:
            self.docset = None

    @property
    def search_result_model(self) -> Gio.ListStore:
        return self.search_provider.result
