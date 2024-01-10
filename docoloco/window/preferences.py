from typing import cast
from ..helpers import is_valid_url
import gi
from docoloco.config import default_config

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402


@Gtk.Template(filename=default_config.template("preferences"))
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"
    download_btn = cast(Gtk.Button, Gtk.Template.Child())

    def __init__(self, parent_window):
        super().__init__()

        self.set_transient_for(parent_window)
        self.props.modal = True

        self.download_website_url: str = None
        self.download_website_task: Gio.Task = None

    @Gtk.Template.Callback()
    def on_url_apply(self, *args):
        self.download_btn.set_visible(True)

    @Gtk.Template.Callback()
    def on_url_changed(self, entry: Adw.EntryRow):
        url = cast(str, entry.get_text()).strip()
        self.download_btn.set_visible(False)
        if is_valid_url(url):
            entry.set_show_apply_button(True)
            self.download_website_url = url
        else:
            entry.set_show_apply_button(False)

    @Gtk.Template.Callback()
    def on_click_download(self, *args):
        page = Adw.NavigationPage(title="Download Progress")
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_vexpand(True)
        vbox.set_vexpand_set(True)

        label = Gtk.Label()
        label.set_label(f"Downloading {self.download_website_url}")
        vbox.append(label)

        spinner = Gtk.Spinner()
        spinner.start()
        vbox.append(spinner)

        button = Gtk.Button()
        button.set_label("Cancel")
        button.set_halign(Gtk.Align.CENTER)
        button.connect("clicked", self.on_cancel_download)
        vbox.append(button)

        page.set_child(vbox)
        self.push_subpage(page)

        self.download_website_task = Gio.Task.new(
            source_object=self, callback=self.on_download_website_complete
        )
        GLib.idle_add(self.download_website, self.download_website_task)

    def on_cancel_download(self, *args):
        self.pop_subpage()

    def download_website(self, *args):
        self.on_download_website_complete()
        return False

    def on_download_website_complete(self, *args):
        pass
