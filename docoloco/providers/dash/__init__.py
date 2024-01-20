import json
import plistlib
import sqlite3
from collections import OrderedDict, namedtuple
from enum import Enum
from pathlib import Path
from typing import Dict, List
from .views import DashDocsetsView

from gi.repository.Gio import ListStore

from docoloco.config import default_config
from docoloco.models import Doc, DocSet
from docoloco.providers import DocumentationProvider


class DashProvider(DocumentationProvider):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Dash"
        self.root_path = default_config.user_data_dir / "Zeal/Zeal/docsets/"

    def load(self):
        for doc_path in self.root_path.iterdir():
            try:
                doc = DashDocSet(provider_id=self.name, path=doc_path)
                self.docs[doc.name] = doc
            except Exception as e:
                print(e)

        self.docs = OrderedDict(sorted(self.docs.items()))

    def get_view(self):
        return DashDocsetsView(self)


def namedtuple_factory(cursor: sqlite3.Cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)


class InfoPlist:
    CFBundleName = "CFBundleName"
    CFBundleIdentifier = "CFBundleIdentifier"
    DashDocSetFamily = "DashDocSetFamily"
    DashDocSetKeyword = "DashDocSetKeyword"
    DashDocSetPluginKeyword = "DashDocSetPluginKeyword"
    DashIndexFilePath = "dashIndexFilePath"
    DocSetPlatformFamily = "DocSetPlatformFamily"
    IsDashDocset = "isDashDocset"
    IsJavaScriptEnabled = "isJavaScriptEnabled"


