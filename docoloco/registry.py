
from abc import ABC
from pathlib import Path
from typing import List

from .models import DocSet


class DocumentationProvider(ABC):
    def __init__(self) -> None:
        super().__init__()

        self.name: str = None
        self.docs: List[DocSet] = list()
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
                self.docs.append(doc)
            except Exception as e:
                print(e)


registered_providers = [DashProvider()]


def initialize_providers():
    for provider in registered_providers:
        provider.load()
