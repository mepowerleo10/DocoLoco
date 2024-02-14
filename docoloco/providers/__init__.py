from enum import Enum
from pathlib import Path
from typing import Dict, Protocol, TypeVar
from docoloco.models import SearchResult

import gi

from ..models import DocSet

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gio, GObject, Gtk  # noqa: E402

T = TypeVar("T")


class DocumentationProviderView(Protocol):
    def filter_or_find(self, value: str):
        ...

    def get_menu_widget(self) -> Gtk.Widget:
        ...


class DocumentationProvider(GObject.Object):
    class Type(Enum):
        PRELOADED = 1
        QUERYABLE = 2

    def __init__(self) -> None:
        super().__init__()

        self.id: str = None
        self.name: str = None
        self.docs: Dict[str, DocSet] = dict()
        self.root_path: Path = None
        self.type = self.Type.PRELOADED
        self.icon_path: str = None

        self.query_results_model = Gio.ListStore(item_type=SearchResult)

    def load(self) -> None:
        ...

    def query(self, name: str) -> Gio.ListStore:
        ...

    def get(self, name: str = None, position: int = None) -> DocSet:
        return self.docs[name]

    def get_view(self) -> Gtk.Widget:
        ...

    @property
    def icon(self) -> Gio.Icon:
        if self.icon_path:
            icon = Gio.FileIcon.new_for_string(self.icon_path)
        else:
            icon = Gio.icon_new_for_string("accessories-dictionary-symbolic")

        return icon
