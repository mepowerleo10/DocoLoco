from .config import Config
import gi
from typing import List, cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit

from .registry import DocSet, registered_providers

config = Config()


@Gtk.Template(filename=f"{config.ui_path}/new_page.ui")
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    box = cast(Gtk.FlowBox, Gtk.Template.Child("docsets"))

    def __init__(self):
        super().__init__()

        docs = registered_providers[0].docs
        for doc in docs:
            card = DocSetCard(doc)
            self.box.append(card)


@Gtk.Template(filename=config.ui("doc_page"))
class DocPage(Adw.Bin):
    __gtype_name__ = "DocPage"

    web_view = cast(WebKit.WebView, Gtk.Template.Child("web_view"))
    search_bar = cast(Gtk.SearchBar, Gtk.Template.Child("search_bar"))
    search_count_label = cast(Gtk.Label, Gtk.Template.Child("search_count_label"))
    search_entry = cast(Gtk.SearchEntry, Gtk.Template.Child("entry"))
    search_ready = False

    def __init__(self, docset: DocSet = None, uri: str = None):
        super().__init__(hexpand=True, vexpand=True)
        self.docset = docset

        if uri:
            self.load_uri(uri)
        else:
            self.set_child(NewPage())

    def load_uri(self, uri: str):
        self.setup_search_signals()
        self.web_view.load_uri(uri)

    def setup_search_signals(self):
        # web_view.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)

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


@Gtk.Template(filename=config.ui("doc_set_card"))
class DocSetCard(Adw.Bin):
    __gtype_name__ = "DocSetCard"
    title = cast(Gtk.Label, Gtk.Template.Child("title"))
    version = cast(Gtk.Label, Gtk.Template.Child("version"))
    index_path = cast(Gtk.Label, Gtk.Template.Child("index_path"))

    def __init__(self, doc: DocSet, **kwargs):
        super().__init__(**kwargs)

        self.title.set_label(doc.title)
        self.version.set_label(doc.version if doc.version else "Unknown")
        self.index_path.set_label(doc.index_file_path.as_posix())


@Gtk.Template(filename="data/ui/main.ui")
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    tab_view = cast(Adw.TabView, Gtk.Template.Child("view"))

    def __init__(self, app, docs: List[DocSet]):
        super().__init__(application=app, title="DocoLoco")
        self.docs = docs

        if self.tab_view.get_n_pages() == 0:
            self.new_tab()

    @Gtk.Template.Callback()
    def new_tab(self, *args, **kwargs):
        page = DocPage(uri="http://google.com")
        self.tab_view.append(page)
        # self.tab_view.set_selected_page(page)
