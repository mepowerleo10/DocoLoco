from collections import OrderedDict
from typing import Dict, List

from .models import Doc, DocSet
from .providers.base import DocumentationProvider
from .providers.dash_provider import DashProvider
from .providers.man_provider import ManProvider, get_all_man_providers


class Registry:
    providers: List[DocumentationProvider] = [
        DashProvider(),
    ]
    entries: Dict[str, DocSet] = dict()

    def __init__(self) -> None:
        self.providers.extend(get_all_man_providers())

        self.initialize_providers()

    def initialize_providers(self):
        for provider in self.providers:
            provider.load()

            sorted_docs = OrderedDict(sorted(provider.docs.items()))
            self.entries |= sorted_docs

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
