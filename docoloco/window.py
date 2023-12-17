from .config import Config
import gi
from typing import List, cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit

from .registry import DocSet, provider

config = Config()


@Gtk.Template(filename=f"{config.ui_path}/new_page.ui")
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    box = cast(Gtk.FlowBox, Gtk.Template.Child("docsets"))

    def __init__(self):
        super().__init__()

        docs = provider.docs
        for doc in docs.values():
            button = Gtk.ToggleButton(
                label=doc.title,
                action_name="win.change_docset",
                action_target=GLib.Variant.new_string(doc.name),
            )
            self.box.append(button)


@Gtk.Template(filename=config.ui("doc_page"))
class DocPage(Adw.Bin):
    __gtype_name__ = "DocPage"

    web_view = cast(WebKit.WebView, Gtk.Template.Child("web_view"))
    search_bar = cast(Gtk.SearchBar, Gtk.Template.Child("search_bar"))
    search_count_label = cast(Gtk.Label, Gtk.Template.Child("search_count_label"))
    search_entry = cast(Gtk.SearchEntry, Gtk.Template.Child("entry"))
    search_ready = False

    title = "Choose a DocSet"

    def __init__(self, docset: DocSet = None, uri: str = None):
        super().__init__(hexpand=True, vexpand=True)
        self.docset = docset

        if uri:
            self.load_uri(uri)
        elif docset:
            self.load_uri(docset.index_file_path.as_uri())
        else:
            self.set_child(NewPage())

    def on_load_changed(self, *args):
        self.title = self.web_view.get_title()

    def load_uri(self, uri: str):
        self.setup_search_signals()
        self.web_view.load_uri(uri)
        # web_view.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)
        self.web_view.connect("load-changed", self.on_load_changed)

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
        history = self.web_view.get_back_forward_list()
        if history.get_back_item():
            history.go_back()

    def can_go_forward(self) -> bool:
        return self.web_view.can_go_forward()

    def go_forward(self, *args):
        return self.web_view.go_forward()

    def page_search(self, *args):
        self.search_bar.set_search_mode(True)


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

    go_back_action: Gio.SimpleAction
    go_forward_action: Gio.SimpleAction

    def __init__(self, app: Adw.Application, docs: List[DocSet]):
        super().__init__(application=app, title="DocoLoco")
        self.docs = docs
        self.app = app

        if self.tab_view.get_n_pages() == 0:
            self.new_tab()

        self.setup_actions()

        self.go_back_action = Gio.SimpleAction(name="go_back")
        self.go_back_action.connect("activate", self.selected_doc_page.go_back)
        self.add_action(self.go_back_action)

        self.go_forward_action = Gio.SimpleAction(name="go_forward")
        self.go_forward_action.connect("activate", self.selected_doc_page.go_forward)
        self.add_action(self.go_forward_action)

    def setup_actions(self):
        actions = [
            {
                "name": "new_tab",
                "shortcut": "<primary>T",
                "closure": lambda x, y: self.new_tab(),
            },
            {
                "name": "page_search",
                "shortcut": "<primary>F",
                "closure": lambda x, y: self.selected_doc_page.page_search(),
            },
        ]

        for action in actions:
            g_action = Gio.SimpleAction(name=action["name"])
            g_action.connect("activate", action["closure"])
            self.add_action(g_action)

            shortcut = action["shortcut"]
            if shortcut:
                self.app.set_accels_for_action(f"win.{action['name']}", [shortcut])

        g_action = Gio.SimpleAction(
            name="change_docset", parameter_type=GLib.VariantType.new("s")
        )
        g_action.connect("activate", self.change_docset)
        self.add_action(g_action)

    @Gtk.Template.Callback()
    def new_tab(self, *args):
        doc_page = DocPage()
        self.add_tab(doc_page)

    def add_tab(self, doc_page: DocPage, position: int = None):
        if position:
            page = self.tab_view.insert(doc_page, position)
        else:
            page = self.tab_view.append(doc_page)

        page.set_title(doc_page.title)
        page.set_live_thumbnail(True)
        self.tab_view.set_selected_page(page)

    def change_docset(self, action, name: GLib.VariantType.new("s")):
        docset = provider.docs[name.get_string()]
        doc_page = DocPage(docset)

        page = self.tab_view.get_selected_page()
        position: int = self.tab_view.get_page_position(page)
        self.tab_view.close_page(page)

        self.add_tab(doc_page, position)

    @property
    def selected_doc_page(self) -> DocPage:
        adw_page = self.tab_view.get_selected_page()
        # if not adw_page.child
        # adw_page.child = DocPage()

        return adw_page.get_child()
