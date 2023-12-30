from typing import cast

import gi

from .config import default_config
from .models import Doc, DocSet
from .registry import get_registry

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.ui("locator"))
class Locator(Adw.Bin):
    __gtype_name__ = "Locator"

    entry = cast(Gtk.Entry, Gtk.Template.Child("locator_entry"))
    results_view: Gtk.ListView = Gtk.Template.Child()
    popover: Gtk.Popover = Gtk.Template.Child()
    docset: DocSet = None
    # search_result_model: SearchResultModel = None
    search_selection_model: Gtk.SingleSelection = None
    docset_btn: Adw.SplitButton = Gtk.Template.Child()
    docset_label: Gtk.Label = Gtk.Template.Child()
    docset_icon: Gtk.Image = Gtk.Template.Child()
    search_box = cast(Gtk.Box, Gtk.Template.Child())

    def __init__(self):
        super().__init__()

        # self.docset = DocSet()
        self.search_result_model = Gio.ListStore(item_type=Doc)

        self.entry.connect("activate", lambda _: self.entry_activated())
        self.entry.connect("changed", lambda _: self.search_changed())

        view_factory = Gtk.SignalListItemFactory()
        view_factory.connect("setup", self.setup_locator_entry)
        view_factory.connect("bind", self.bind_locator_entry)

        self.search_selection_model = Gtk.SingleSelection(
            model=self.search_result_model
        )
        self.search_selection_model.autoselect = False
        self.results_view.set_model(self.search_selection_model)
        self.results_view.set_factory(view_factory)
        self.results_view.connect("activate", lambda _, i: self.entry_activated(pos=i))
        self.popover.set_parent(self.search_box)

        menu = Gio.Menu()
        for name, docset in get_registry().entries.items():
            variant = GLib.Variant.new_string(name)
            menu.append(docset.title, f"win.change_docset({variant})")
        self.docset_btn.set_menu_model(menu)
        self.docset_btn.connect("clicked", self.on_click_docset_btn)

    def setup_locator_entry(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image()
        label = Gtk.Label()

        box.append(icon)
        box.append(label)
        list_item.set_child(box)

    def bind_locator_entry(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = cast(Gtk.Box, list_item.get_child())
        doc = cast(Doc, list_item.get_item())

        icon = cast(Gtk.Image(), box.get_first_child())
        icon.set_from_icon_name(doc.icon_name)
        label = cast(Gtk.Label(), box.get_last_child())
        label.set_label(doc.name)

    def search_changed(self):
        text = self.entry.get_text()

        if not (text or self.popover.is_visible()):
            return

        if self.docset:
            results = self.docset.search(text)
            self.search_result_model.remove_all()
            for result in results:
                self.search_result_model.append(result)

            # self.search_result_model.data = results
            self.search_selection_model.set_selected(False)
            self.popover.set_visible(True)
        else:
            title_variant = GLib.Variant.new_string(text)
            self.activate_action("win.filter_docset", title_variant)

    def entry_activated(self, pos: int = None, doc: Doc = None):
        pos = pos if pos else self.search_selection_model.get_selected()
        doc = self.search_result_model.get_item(pos)

        if not doc:
            return

        variant = GLib.Variant.new_string(doc.url)
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
        else:
            self.docset_label.set_label("DocSet")
            self.docset_icon.set_from_icon_name("accessories-dictionary-symbolic")
            self.entry.set_placeholder_text("Press Ctrl+P to filter docsets")

    def toggle_focus(self, *args):
        if self.popover.get_visible():
            self.popover.set_visible(False)
        else:
            if self.docset:
                self.popover.set_visible(True)

            self.entry.grab_focus()

    def on_click_docset_btn(self, *args):
        if self.docset:
            variant = GLib.Variant.new_string(self.docset.index_file_path.as_uri())
            self.activate_action("win.open_page", variant)
