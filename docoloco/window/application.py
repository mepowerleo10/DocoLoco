import re

from .doc_page import DocPage
from ..locator import Locator
from ..config import default_config
import gi
from typing import cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gio, GLib
from ..registry import get_registry


@Gtk.Template(filename=default_config.ui("main"))
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
            name="open_page", parameter_type=GLib.VariantType.new("s")
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

    def focus_locator(self, *args):
        self.locator.toggle_focus()

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

        self.update_ui_for_page_change(doc_page)

    def doc_page(self, pos: int) -> DocPage:
        adw_page = self.tab_view.get_nth_page(pos)

        return adw_page.get_child()

    @property
    def selected_doc_page(self) -> DocPage:
        adw_page = self.tab_view.get_selected_page()
        # if not adw_page.child
        # adw_page.child = DocPage()

        return adw_page.get_child()
