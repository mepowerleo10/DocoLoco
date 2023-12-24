import html
import re
from urllib.parse import unquote

from .section_widget import SectionWidget

from ..models import Doc, Section, DocSet

from .new_page import NewPage
from ..config import default_config
import gi
from typing import cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit, Pango


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

        self._update_sections()

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
                section.set_margin_top(6)
                section.set_margin_bottom(6)

                item_list = Gtk.ListBox()
                item_list.set_margin_top(3)
                item_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

                for doc in docs:
                    item_label = Gtk.Label(halign=Gtk.Align.START)
                    item_label.set_markup(
                        f"<a href='{doc.path}'>{html.escape(doc.name)}</a>"
                    )
                    item_label.set_cursor(Gdk.Cursor.new_from_name("pointer"))
                    item_label.set_margin_start(10)
                    item_label.set_ellipsize(Pango.EllipsizeMode.END)
                    item_label.set_tooltip_text(doc.name)

                    item_label.connect("activate-link", self.on_item_clicked)
                    item_label.connect("activate-current-link", self.on_item_clicked)
                    item_list.append(item_label)

                section.set_child(item_list)
                list_box.append(section)
                # self.sidebar.append(section)

        scrolled_window = Gtk.ScrolledWindow()
        # scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(list_box)
        scrolled_window.set_vexpand(True)
        self.sidebar.append(scrolled_window)

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
        # sections_tree.connect("activate", self._on_subdocument_clicked)

        scrolled_window = Gtk.ScrolledWindow()
        # scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
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
        self.activate_action(f"win.open_page", variant)

    def load_uri(self, uri: str):
        self.setup_search_signals()
        uri = unquote(uri)
        uri = self.clean_uri(uri)

        # content = self.get_content(uri)
        # self.web_view.load_html(content, uri)

        self.web_view.load_uri(uri)
        # self.web_view.bind_property("title", self, "title", GObject.BindingFlags.DEFAULT)
        self.web_view.connect("load-changed", self.on_load_changed)

    def get_content(self, uri: str):
        uri = uri.split("://")[1].split("#")[0]
        with open(uri, "r") as file:
            content = "".join(file.readlines())
            cleand_content = processed_xml = content.replace(
                "<?xml", "<!--?xml"
            ).replace("?>", "?-->")
            return cleand_content

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
        self.web_view.go_back()

    def can_go_forward(self) -> bool:
        return self.web_view.can_go_forward()

    def go_forward(self, *args):
        return self.web_view.go_forward()

    def page_search(self, *args):
        self.search_bar.set_search_mode(True)
