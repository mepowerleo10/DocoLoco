from typing import List, cast
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject

from .registry import DocSet


class Window(Gtk.ApplicationWindow):
    __gtype_name__ = "Window"

    def __init__(self, app, docs):
        """Initialize the main window"""

        super().__init__(application=app, title="Documentation Browser")

        self.set_default_size(600, 600)
        self.set_title("Documentation Browser")

        Gtk.Settings.get_default().set_property("gtk-icon-theme-name", "Adwaita")

        self.overlay_split_view = Adw.OverlaySplitView.new()
        self.set_child(self.overlay_split_view)

        self.docs: List[DocSet] = docs

        # Sidebar
        self.sidebar_content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10
        )

        self.sidebar_content_box.set_margin_start(6)
        self.sidebar_content_box.set_margin_end(6)
        self.sidebar_content_box.set_margin_top(6)
        self.sidebar_content_box.set_margin_bottom(6)

        # Create the search entry
        search_entry = Gtk.SearchEntry()
        search_entry.connect("search-changed", self.on_search_changed)
        self.sidebar_content_box.append(search_entry)

        # Create the listbox
        self.listbox = Gtk.ListBox()
        self.sidebar_content_box.append(self.listbox)

        # self.scrolled_box = Gtk.ScrolledWindow.new()
        # sidebar_content_box.append(self.scrolled_box)

        self.overlay_split_view.set_sidebar(self.sidebar_content_box)

        self.create_document_rows()

    def create_document_rows(self):
        for doc in self.docs:
            row = Gtk.ListBoxRow()
            text_expander = Gtk.Expander(label=doc.title)
            details = Gtk.Label(label=doc.index_file_path)
            text_expander.set_child(details)

            row.set_child(text_expander)
            self.listbox.append(row)

    def on_search_changed(self, search_entry: Gtk.SearchEntry):
        query = search_entry.get_text().lower()

        for row in self.listbox.observe_children():
            row = cast(Gtk.ListBoxRow, row)
            expander: Gtk.Expander = row.get_child()
            label_text = expander.get_label().lower()
            row.set_visible(query in label_text)

    def on_document_row_toggled(self, button: Gtk.Button, hbox: Gtk.Box):
        for child in hbox.get_children():
            child.set_visible(not child.get_visible())
