import re
from urllib.parse import unquote

from .new_page import NewPage
from ..config import default_config
import gi
from typing import cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit

from ..registry import DocSet


@Gtk.Template(filename=default_config.ui("doc_page"))
class DocPage(Adw.Bin):
    __gtype_name__ = "DocPage"

    web_view = cast(WebKit.WebView, Gtk.Template.Child("web_view"))
    search_bar = cast(Gtk.SearchBar, Gtk.Template.Child("search_bar"))
    search_count_label = cast(Gtk.Label, Gtk.Template.Child("search_count_label"))
    search_entry = cast(Gtk.SearchEntry, Gtk.Template.Child("entry"))
    sidebar = cast(Gtk.Box, Gtk.Template.Child("sidebar"))
    search_ready = False
    base_uri: str = None
    anchor: str = None

    def __init__(self, docset: DocSet = None, uri: str = None):
        super().__init__(hexpand=True, vexpand=True)
        self.docset = docset

        self.title = "Choose a DocSet"

        # context = WebKit.WebContext#.new_with_website_data_manager(WebKit.WebsiteDataManager())
        # self.web_view = WebKit.WebView()

        self.web_view.connect("load-failed", self.on_load_failed)
        self.web_view.connect("load-changed", self.on_load)

        self.update_sections()

        if uri:
            self.load_uri(uri)
        elif docset:
            self.load_uri(docset.index_file_path.as_uri())
        else:
            self.set_child(NewPage())

    def on_load_changed(self, *args):
        self.title = self.web_view.get_title()

    def update_sections(self):
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)

        if self.docset:
            for title, docs in self.docset.sections.items():
                section = Gtk.Expander(label=f"{title}")
                section.set_margin_bottom(6)
                """ section.override_background_color(
                    Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0)
                ) """
                item_list = Gtk.ListBox()
                item_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

                """ section = Adw.ExpanderRow()
                section.set_title(title=title) """
                for doc in docs:
                    button = Gtk.Button(hexpand=True)
                    # content = Adw.ButtonContent()
                    # content.set_icon_name(doc.icon_name)
                    # content.set_label(doc.name)
                    # button.set_child(content)

                    item_label = Gtk.Label(label=doc.name, halign=Gtk.Align.START)
                    item_label.set_margin_bottom(5)
                    item_label.set_cursor(Gdk.Cursor.new_from_name("pointer"))
                    item_label.set_margin_start(10)
                    button.set_child(item_label)
                    button.connect("activate", self.on_item_clicked)
                    item_list.append(button)

                    # section.add_row(button)
                    # item_list.append(button)
                section.set_child(item_list)
                list_box.append(section)
                # self.sidebar.append(section)

        scrolled_window = Gtk.ScrolledWindow()
        # scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(list_box)
        scrolled_window.set_vexpand(True)
        self.sidebar.append(scrolled_window)

    def on_item_clicked(self, *args):
        # variant = GLib.Variant.new_string(path)
        self.activate_action(f"win.open_page", None)

    def load_uri(self, uri: str):
        self.setup_search_signals()
        uri = unquote(uri)
        uri = self.clean_uri(uri)
        # uri_components = uri.split("#")
        # if len(uri_components) == 1:
        #     self.base_uri, self.anchor = (uri_components[0], None)
        # else:
        #     self.base_uri, self.anchor = uri_components

        self.web_view.load_uri(uri)
        # self.web_view.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)
        self.web_view.connect("load-changed", self.on_load_changed)

    def clean_uri(self, uri: str):
        # Define a regular expression pattern to find metadata tags
        metadata_pattern = re.compile(r"<dash_entry_[^>]+>")

        # Remove metadata tags from the input uri
        cleaned_uri = re.sub(metadata_pattern, "", uri)
        return cleaned_uri

    def on_load(self, web_view, event):
        if self.anchor and event == WebKit.LoadEvent.FINISHED:
            self.web_view.evaluate_javascript(
                f"location.hash = '{self.anchor}'", -1, None, None, None, None, None
            )

    def on_load_failed(self, web_view, load_event, failing_uri: str, error):
        print(error)

    def setup_search_signals(self):
        self.search_bar.connect_entry(self.search_entry)
        self.search_bar.key_capture_widget = self

        self.find_controller = self.web_view.get_find_controller()
        self.find_controller.connect("counted-matches", self.counted_matches)
        self.find_controller.connect(
            "failed-to-find-text", lambda f: self.search_entry.add_css_class("error")
        )
        self.find_controller.connect(
            "found-text", lambda f, v: self.search_entry.remove_css_class("error")
        )

    def counted_matches(self, find_controller, count):
        self.search_ready = True
        self.search_count_label.set_label(f"{count} matches")

    def failed_to_find_text(self, find_controller):
        self.search_entry.add_css_class("error")

    @Gtk.Template.Callback()
    def search_started(self, entry: Gtk.SearchEntry):
        text = entry.get_text()
        self.find_controller.search(text, WebKit.FindOptions.CASE_INSENSITIVE, 1000)
        self.find_controller.count_matches(
            text, WebKit.FindOptions.CASE_INSENSITIVE, 1000
        )

    @Gtk.Template.Callback()
    def search_stopped(self, *args):
        self.search_ready = False
        self.find_controller.search_finish()

    @Gtk.Template.Callback()
    def search_next(self, *args):
        self.find_controller.search_next()

    @Gtk.Template.Callback()
    def search_previous(self, *args):
        self.find_controller.search_previous()

    def can_go_back(self) -> bool:
        return self.web_view.can_go_back()

    def go_back(self, *args):
        # history = self.web_view.get_back_forward_list()
        # if history.get_back_item():
        #     history.go_back()
        self.web_view.go_back()

    def can_go_forward(self) -> bool:
        return self.web_view.can_go_forward()

    def go_forward(self, *args):
        return self.web_view.go_forward()

    def page_search(self, *args):
        self.search_bar.set_search_mode(True)
