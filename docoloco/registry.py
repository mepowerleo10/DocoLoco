from abc import ABC
from pathlib import Path
from typing import Dict, List

from tomlkit import value

from .models import DocSet, Doc


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


class Registry:
    providers: List[DocumentationProvider] = [
        DashProvider(),
    ]
    entries: Dict[str, DocSet] = dict()

    def __init__(self) -> None:
        self.initialize_providers()

    def initialize_providers(self):
        for provider in self.providers:
            provider.load()
            self.entries |= provider.docs

    def search(self, term: str) -> List[Doc]:
        results: List[Doc] = list()
        for key, entry in self.entries:
            res = entry.search(term)
            results.extend(res)

        return results

    def get(self, key: str) -> DocSet:
        return self.entries.get(key)


registry = Registry()


def get_registry():
    return registry


provider = DashProvider()


def initialize_providers():
    provider.load()
