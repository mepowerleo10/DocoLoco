from gi.repository import Gio, GLib, GObject

from .helpers import is_valid_url
from .models import DocSet, SearchResult, Section
from .registry import get_registry


class SearchProvider(GObject.Object):
    def __init__(
        self,
        docset: DocSet = None,
        section: Section = None,
    ):
        super().__init__()

        self.docset = docset
        self.section = section
        self.result = Gio.ListStore(item_type=SearchResult)

    def search(self, word: str):
        self.result.remove_all()
        word = word.strip().lower()

        if self.docset:
            if not self.section and (not word or len(word) == 0):
                self.show_sections()
            else:
                self.find_in_docset(word)
        else:
            self.filter_docsets(word)

    def find_in_docset(self, word):
        results = (
            self.docset.search(word, self.section.title)
            if self.section
            else self.docset.search(word)
        )

        if not results:
            return

        self.result.splice(0, self.result.get_n_items(), results)

        if self.result.get_n_items() == 0:
            query = f'"{self.docset.name}" {word}'
            google_item = SearchResult(
                title=f"Google - {word}",
                icon="web-browser-symbolic",
                has_child=False,
                action_name="win.open_page_uri",
                action_args=GLib.Variant.new_string(
                    f"https://google.com/search?q={query}"
                ),
            )
            self.result.append(google_item)

        if is_valid_url(word):
            url_link_item = SearchResult(
                title=f"Open Link - {word}",
                icon="emblem-symbolic-link",
                has_child=False,
                action_name="win.open_page_uri",
                action_args=GLib.Variant.new_string(word),
            )
            self.result.insert(0, url_link_item)

    def filter_docsets(self, word: str):
        results = get_registry().search(word)
        self.result.splice(0, self.result.get_n_items(), results)

    def show_sections(self):
        for title, count in self.docset.symbol_counts.items():
            section = Section(title, count)
            self.result.append(
                SearchResult(
                    title=section.title,
                    icon=section.icon_name,
                    has_child=True,
                    action_name="win.change_section",
                    action_args=GLib.Variant.new_string(section.title),
                )
            )
