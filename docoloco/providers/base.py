from enum import Enum
from pathlib import Path
from typing import Dict

import gi

from ..models import DocSet

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gio, GObject  # noqa: E402


class DocumentationProvider(GObject.Object):
    class Type(Enum):
        PRELOADED = 1
        QUERYABLE = 2

    def __init__(self) -> None:
        super().__init__()

        self.name: str = None
        self.docs: Dict[str, DocSet] = dict()
        self.root_path: Path = None
        self.type = self.Type.PRELOADED

        self.query_results_model = Gio.ListStore(item_type=DocSet)

    def load(self) -> None:
        ...

    def query(self, name: str):
        ...

    def get(self, name: str = None, position: int = None) -> DocSet:
        if self.type == self.Type.PRELOADED:
            return self.docs[name]
        else:
            return self.query_results_model.get_item(position)
