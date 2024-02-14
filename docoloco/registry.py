from typing import Dict, List

from gi.repository import Gio

from docoloco.config import default_config
from docoloco.models import DocSet, SearchResult
from docoloco.providers import DocumentationProvider
from docoloco.providers.dash import DashProvider
from docoloco.providers.man import ManProvider


class Registry:
    providers: Dict[str, DocumentationProvider] = None

    def __init__(self, providers: List[DocumentationProvider]) -> None:
        self.providers = dict((provider.id, provider) for provider in providers)
        self.initialize_providers()

    def initialize_providers(self):
        for _, provider in self.providers.items():
            provider.load()

    def search(self, term: str):
        term = term.strip().lower()
        if ":" in term:
            provider_id, term = term.split(":", 1)
            provider = self.providers.get(provider_id)
            results = provider.query(term)
        else:
            results = Gio.ListStore(item_type=SearchResult)
            for _, provider in self.providers.items():
                if provider.type == DocumentationProvider.Type.QUERYABLE:
                    continue

                results.splice(
                    results.get_n_items(),
                    0,
                    provider.query(term),
                )

        return results

    def get(self, provider_id: str, docset_name: str, position: int) -> DocSet:
        provider = self.providers.get(provider_id)
        return provider.get(name=docset_name, position=position)


registry = Registry(
    providers=[
        DashProvider(
            id="zeal",
            name="Zeal",
            root_path=default_config.user_data_dir / "Zeal/Zeal/docsets/",
        ),
        ManProvider(),
    ]
)


def get_registry():
    return registry
