import re
from urllib.parse import unquote
from .locator import Locator
from .config import Config
import gi
from typing import List, cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit

from .registry import DocSet, get_registry

config = Config()


@Gtk.Template(filename=f"{config.ui_path}/new_page.ui")
class NewPage(Adw.Bin):
    __gtype_name__ = "NewPage"
    box = cast(Gtk.FlowBox, Gtk.Template.Child("docsets"))

    def __init__(self):
        super().__init__()

        docs = get_registry().entries
        for doc in docs.values():
            box = Gtk.Box(spacing=6)

            icon = Gtk.Image()
            icon.set_from_gicon(doc.icon)
            box.append(icon)

            label = Gtk.Label(label=doc.title)
            box.append(label)

            button = Gtk.Button(
                # label=doc.title,
                action_name="win.change_docset",
                action_target=GLib.Variant.new_string(doc.name),
            )
            button.set_child(box)
            self.box.append(button)


@Gtk.Template(filename=config.ui("doc_page"))
class DocPage(Adw.Bin):
    __gtype_name__ = "DocPage"

    web_view = cast(WebKit.WebView, Gtk.Template.Child("web_view"))
    search_bar = cast(Gtk.SearchBar, Gtk.Template.Child("search_bar"))
    search_count_label = cast(Gtk.Label, Gtk.Template.Child("search_count_label"))
    search_entry = cast(Gtk.SearchEntry, Gtk.Template.Child("entry"))
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
    locator: Locator = None
    header_bar: Adw.HeaderBar = cast(Adw.HeaderBar, Gtk.Template.Child("header_bar"))

    go_back_action: Gio.SimpleAction
    go_forward_action: Gio.SimpleAction

    primary_menu_btn = cast(Gtk.MenuButton, Gtk.Template.Child("primary_menu_btn"))

    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="DocoLoco")
        self.app = app
        self.locator = Locator()

        self.tab_view.connect("notify::title", self.on_tab_change)
        if self.tab_view.get_n_pages() == 0:
            self.new_tab()

        # TODO: Setup tab_view signals for on-close

        self.header_bar.set_title_widget(self.locator)
        self.popover_primary_menu = cast(
            Gtk.PopoverMenu, self.primary_menu_btn.get_popover()
        )

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
            {
                "name": "focus_locator",
                "shortcut": "<primary>P",
                "closure": self.focus_locator,
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
            name="open_page", parameter_type=GLib.VariantType("s")
        )
        g_action.connect("activate", self.open_page)
        self.add_action(g_action)

        g_action = Gio.SimpleAction(
            name="change_docset", parameter_type=GLib.VariantType.new("s")
        )
        g_action.connect("activate", self.change_docset)
        self.add_action(g_action)

    @Gtk.Template.Callback()
    def new_tab(self, *args, **kwargs):
        docset = None
        if "docset" in kwargs.keys():
            docset = kwargs.pop("docset")

        doc_page = DocPage(docset=docset) if docset else DocPage()
        self.add_tab(doc_page)
        self.locator.set_docset(docset)

    def add_tab(self, doc_page: DocPage, position: int = None):
        if position:
            page = self.tab_view.insert(doc_page, position)
        else:
            page = self.tab_view.append(doc_page)

        # doc_page.bind_property("title", page, "title", GObject.BindingFlags.DEFAULT)
        page.set_title(doc_page.title)
        page.set_live_thumbnail(True)
        self.tab_view.set_selected_page(page)

    def on_tab_change(self, *args):
        pass

    def on_doc_page_change(self, doc_page: DocPage):
        if doc_page != self.selected_doc_page:
            return

        self.update_ui_for_page_change(doc_page)

    def on_selected_page_change(self, **kwargs):
        doc_page = self.selected_doc_page
        self.update_ui_for_page_change(doc_page)

        if doc_page:
            self.change_docset(GLib.Variant(doc_page.docset.name))

    def update_ui_for_page_change(self, doc_page: DocPage = None):
        if doc_page:
            self.locator.set_docset(doc_page.docset)
            self.go_back_action.set_enabled(doc_page.can_go_back())
            self.go_forward_action.set_enabled(doc_page.can_go_forward())
        else:
            self.locator.set_docset(None)
            self.go_back_action.set_enabled(False)
            self.go_forward_action.set_enabled(False)

    def focus_locator(self, *args, **kwargs):
        self.locator.grab_focus()

    def change_docset(self, action=None, name: GLib.Variant = None):
        if not name:
            return

        docset = get_registry().get(name.get_string())
        self.locator.set_docset(docset)
        doc_page = DocPage(docset)

        page = self.tab_view.get_selected_page()
        position: int = self.tab_view.get_page_position(page)
        self.tab_view.close_page(page)

        self.add_tab(doc_page, position)

    """ def change_docset(self, name: GLib.Variant = None):
        if not name:
            return

        docset = get_registry().get(name.get_string())
        self.locator.docset = docset
        self.selected_doc_page(docset) """

    def open_page(self, action=None, variant: GLib.Variant = None):
        if variant:
            self.open_page_uri(variant.get_string())

    def open_page_uri(self, uri: str):
        if not self.tab_view.get_n_pages():
            doc_page = DocPage(self.locator.docset, uri)
            self.add_tab(doc_page)
        else:
            doc_page = self.selected_doc_page
            doc_page.load_uri(uri)

    def doc_page(self, pos: int) -> DocPage:
        adw_page = self.tab_view.get_nth_page(pos)

        return adw_page.get_child()

    @property
    def selected_doc_page(self) -> DocPage:
        adw_page = self.tab_view.get_selected_page()
        # if not adw_page.child
        # adw_page.child = DocPage()

        return adw_page.get_child()
