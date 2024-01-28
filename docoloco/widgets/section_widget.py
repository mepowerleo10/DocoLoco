import html
from typing import cast

import gi

from ..config import default_config
from ..models import Doc, DocSet, Section

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango  # noqa: E402


def plurarize(val: str) -> str:
    last_char = val[-1]
    match last_char:
        case "s":
            return f"{val}es"
        case "y":
            return f"{val[:-1]}ies"
        case _:
            return f"{val}s"


@Gtk.Template(filename=default_config.template("section"))
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

            self.label.set_label(f"{plurarize(section.title)} ({section.count})")
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
            f"<a href='{html.escape(doc.url)}'>{html.escape(doc.name)}</a>"
        )
        label.set_cursor(Gdk.Cursor.new_from_name("pointer"))
        label.set_margin_start(10)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_tooltip_text(doc.name)

        label.connect("activate-link", self.on_item_clicked)
        label.connect("activate-current-link", self.on_item_clicked)

        menu = Gio.Menu()
        menu.append(
            "Open In New Tab",
            f"win.open_in_new_tab({GLib.Variant('(sss)', (doc.url, self.docset.provider_id, self.docset.name))})",
        )
        label.set_extra_menu(menu)

    def on_item_clicked(self, label: Gtk.Label, path: str, *args):
        label.stop_emission_by_name("activate-link")

        if path == "more":
            self.docset.populate_section(self.section.title)
        else:
            variant = GLib.Variant.new_string(path)
            self.activate_action("win.open_page", variant)
