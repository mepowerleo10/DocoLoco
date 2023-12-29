import re
from typing import cast
from urllib.parse import unquote

from bs4 import BeautifulSoup

import gi

from ..config import default_config
from ..models import DocSet, Section
from .new_page import NewPage
from .section_widget import SectionWidget

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gio, GLib, GObject, Gtk, WebKit  # noqa: E402


@Gtk.Template(filename=default_config.ui("doc_page"))
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

    def __init__(self, docset: DocSet = None, uri: str = None):
        super().__init__(hexpand=True, vexpand=True)
        self.docset = docset

        self.web_view.connect("load-failed", self.on_load_failed)
        self.web_view.connect("load-changed", self.on_load_changed)
        self.web_view.connect("mouse-target-changed", self.on_mouse_target_changed)

        self._update_sections()

        if uri:
            self.load_uri(uri)
        elif docset:
            self.load_uri(docset.index_file_path.as_uri())
        else:
            new_page = NewPage()
            new_page.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)
            self.set_child(NewPage())

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

    def _update_sections(self):
        if not self.docset:
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
        self.sidebar.append(scrolled_window)

    def _setup_sections(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        widget = SectionWidget()
        list_item.set_child(widget)

    def _bind_sections(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        widget = cast(SectionWidget, list_item.get_child())
        section = cast(Section, list_item.get_item())
        widget.build_with(section, self.docset)

    def on_item_clicked(self, label: Gtk.Label, path: str, *args):
        label.stop_emission_by_name("activate-link")
        variant = GLib.Variant.new_string(path)
        self.activate_action("win.open_page", variant)

    def load_uri(self, uri: str):
        self.setup_search_signals()
        uri = unquote(uri)
        uri = self.clean_uri(uri)

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

    def remove_xml_and_load_new_content(self, web_view):
        current_uri: str = web_view.get_uri()
        resource_path: str = current_uri.split("#")[0]
        if resource_path.startswith("file://"):
            resource_path = resource_path.replace("file://", "")
            with open(resource_path, "r+") as resource:
                soup = BeautifulSoup(resource, "html.parser")
                for xml_tag in soup.find_all("xml"): # delete all xml tags if in document
                    xml_tag.decompose() 

                for element in soup.find_all("html"): # remove xml related attributes from the html tag
                    element.attrs.pop("xmlns", None)
                    element.attrs.pop("xml:lang", None)

                web_view.load_alternate_html(str(soup), current_uri, current_uri)
                
                    

    def on_load_failed(self, web_view, load_event, failing_uri: str, error):
        print(error)

    def on_mouse_target_changed(
        self, web_view: WebKit.WebView, hit_test_result: WebKit.HitTestResult, *args
    ):
        uri = hit_test_result.get_link_uri()
        if uri:
            pass

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
