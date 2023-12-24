import html
from ..models import Section, Doc, DocSet
import gi
from typing import cast

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject, WebKit, Pango

from ..config import default_config


@Gtk.Template(filename=default_config.ui("section"))
class SectionWidget(Adw.Bin):
    __gtype_name__ = "SectionWidget"

    expander = cast(Gtk.Expander, Gtk.Template.Child())
    icon = cast(Gtk.Image, Gtk.Template.Child("icon"))
    label = cast(Gtk.Label, Gtk.Template.Child("label"))
    list_view = cast(Gtk.ListView, Gtk.Template.Child())

    docset: DocSet = None
    section: Section = None

    def __init__(self, section: Section = None, docset: DocSet = None):
        super().__init__()
        self.build_with(section, docset)

    def build_with(self, section: Section, docset: DocSet):
        if docset and section:
            self.section = section
            self.docset = docset

            self.label.set_label(f"{section.title} ({section.count})")
            self.icon.set_from_icon_name(section.icon_name)

            docs_list_store = self.docset.sections[self.section.title]

            list_model = Gtk.SingleSelection(model=docs_list_store)
            self.list_view.set_model(list_model)

            view_factory = Gtk.SignalListItemFactory()
            view_factory.connect("setup", self.setup_doc_widget)
            view_factory.connect("bind", self.bind_doc_widget)
            self.list_view.set_factory(view_factory)

    def setup_doc_widget(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = Gtk.Box()
        icon = Gtk.Image()
        label = Gtk.Label()

        box.append(icon)
        box.append(label)
        list_item.set_child(box)

    def bind_doc_widget(self, factory, obj: GObject.Object):
        list_item = cast(Gtk.ListItem, obj)
        box = cast(Gtk.Box, list_item.get_child())
        icon = cast(Gtk.Image, box.get_first_child())
        label = cast(Gtk.Label, box.get_last_child())

        doc = cast(Doc, list_item.get_item())
        label.set_markup(
            f"<a href='{html.escape(doc.path)}'>{html.escape(doc.name)}</a>"
        )
        label.set_cursor(Gdk.Cursor.new_from_name("pointer"))
        label.set_margin_start(10)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_tooltip_text(doc.name)

        label.connect("activate-link", self.on_item_clicked)
        label.connect("activate-current-link", self.on_item_clicked)

        box.append(icon)
        box.append(label)
        list_item.set_child(box)

    def on_item_clicked(self, label: Gtk.Label, path: str, *args):
        label.stop_emission_by_name("activate-link")

        if path == "more":
            self.docset.populate_section(self.section.title)
        else:
            variant = GLib.Variant.new_string(path)
            self.activate_action(f"win.open_page", variant)
