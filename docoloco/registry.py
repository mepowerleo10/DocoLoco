from typing import Dict, List

from .models import Doc, DocSet
from .providers import DocumentationProvider
from .providers.dash import DashProvider
from .providers.man import ManProvider


class Registry:
    providers: Dict[str, DocumentationProvider] = dict()
    entries: Dict[str, DocSet] = dict()

    def __init__(self) -> None:
        registerd_providers: List[DocumentationProvider] = [
            DashProvider(),
            ManProvider(),
        ]

        for provider in registerd_providers:
            self.providers[provider.name] = provider

        self.initialize_providers()

    def initialize_providers(self):
        for _, provider in self.providers.items():
            provider.load()

    def search(self, term: str) -> List[Doc]:
        results: List[Doc] = list()
        for key, entry in self.entries:
            res = entry.search(term)
            results.extend(res)

        return results

    def get(self, provider_id: str, docset_name: str, position: int) -> DocSet:
        provider = self.providers.get(provider_id)
        return provider.get(name=docset_name, position=position)


registry = Registry()


def get_registry():
    return registry
