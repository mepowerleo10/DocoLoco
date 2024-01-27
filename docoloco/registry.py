from typing import Dict, List

from docoloco.config import default_config
from docoloco.models import Doc, DocSet
from docoloco.providers import DocumentationProvider
from docoloco.providers.dash import DashProvider
from docoloco.providers.man import ManProvider


class Registry:
    providers: Dict[str, DocumentationProvider] = dict()
    entries: Dict[str, DocSet] = dict()

    def __init__(self) -> None:
        registered_providers: List[DocumentationProvider] = [
            DashProvider(
                name="Zeal",
                root_path=default_config.user_data_dir / "Zeal/Zeal/docsets/",
            ),
            ManProvider(),
        ]

        for provider in registered_providers:
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
