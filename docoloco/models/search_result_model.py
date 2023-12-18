from typing import List
from . import DocSet
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject


class SearchResultModel(GObject.Object, Gio.ListModel):
    data: List[DocSet] = list()

    def set(self, data: List[DocSet]):
        old_data_size = len(self.data)
        self.data = data
        self.items_changed(position=0, added=len(self.data), removed=old_data_size)

    def reset(self):
        old_data_size = len(self.data)
        self.data.clear()
        self.items_changed(position=0, added=0, removed=old_data_size)

    def get_n_items(self):
        return len(self.data)

    def get_item(self, position=None):
        return self.data[position]