class DashDocSet(DocSet):
    __gtype_name__ = "DashDocSet"

    class Type(Enum):
        DASH = 1
        ZDASH = 2
        INVALID = 3

    def __init__(self, provider_id: str, path: Path) -> None:
        super().__init__(provider_id)

        self.dir = path
        if not self.dir.exists():
            raise ValueError(f"Docset path {self.dir} does not exist")

        self.icon_files: list = [icon for icon in self.dir.glob("icon*.*")]
        self.type = self.Type.DASH

        self.meta: Dict = None
        self.load_metadata()

        self.contents_dir = self.dir / "Contents"
        self.plist: Dict = None
        self.load_plist_info()

        self.resources_dir = self.contents_dir / "Resources"
        if not self.resources_dir.exists():
            raise ValueError(f"Resources path {self.resources_dir} does not exist")

        self.database_path = self.resources_dir / "docSet.dsidx"
        self.load_database()

        self.documents_dir = self.resources_dir / "Documents"
        self.setup_keywords()

        if InfoPlist.DashIndexFilePath in self.plist:
            index_file: Path = self.documents_dir / self.plist.get(
                InfoPlist.DashIndexFilePath
            )
            self.index_file_path = (
                index_file if index_file.exists() else self.index_file_path
            )

        if not self.index_file_path and (self.documents_dir / "index.html").exists():
            self.index_file_path = self.documents_dir / "index.html"

        self.count_symbols()

        # self.populate_all_sections()

    def load_metadata(self):
        """Reads the meta.json file"""

        try:
            with open(self.dir / "meta.json") as meta_file:
                self.meta = json.load(meta_file)
                self.name = self.meta.get("name", None)
                self.version = self.meta.get("version")
                self.revision = self.meta.get("revision")
                self.title = self.meta.get("title", None)

                if "extra" in self.meta.keys():
                    extra: Dict = self.meta.get("extra")
                    self.is_javascript_enabled = extra.get("isJavaScriptEnabled", None)
                    self.index_file_path = extra.get("indexFilePath", None)
                    self.keywords = set([word for word in extra.get("keyword", [])])
        except Exception as e:
            print(e)

    def load_plist_info(self):
        """Reads the Info.plist or info.plist file and prefills the metadata fields"""

        plist_path = self.contents_dir / "Info.plist"
        if not plist_path.exists():
            plist_path = self.contents_dir / "info.plist"

        with open(plist_path, "rb") as plist_file:
            self.plist: Dict = plistlib.load(plist_file)

        if not self.name:
            if InfoPlist.CFBundleName in self.plist.keys():
                self.title = self.name = self.plist[InfoPlist.CFBundleName]
                self.name = self.name.replace(" ", "_")
            else:
                self.name = self.dir.name.replace(".docset", "")

        if not self.title:
            self.title = self.name
            self.title = self.title.replace("_", " ")

        if (
            InfoPlist.DashDocSetFamily in self.plist.keys()
            and self.plist[InfoPlist.DashDocSetFamily] == "cheatsheet"
        ):
            self.name = f"{self.name} cheats"

        if InfoPlist.IsJavaScriptEnabled in self.plist.keys():
            self.is_javascript_enabled = self.plist.get(InfoPlist.IsJavaScriptEnabled)

    def load_database(self):
        if not self.database_path.exists():
            raise ValueError(f"{self.database_path} does not exist")

        self.table_name = "searchindex"
        self.con = sqlite3.connect(self.database_path)

        column_names = self.con.execute(
            f"PRAGMA table_info({self.table_name})"
        ).fetchall()

        self.type = (
            self.Type.DASH
            if "id" in [col[1] for col in column_names]
            else self.Type.ZDASH
        )

        self.con.row_factory = namedtuple_factory

    def setup_keywords(self):
        for key in [
            InfoPlist.DocSetPlatformFamily,
            InfoPlist.DashDocSetPluginKeyword,
            InfoPlist.DashDocSetKeyword,
            InfoPlist.DashDocSetFamily,
        ]:
            if key in self.plist.keys():
                self.keywords.add(self.plist.get(key))

    def count_symbols(self):
        query = f"SELECT type as value, COUNT(*) as count FROM {self.table_name} GROUP BY type"
        results: sqlite3.Cursor = self.con.cursor().execute(query)

        for row in results.fetchall():
            symbol_type_value = row.value
            if not len(symbol_type_value):
                print(f"Empty symbol type in the {self.name} docset, skipping...")
                continue

            symbol_type_key = self.parse_symbol_type(symbol_type_value)
            symbol_list = self.symbol_strings.get(symbol_type_key, list())
            symbol_list.append(symbol_type_value)
            self.symbol_strings[symbol_type_key] = symbol_list
            self.symbol_counts[symbol_type_key] = (
                self.symbol_counts.get(
                    symbol_type_value,
                    0,
                )
                + row.count
            )

    def populate_all_sections(self):
        for key in self.symbol_strings.keys():
            self.populate_section(key)

    def populate_section(self, name: str):
        section_index = self.sections.get(name, self.new_docs_list())
        section_size = section_index.get_n_items()

        page_size = 20
        if section_size > 0:
            last_item: Doc = section_index.get_item(section_size - 1)
            if last_item.type == "More":
                section_index.remove(section_size - 1)  # remove the 'More...' link

            offset = section_size - 1
        else:
            offset = 0

        also_known_as_list = self.symbol_strings[name]
        like_conditions = [f"type LIKE '%{value}%'" for value in also_known_as_list]

        columns_to_select = self.get_columns()

        query = f"SELECT {columns_to_select} FROM {self.table_name} WHERE {"OR ".join(like_conditions)} LIMIT {page_size} OFFSET {offset}"
        rows = self.con.cursor().execute(query)

        for row in rows.fetchall():
            doc = self.build_doc_from_row(row)
            section_index.append(doc)

        if section_index.get_n_items() < self.symbol_counts[name]:
            section_index.append(
                Doc("Load more ...", "More", "more")
            )  # add the 'More...' link

        self.sections[name] = section_index

    def search(self, value: str, section: str = "") -> List[Doc]:
        columns_to_select = self.get_columns()
        symbols_aka = []
        where_conditions = f"name LIKE '%{value}%'"

        if section and len(section) > 0:
            for aka in self.symbol_strings[section]:
                symbols_aka.append(f"type LIKE '%{aka}%'")

            where_conditions = f"{where_conditions} AND ({"OR ".join(symbols_aka)})"

        query = f"SELECT {columns_to_select} FROM {self.table_name} WHERE {where_conditions} LIMIT 100"
        rows: sqlite3.Cursor = self.con.cursor().execute(query)

        results: List[Doc] = []
        for row in rows.fetchall():
            doc = self.build_doc_from_row(row)
            results.append(doc)

        return results

    def related_docs_of(self, url: str) -> ListStore:
        path = url.replace(f"{self.documents_dir.as_uri()}/", "").split("#")[0]
        columns_to_select = self.get_columns()

        if self.type == self.Type.DASH:
            where_condition = f"path LIKE '%{path}%' AND path <> '%{path}'"
        else:
            where_condition = f"path LIKE '%{path}' AND fragment IS NOT NULL"

        query = (
            f"SELECT {columns_to_select} FROM {self.table_name} WHERE {where_condition}"
        )
        rows = self.con.cursor().execute(query)

        related_links = self.new_docs_list()
        for row in rows.fetchall():
            doc = self.build_doc_from_row(row)
            related_links.append(doc)

        return related_links

    def get_columns(self):
        columns_to_select = "name as name, type as type, path as path"
        if self.type != self.Type.DASH:
            columns_to_select = f"{columns_to_select}, fragment as fragment"
        return columns_to_select

    def build_doc_from_row(self, row):
        symbol_type = self.parse_symbol_type(row.type)
        doc = Doc(name=row.name, type=symbol_type, path=self.get_uri_to(row.path))
        if self.type != self.Type.DASH:
            doc.fragment = row.fragment

        return doc

    def get_uri_to(self, path: str) -> str:
        full_path = f"{self.documents_dir.as_uri()}/{path}"
        return full_path
