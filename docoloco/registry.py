from abc import ABC
from pathlib import Path
from typing import Dict, List

from .models import DocSet


class DocumentationProvider(ABC):
    def __init__(self) -> None:
        super().__init__()

        self.name: str = None
        self.docs: Dict[str, DocSet] = dict()
        self.root_path: Path = None

    def load(self) -> None:
        pass


class DashProvider(DocumentationProvider):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Dash"
        self.root_path = Path("/home/mepowerleo10/.local/share/Zeal/Zeal/docsets/")

    def load(self):
        for doc_path in self.root_path.iterdir():
            try:
                doc = DocSet(path=doc_path)
                self.docs[doc.name] = doc
            except Exception as e:
                print(e)


provider = DashProvider()

def initialize_providers():
    provider.load()
