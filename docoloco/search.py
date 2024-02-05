from gi.repository import Gio, GObject, GLib

from .helpers import is_valid_url
from .models.base import DocSet, Section
from .providers import DocumentationProvider


class SearchResult(GObject.Object):
    __gtype_name__ = "SearchResult"

    def __init__(
        self,
        title: str,
        icon_name: str,
        has_child: bool,
        action_name: str,
        action_args: str,
    ) -> None:
        super().__init__()

        self.title = title
        self.icon_name = icon_name
        self.has_child = (has_child,)
        self.action_name = action_name
        self.action_args = action_args


class SearchProvider(GObject.Object):
    def __init__(
        self,
        provider: DocumentationProvider = None,
        docset: DocSet = None,
        section: Section = None,
    ):
        super().__init__()

        self.provider = provider
        self.docset = docset
        self.section = section
        self.result = Gio.ListStore(item_type=SearchResult)

    def search(self, word: str):
        self.result.remove_all()

        if self.docset:
            self.filter_docsets(word)

    def filter_docsets(self, word):
        results = (
            self.docset.search(word, self.section.title)
            if self.section
            else self.docset.search(word)
        )
        for item in results:
            self.result.append(
                SearchResult(
                    item.name,
                    item.icon_name,
                    False,
                    action_name="win.open_page_uri",
                    action_args=GLib.Variant.new_string(item.url),
                )
            )

        if self.result.get_n_items() == 0:
            query = f'"{self.docset.name}" {word}'
            google_item = SearchResult(
                title=f"Google - {word}",
                icon_name="web-browser-symbolic",
                has_child=False,
                action_name="win.open_page_uri",
                action_args=GLib.Variant.new_string(f"https://google.com/search?q={query}"),
            )
            self.result.append(google_item)

        if is_valid_url(word):
            url_link_item = SearchResult(
                title=f"Open Link - {word}",
                icon_name="emblem-symbolic-link",
                has_child=False,
                action_name="win.open_page_uri",
                action_args=GLib.Variant.new_string(word),
            )
            self.result.insert(0, url_link_item)
