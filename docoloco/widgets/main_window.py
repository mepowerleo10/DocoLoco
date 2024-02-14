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
        # TODO: Setup tab_view signals for on-close

        self.popover_primary_menu = cast(
            Gtk.PopoverMenu, self.primary_menu_btn.get_popover()
        )

        self.setup_actions()

        self.go_back_action.connect("activate", self.go_back)
        self.add_action(self.go_back_action)

        self.go_forward_action.connect("activate", self.go_forward)
        self.add_action(self.go_forward_action)

        if self.tab_view.get_n_pages() == 0:
            self.new_tab()

    def setup_style_context(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(
            default_config.get_path_from_style("style.css").as_posix()
        )
        self.get_style_context().add_provider_for_display(
            self.get_display(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_actions(self):
        actions = [
            # (action_name, method_to_call, argument_types, shortcut, shortcut_arguments)
            (
                "open_new_tab",
                self.open_new_tab,
                "i",
                "<primary>T",
                f"({GLib.Variant.new_int32(-1)})",
            ),
            (
                "page_search",
                lambda *_: self.selected_doc_page.page_search(),
                None,
                "<primary>F",
                None,
            ),
            ("focus_locator", self.focus_locator, None, "<primary>P", None),
            ("clear_filters", self.clear_filters, None, "<primary>BackSpace", None),
            ("zoom_in", self.zoom_in, None, "<primary>equal", None),
            ("zoom_out", self.zoom_out, None, "<primary>minus", None),
            ("reset_zoom", self.reset_zoom, None, "<primary>plus", None),
            ("open_page", self.open_page, "s", None, None),
            ("open_page_uri", self.open_page_uri, "s", None, None),
            ("change_docset", self.change_docset, "(ssi)", None, None),
            ("change_section", self.change_section, "s", None, None),
            ("open_in_new_tab", self.open_in_new_tab, "(sss)", None, None),
            ("filter_docset", self.filter_docset, "s", None, None),
            ("close_tab", self.close_tab, None, "<primary>W", None),
            ("go_back", self.go_back, None, "<Alt>Left", None),
            ("go_forward", self.go_forward, None, "<Alt>Right", None),
        ]

        for action in actions:
            self.create_action(action)

    def create_action(self, action_desc: Tuple[str, str, Callable, str]):
        name, on_activate, parameter_type, shortcut, shortcut_args = action_desc
        g_action = Gio.SimpleAction(
            name=name,
            parameter_type=(
                GLib.VariantType.new(parameter_type) if parameter_type else None
            ),
        )
        g_action.connect("activate", on_activate)
        self.add_action(g_action)

        if shortcut:
            self.app.set_accels_for_action(
                f"win.{name}{shortcut_args if shortcut_args else ''}", [shortcut]
            )

    @Gtk.Template.Callback()
    def new_tab(self, *args):
        self.activate_action("win.open_new_tab", GLib.Variant.new_int32(-1))

    def open_new_tab(self, _, position_variant):
        doc_page = DocPage()
        position = position_variant.get_int32()
        self.add_tab(
            doc_page,
            None if position == -1 else position,
        )

    def add_tab(self, doc_page: DocPage, position: int = None):
        page: Adw.TabPage = None
        if position is not None:
            page = self.tab_view.insert(doc_page, position)
        else:
            page = self.tab_view.append(doc_page)

        docset = doc_page.docset
        if docset:
            page.set_icon(docset.icon)

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

    def change_section(self, _, name_variant):
        name = name_variant.get_string()
        self.selected_doc_page.locator.change_section(name)

    def focus_locator(self, *args):
        self.selected_doc_page.locator.toggle_focus()

    def clear_filters(self, *_):
        if self.selected_doc_page.locator.search_box.get_focus_child():
            self.selected_doc_page.locator.clear_filters()

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
            self.open_page_uri(None, variant)

    def open_page_uri(self, action, uri_variant: GLib.Variant):
        uri = uri_variant.get_string()
        if not self.tab_view.get_n_pages():
            doc_page = DocPage(uri)
            self.add_tab(doc_page)
        else:
            doc_page = self.selected_doc_page
            doc_page.load_uri(uri)

    def open_in_new_tab(self, action, parameters):
        if not (parameters or action):
            return

        url, provider_id, docset_name = parameters.unpack()

        position = self.tab_view.get_page_position(self.tab_view.get_selected_page())
        self.activate_action("win.open_new_tab", GLib.Variant.new_int32(position + 1))
        self.activate_action(
            "win.change_docset",
            GLib.Variant("(ssi)", (provider_id, docset_name, 0)),
        )
        self.activate_action("win.open_page", GLib.Variant.new_string(url))

    def close_tab(self, action, *parameters):
        self.tab_view.close_page(
            self.tab_view.get_selected_page(),
        )

        if self.tab_view.get_n_pages() == 0:
            self.new_tab()

    def doc_page(self, pos: int) -> DocPage:
        adw_page = self.tab_view.get_nth_page(pos)

        return adw_page.get_child()

    @property
    def selected_doc_page(self) -> DocPage:
        page = self.tab_view.get_selected_page()

        if page:
            return page.get_child()
