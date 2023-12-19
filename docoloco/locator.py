from typing import cast

from .models import DocSet, SearchResultModel, Doc
from .config import default_config
from .registry import get_registry
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject


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

    def __init__(self):
        super().__init__()

        # self.docset = DocSet()
        self.search_result_model = Gio.ListStore()

        self.entry.connect("activate", lambda _: self.entry_activated())
        self.entry.connect("changed", lambda _: self.search_changed())

        view_factory = Gtk.SignalListItemFactory()
        view_factory.connect("setup", self.setup_locator_entry)
        view_factory.connect("bind", self.bind_locator_entry)

        self.search_selection_model = Gtk.SingleSelection(model=self.search_result_model)
        self.search_selection_model.autoselect = False
        self.results_view.set_model(self.search_selection_model)
        self.results_view.set_factory(view_factory)
        # self.results_view.connect("activate", lambda i: self.entry_activated(pos=i))
        self.popover.set_parent(self)

        menu = Gio.Menu()
        for name, docset in get_registry().entries.items():
            variant = GLib.Variant.new_string(name)
            menu.append(docset.title, f"win.change_docset({variant})")
        self.docset_btn.set_menu_model(menu)

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

        results = self.docset.search(text)
        self.search_result_model.remove_all()
        for result in results:
            self.search_result_model.append(result)

        # self.search_result_model.data = results
        # self.search_selection_model.set_selected(False)
        self.popover.set_visible(True)

    def entry_activated(self, pos: int = None, doc: DocSet = None):
        pos = pos if pos else self.search_selection_model.selected()
        doc = self.search_result_model.get_item(pos)

    def set_docset(self, docset: DocSet):
        self.docset = docset

        if docset:
            self.docset_label.set_label(docset.title)
            self.docset_icon.set_from_gicon(docset.icon)
        else:
            self.docset_label.set_label("DocSet")
            self.docset_icon.set_from_icon_name("accessories-dictionary-symbolic")
