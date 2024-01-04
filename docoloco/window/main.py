from typing import Callable, Tuple, cast

import gi

from ..config import default_config
from ..registry import get_registry
from .doc_page import DocPage

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.template("main"))
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    tab_view = cast(Adw.TabView, Gtk.Template.Child("view"))
    tab_bar = cast(Adw.TabBar, Gtk.Template.Child())
    header_bar: Adw.HeaderBar = cast(Adw.HeaderBar, Gtk.Template.Child("header_bar"))

    go_back_action: Gio.SimpleAction
    go_forward_action: Gio.SimpleAction

    primary_menu_btn = cast(Gtk.MenuButton, Gtk.Template.Child("primary_menu_btn"))

    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="DocoLoco")
        self.app = app
        self.setup_style_context()

        self.go_back_action = Gio.SimpleAction(name="go_back")
        self.go_forward_action = Gio.SimpleAction(name="go_forward")

        self.tab_view.connect("notify::title", self.on_tab_change)
        self.tab_view.connect("notify::selected-page", self.on_tab_change)

        if self.tab_view.get_n_pages() == 0:
            self.new_tab()

        # TODO: Setup tab_view signals for on-close

        self.popover_primary_menu = cast(
            Gtk.PopoverMenu, self.primary_menu_btn.get_popover()
        )

        self.setup_actions()

        self.go_back_action.connect("activate", self.go_back)
        self.add_action(self.go_back_action)

        self.go_forward_action.connect("activate", self.go_forward)
        self.add_action(self.go_forward_action)

    def setup_style_context(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(
            default_config.get_path_from_style("style.css").as_posix()
        )
        self.get_style_context().add_provider_for_display(
            self.get_display(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_actions(self):
        actions = []

        for action in actions:
            self.create_action(action)

        parameterized_actions = [
            ("new_tab", "<primary>T", lambda *_: self.new_tab(), None),
            (
                "page_search",
                "<primary>F",
                lambda *_: self.selected_doc_page.page_search(),
                None,
            ),
            ("focus_locator", "<primary>P", self.focus_locator, None),
            ("zoom_in", "<primary>equal", self.zoom_in, None),
            ("zoom_out", "<primary>minus", self.zoom_out, None),
            ("reset_zoom", "<primary>plus", self.reset_zoom, None),
            ("open_page", None, self.open_page, "s"),
            ("change_docset", None, self.change_docset, "(ssi)"),
            ("filter_docset", None, self.filter_docset, "s"),
            ("change_filter", None, self.change_filter, "s"),
        ]

        for action in parameterized_actions:
            self.create_action(action)

    @Gtk.Template.Callback()
    def new_tab(self, *args, **kwargs):
        docset = None
        if "docset" in kwargs.keys():
            docset = kwargs.pop("docset")

        doc_page = DocPage(docset=docset) if docset else DocPage()
        self.add_tab(doc_page)

    def add_tab(self, doc_page: DocPage, position: int = None):
        if position:
            page = self.tab_view.insert(doc_page, position)
        else:
            page = self.tab_view.append(doc_page)

        doc_page.bind_property("title", page, "title", GObject.BindingFlags.DEFAULT)
        page.set_title(doc_page.title)
        page.connect("notify::title", self.on_page_title_changed)
        page.set_live_thumbnail(True)
        self.tab_view.set_selected_page(page)

    def on_page_title_changed(self, page: Adw.TabPage, title):
        self.update_ui_for_page_change(page.get_child())

    def on_tab_change(self, tab_view: Adw.TabView, selected_page):
        self.update_ui_for_page_change(self.selected_doc_page)

    def update_ui_for_page_change(self, doc_page: DocPage = None):
        if doc_page:
            self.go_back_action.set_enabled(doc_page.can_go_back)
            self.go_forward_action.set_enabled(doc_page.can_go_forward)
            self.header_bar.set_title_widget(doc_page.locator)

        else:
            self.go_back_action.set_enabled(False)
            self.go_forward_action.set_enabled(False)

    def change_filter(self, _, name_variant):
        name = name_variant.get_string()
        self.selected_doc_page.locator.change_filter(name)

    def focus_locator(self, *args):
        self.selected_doc_page.locator.toggle_focus()

    def zoom_in(self, *args):
        self.selected_doc_page.zoom_in()

    def zoom_out(self, *args):
        self.selected_doc_page.zoom_out()

    def reset_zoom(self, *args):
        self.selected_doc_page.reset_zoom()

    def go_back(self, *args):
        self.selected_doc_page.go_back()

    def go_forward(self, *args):
        self.selected_doc_page.go_forward()

    def filter_docset(self, action=None, name: GLib.Variant = None):
        self.selected_doc_page.filter_docset(name.get_string())

    def change_docset(self, action, parameters):
        if not (parameters or action):
            return

        provider_id, docset_name, position = parameters.unpack()
        docset = get_registry().get(provider_id, docset_name, position)
        if not docset.is_populated:
            docset.populate_all_sections()

        doc_page = DocPage(docset)

        page = self.tab_view.get_selected_page()
        position: int = self.tab_view.get_page_position(page)
        self.tab_view.close_page(page)

        self.add_tab(doc_page, position)

    def open_page(self, action=None, variant: GLib.Variant = None):
        if variant:
            self.open_page_uri(variant.get_string())

    def open_page_uri(self, uri: str):
        if not self.tab_view.get_n_pages():
            doc_page = DocPage(uri)
            self.add_tab(doc_page)
        else:
            doc_page = self.selected_doc_page
            doc_page.load_uri(uri)

    def doc_page(self, pos: int) -> DocPage:
        adw_page = self.tab_view.get_nth_page(pos)

        return adw_page.get_child()

    @property
    def selected_doc_page(self) -> DocPage:
        page = self.tab_view.get_selected_page()

        if page:
            return page.get_child()

    def create_action(self, action_desc: Tuple[str, str, Callable, str]):
        name, shortcut, on_activate, parameter_type = action_desc
        g_action = Gio.SimpleAction(
            name=name,
            parameter_type=(
                GLib.VariantType.new(parameter_type) if parameter_type else None
            ),
        )
        g_action.connect("activate", on_activate)
        self.add_action(g_action)

        if shortcut:
            self.app.set_accels_for_action(f"win.{name}", [shortcut])
