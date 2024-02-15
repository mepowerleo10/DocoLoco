import html
import re
from typing import cast
from urllib.parse import unquote

import gi
from bs4 import BeautifulSoup

from ..config import default_config
from ..helpers import add_symmetric_margins
from ..models import Doc, DocSet, Section
from .locator import Locator
from .new_page import NewPage
from .section_widget import SectionWidget

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit2", "4.1")
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango, WebKit  # noqa: E402


@Gtk.Template(filename=default_config.template("doc_page"))
class DocPage(Adw.Bin):
    __gtype_name__ = "DocPage"

    web_view = cast(WebKit.WebView, Gtk.Template.Child("web_view"))
    progress_bar = cast(Gtk.SearchBar, Gtk.Template.Child("progress_bar"))
    search_bar = cast(Gtk.SearchBar, Gtk.Template.Child("search_bar"))
    search_count_label = cast(Gtk.Label, Gtk.Template.Child("search_count_label"))
    search_entry = cast(Gtk.SearchEntry, Gtk.Template.Child("entry"))
    sidebar = cast(Gtk.Box, Gtk.Template.Child("sidebar"))
    search_ready = False
    title = GObject.Property(
        type=str, default="Choose DocSet", flags=GObject.ParamFlags.READWRITE
    )

    zoom_level = GObject.Property(
        type=float, default=1.0, flags=GObject.ParamFlags.READWRITE
    )
    zoom_step = 0.1
    content_page = None
    symbols_frame = Gtk.Frame()

    def __init__(self, docset: DocSet = None, uri: str = None):
        super().__init__(hexpand=True, vexpand=True)
        self.locator = Locator()

        self.web_view.connect("load-failed", self.on_load_failed)
        self.web_view.connect("load-changed", self.on_load_changed)
        self.web_view.connect("context-menu", self.on_context_menu)

        self.bind_property(
            "title",
            self.locator.search_btn.get_child(),
            "label",
            GObject.BindingFlags.DEFAULT,
        )

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.append(self.paned)

        self.related_docs: Gio.ListStore = Gio.ListStore()

        if uri:
            self.load_uri(uri)
        elif docset:
            self.docset = docset
        else:
            self.content_page = self.get_child()
            new_page = NewPage()
            self.set_child(new_page)

        self.web_view.bind_property(
            "estimated-load-progress",
            self.progress_bar,
            "fraction",
            GObject.BindingFlags.DEFAULT,
        )
        self.web_view.bind_property(
            "zoom-level",
            self,
            "zoom_level",
            GObject.BindingFlags.BIDIRECTIONAL,
        )

        self._create_symbols_sections()
        self._create_related_links_frame()

    def _create_symbols_sections(self):
        if not self.docset or len(self.docset.sections) == 0:
            self.symbols_frame.set_visible(False)
            return

        sections_list_store = Gio.ListStore(item_type=Section)
        for title, count in self.docset.symbol_counts.items():
            section = Section(title, count)
            sections_list_store.append(section)

        view_factory = Gtk.SignalListItemFactory()
        view_factory.connect("setup", self._setup_sections)
        view_factory.connect("bind", self._bind_sections)

        list_selection_model = Gtk.SingleSelection(model=sections_list_store)

        sections_tree = Gtk.ListView()
        sections_tree.set_model(list_selection_model)
        sections_tree.set_factory(view_factory)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(sections_tree)
        scrolled_window.set_vexpand(True)

        self.symbols_frame.set_label("Symbols")
        self.symbols_frame.set_child(scrolled_window)
        self.symbols_frame.set_visible(True)
        add_symmetric_margins(self.symbols_frame, vertical=4, horizontal=4)
        self.paned.set_start_child(self.symbols_frame)

    def _setup_sections(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        widget = SectionWidget()
        list_item.set_child(widget)

    def _bind_sections(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        widget = cast(SectionWidget, list_item.get_child())
        section = cast(Section, list_item.get_item())
        widget.build_with(section, self.docset)

    def _create_related_links_frame(self):
        view_factory = Gtk.SignalListItemFactory()
        view_factory.connect("setup", self._setup_related_link)
        view_factory.connect("bind", self._bind_related_link)

        list_selection_model = Gtk.SingleSelection(model=self.related_docs)

        related_links_list = Gtk.ListView()
        related_links_list.set_model(list_selection_model)
        related_links_list.set_factory(view_factory)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(related_links_list)
        scrolled_window.set_vexpand(True)

        related_links_frame = Gtk.Frame()
        related_links_frame.set_label("Related Links")
        related_links_frame.set_child(scrolled_window)
        add_symmetric_margins(related_links_frame, vertical=4, horizontal=4)

        self.paned.set_end_child(related_links_frame)

    def _setup_related_link(self, factory, obj):
        list_item = cast(Gtk.ListItem, obj)
        box = Gtk.Box()
        icon = Gtk.Image()
        label = Gtk.Label()

        box.append(icon)
        box.append(label)
        list_item.set_child(box)

    def _bind_related_link(self, factory, obj):
        list_item = cast(Gtk.ListItem, obj)
        box = cast(Gtk.Box, list_item.get_child())
        label = cast(Gtk.Label, box.get_last_child())

        doc = cast(Doc, list_item.get_item())
        label.set_markup(
            f"<a href='{html.escape(doc.url)}'>{html.escape(doc.name)}</a>"
        )
        label.set_cursor(Gdk.Cursor.new_from_name("pointer"))
        label.set_margin_start(10)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_tooltip_text(doc.name)

        label.connect("activate-link", self._on_related_link_clicked)
        label.connect("activate-current-link", self._on_related_link_clicked)

        menu = Gio.Menu()
        menu.append(
            "Open In New Tab",
            f"win.open_in_new_tab({GLib.Variant('(sss)', (doc.url, self.docset.provider_id, self.docset.name))})",
        )
        label.set_extra_menu(menu)

    def _on_related_link_clicked(self, label: Gtk.Label, path: str, *args):
        label.stop_emission_by_name("activate-link")
        variant = GLib.Variant.new_string(path)
        self.activate_action("win.open_page", variant)

    def load_uri(self, uri: str):
        self.setup_search_signals()
        uri = self.clean_uri(uri)
        uri = unquote(uri)

        self.web_view.load_uri(uri)
        self.web_view.bind_property(
            "title", self, "title", GObject.BindingFlags.DEFAULT
        )

    def get_content(self, uri: str):
        uri = uri.split("://")[1].split("#")[0]
        with open(uri, "r") as file:
            content = "".join(file.readlines())
            cleand_content = content.replace("<?xml", "<!--?xml").replace("?>", "?-->")
            return cleand_content

    def clean_uri(self, uri: str):
        # Define a regular expression pattern to find metadata tags
        metadata_pattern = re.compile(r"<dash_entry_[^>]+>")

        # Remove metadata tags from the input uri
        cleaned_uri = re.sub(metadata_pattern, "", uri)
        return cleaned_uri

    def on_load_changed(self, web_view, event):
        match event:
            case WebKit.LoadEvent.STARTED:
                self.progress_bar.set_visible(True)
            case WebKit.LoadEvent.FINISHED:
                mime_type = web_view.get_main_resource().get_response().get_mime_type()
                if mime_type == "application/xhtml+xml":
                    # TODO: Find a better way to handle WebKitGTK being unforgiving on rendering XML
                    self.remove_xml_and_load_new_content(web_view)

                self.progress_bar.set_visible(False)

                self.related_docs.remove_all()
                for doc in self.docset.related_docs_of(web_view.get_uri()):
                    self.related_docs.append(doc)

    def remove_xml_and_load_new_content(self, web_view):
        current_uri: str = web_view.get_uri()
        resource_path: str = current_uri.split("#")[0]
        if resource_path.startswith("file://"):
            resource_path = resource_path.replace("file://", "")
            with open(resource_path, "r") as resource:
                soup = BeautifulSoup(resource, "html.parser")
                for xml_tag in soup.find_all(
                    "xml"
                ):  # delete all xml tags if in document
                    xml_tag.decompose()

                for element in soup.find_all(
                    "html"
                ):  # remove xml related attributes from the html tag
                    element.attrs.pop("xmlns", None)
                    element.attrs.pop("xml:lang", None)

                web_view.load_alternate_html(str(soup), current_uri, current_uri)

    def on_load_failed(self, web_view, load_event, failing_uri: str, error):
        print(error)

    def on_context_menu(
        self,
        web_view: WebKit.WebView,
        context_menu: WebKit.ContextMenu,
        hit_test_result: WebKit.HitTestResult,
    ):
        if hit_test_result.context_is_link():
            if not self.docset:
                return

            action = Gio.SimpleAction(
                name="open_in_new_tab", parameter_type=GLib.VariantType.new("s")
            )
            action.connect("activate", self._on_open_in_new_tab)
            open_in_new_tab_item = WebKit.ContextMenuItem.new_from_gaction(
                action,
                "Open In New Tab",
                GLib.Variant.new_string(hit_test_result.get_link_uri()),
            )
            context_menu.remove(
                context_menu.get_item_at_position(1)
            )  # Remove the 'Open in New Window' action
            context_menu.remove(
                context_menu.get_item_at_position(1)
            )  # Remove the 'Download Linked File' action
            context_menu.insert(open_in_new_tab_item, 1)

    def _on_open_in_new_tab(self, action, url):
        self.activate_action(
            "win.open_in_new_tab",
            GLib.Variant(
                "(sss)", (url.get_string(), self.docset.provider_id, self.docset.name)
            ),
        )

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

    @GObject.Property(type=bool, default=False)
    def can_go_back(self) -> bool:
        return self.web_view.can_go_back() if self.web_view else False

    def go_back(self, *args):
        self.web_view.go_back()

    @GObject.Property(type=bool, default=False)
    def can_go_forward(self) -> bool:
        return self.web_view.can_go_forward() if self.web_view else False

    def go_forward(self, *args):
        return self.web_view.go_forward()

    def zoom_in(self, *args):
        self.zoom_level = self.zoom_level + self.zoom_step

    def zoom_out(self, *args):
        self.zoom_level = self.zoom_level - self.zoom_step

    def reset_zoom(self, *args):
        self.zoom_level = 1.0

    def page_search(self, *args):
        self.search_bar.set_search_mode(True)

    def filter_docset(self, name: str):
        if isinstance(self.get_child(), NewPage):
            new_page = cast(NewPage, self.get_child())
            new_page.filter_item(name)

    @property
    def docset(self) -> DocSet:
        return self.locator.docset

    @docset.setter
    def docset(self, docset: DocSet):
        self.locator.docset = docset
        self.load_uri(docset.index_file_path.as_uri())
        self._create_symbols_sections()

        if isinstance(self.get_child(), NewPage):
            self.set_child(self.content_page)
