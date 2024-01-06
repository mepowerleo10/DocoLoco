import gi

from docoloco.providers import DocumentationProvider

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402


class DashDocsetsView(Gtk.FlowBox):
    def __init__(self, provider: DocumentationProvider):
        super().__init__()

        self.provider = provider

        for doc in provider.docs.values():
            box = Gtk.Box(spacing=6)

            icon = Gtk.Image()
            icon.set_from_gicon(doc.icon)
            box.append(icon)

            label = Gtk.Label(label=doc.title)
            box.append(label)

            action_params = GLib.Variant("(ssi)", (provider.name, doc.name, 0))
            button = Gtk.Button(
                action_name="win.change_docset",
                action_target=action_params,
            )
            button.set_child(box)
            self.append(button)

    def filter_or_find(self, value: str):
        value = value.strip().lower()

        def filter_func(box: Gtk.FlowBoxChild, *args):
            label = box.get_child().get_child().get_last_child()
            return value in label.get_label().lower()

        self.set_filter_func(filter_func)
