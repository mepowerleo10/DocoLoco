from typing import cast

from .models import DocSet, SearchResultModel
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
    results_view: Gtk.Widget = Gtk.Template.Child()
    popover: Gtk.Popover = Gtk.Template.Child()
    docset: DocSet = None
    search_result_model: SearchResultModel = None
    search_selection_model: Gtk.SingleSelection = None
    docset_btn: Gtk.MenuButton = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        # self.docset = DocSet()
        self.search_result_model = SearchResultModel()

        self.entry.connect("activate", lambda _: self.entry_activated())
        self.entry.connect("changed", lambda _: self.search_changed())

        menu = Gio.Menu()
        for name, docset in get_registry().entries.items():
            variant = GLib.Variant.new_string(name)
            menu.append(docset.title, f"win.change_docset({variant})")
        self.docset_btn.set_menu_model(menu)

    def search_changed(self):
        text = self.entry.get_text()

        if not (text or self.popover.is_visible()):
            return

        results = self.docset.search(text)
        self.search_result_model.set(results)
        self.search_selection_model.set_selected(False)
        self.popover.set_visible(True)

    def entry_activated(self, pos: int = None, doc: DocSet = None):
        pos = pos if pos else self.search_selection_model.selected()
        doc = self.search_result_model.get_item(pos)
