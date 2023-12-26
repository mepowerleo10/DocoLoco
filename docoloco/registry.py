from typing import Dict, List

from .models import Doc, DocSet
from .providers.base import DocumentationProvider
from .providers.dash_provider import DashProvider


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
