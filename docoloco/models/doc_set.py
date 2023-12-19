from collections import namedtuple
from enum import Enum
import json
from pathlib import Path
import plistlib
import sqlite3
from typing import Dict, List
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject


def namedtuple_factory(cursor: sqlite3.Cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)


class Doc(GObject.Object):
    def __init__(self, name: str, type: str, path: str):
        super().__init__()

        self.name = name
        self.type = type
        self.path = path

    @property
    def icon_name(self) -> str:
        icons = {
            "Attribute": "lang-define-symbolic",
            "Binding": "lang-define-symbolic",
            "Category": "lang-include-symbolic",
            "Class": "lang-class-symbolic",
            "Constant": "lang-union-symbolic",
            "Constructor": "lang-method-symbolic",
            "Enumeration": "lang-enum-symbolic",
            "Event": "lang-include-symbolic",
            "Field": "lang-variable-symbolic",
            "Function": "lang-function-symbolic",
            "Guide": "open-book-symbolic",
            "Namespace": "lang-namespace-symbolic",
            "Macro": "lang-define-symbolic",
            "Method": "lang-method-symbolic",
            "Operator": "lang-typedef-symbolic",
            "Property": "lang-variable-symbolic",
            "Protocol": "lang-typedef-symbolic",
            "Structure": "lang-struct-symbolic",
            "Type": "lang-typedef-symbolic",
            "Variable": "lang-variable-symbolic",
        }

        return icons.get(self.type, "lang-include-symbolic")


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


class DocSet(GObject.Object):
    class Type(Enum):
        DASH = 1
        ZDASH = 2
        INVALID = 3

    def __init__(self, path: Path) -> None:
        self.dir = path
        if not self.dir.exists():
            raise ValueError(f"Docset path {self.dir} does not exist")

        # Required Description Fields
        self.name: str = None
        self.version: str = None
        self.revision: str = None
        self.title: str = None

        # Optional Description fields
        self.is_javascript_enabled: bool = None
        self.index_file_path: Path = None
        self.type = self.Type.DASH

        self.meta: Dict = None
        self.load_metadata()

        self.icon_files: list = self.dir.glob("icon*.*")

        self.plist: Dict = None
        self.load_plist_info()

        self.resources_dir = self.contents_dir / "Resources"
        if not self.resources_dir.exists():
            raise ValueError(f"Resources path {self.resources_dir} does not exist")

        self.load_database()

        self.documents_dir = self.resources_dir / "Documents"

        self.keywords: List[str] = []
        self.setup_keywords()

        self.keywords = set(self.keywords)

        if InfoPlist.DashIndexFilePath in self.plist:
            index_file: Path = self.documents_dir / self.plist.get(
                InfoPlist.DashIndexFilePath
            )
            self.index_file_path = (
                index_file if index_file.exists() else self.index_file_path
            )

        if not self.index_file_path and (self.documents_dir / "index.html").exists():
            self.index_file_path = self.documents_dir / "index.html"

        self.symbol_strings: Dict[str, List] = {}
        self.symbol_counts = {}
        self.count_symbols()

    def load_metadata(self):
        """Reads the meta.json file"""

        self.contents_dir = self.dir / "Contents"

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
                self.keywords = [word for word in extra.get("keyword", [])]

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
        self.database_path = self.resources_dir / "docSet.dsidx"
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
                self.keywords.append(self.plist.get(key))

    def count_symbols(self):
        query = "SELECT type as value, COUNT(*) as count FROM searchIndex GROUP BY type"
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

    def search(self, value: str) -> List[Doc]:
        query = f"SELECT name as name, type as type, path as path FROM searchIndex WHERE name LIKE '%{value}%' LIMIT 20"
        rows: sqlite3.Cursor = self.con.cursor().execute(query)

        results: List[Doc] = []
        for row in rows.fetchall():
            symbol_type = self.parse_symbol_type(row.type)
            doc = Doc(name=row.name, type=symbol_type, path=row.path)
            results.append(doc)

        return results

    def parse_symbol_type(self, value: str):
        aliases = {
            # Attribute
            "Package Attributes": "Attribute",
            "Private Attributes": "Attribute",
            "Protected Attributes": "Attribute",
            "Public Attributes": "Attribute",
            "Static Package Attributes": "Attribute",
            "Static Private Attributes": "Attribute",
            "Static Protected Attributes": "Attribute",
            "Static Public Attributes": "Attribute",
            "XML Attributes": "Attribute",
            # Binding
            "binding": "Binding",
            # Category
            "cat": "Category",
            "Groups": "Category",
            "Pages": "Category",
            # Class
            "cl": "Class",
            "specialization": "Class",
            "tmplt": "Class",
            # Constant
            "data": "Constant",
            "econst": "Constant",
            "enumdata": "Constant",
            "enumelt": "Constant",
            "clconst": "Constant",
            "structdata": "Constant",
            "writerid": "Constant",
            "Notifications": "Constant",
            # Constructor
            "structctr": "Constructor",
            "Public Constructors": "Constructor",
            # Enumeration
            "enum": "Enumeration",
            "Enum": "Enumeration",
            "Enumerations": "Enumeration",
            # Event
            "event": "Event",
            "Public Events": "Event",
            "Inherited Events": "Event",
            "Private Events": "Event",
            # Field
            "Data Fields": "Field",
            # Function
            "dcop": "Function",
            "func": "Function",
            "ffunc": "Function",
            "signal": "Function",
            "slot": "Function",
            "grammar": "Function",
            "Function Prototypes": "Function",
            "Functions/Subroutines": "Function",
            "Members": "Function",
            "Package Functions": "Function",
            "Private Member Functions": "Function",
            "Private Slots": "Function",
            "Protected Member Functions": "Function",
            "Protected Slots": "Function",
            "Public Member Functions": "Function",
            "Public Slots": "Function",
            "Signals": "Function",
            "Static Package Functions": "Function",
            "Static Private Member Functions": "Function",
            "Static Protected Member Functions": "Function",
            "Static Public Member Functions": "Function",
            # Guide
            "doc": "Guide",
            # Namespace
            "ns": "Namespace",
            # Macro
            "macro": "Macro",
            # Method
            "clm": "Method",
            "enumcm": "Method",
            "enumctr": "Method",
            "enumm": "Method",
            "intfctr": "Method",
            "intfcm": "Method",
            "intfm": "Method",
            "intfsub": "Method",
            "instsub": "Method",
            "instctr": "Method",
            "instm": "Method",
            "structcm": "Method",
            "structm": "Method",
            "structsub": "Method",
            "Class Methods": "Method",
            "Inherited Methods": "Method",
            "Instance Methods": "Method",
            "Private Methods": "Method",
            "Protected Methods": "Method",
            "Public Methods": "Method",
            # Operator
            "intfopfunc": "Operator",
            "opfunc": "Operator",
            # Property
            "enump": "Property",
            "intfdata": "Property",
            "intfp": "Property",
            "instp": "Property",
            "structp": "Property",
            "Inherited Properties": "Property",
            "Private Properties": "Property",
            "Protected Properties": "Property",
            "Public Properties": "Property",
            # Protocol
            "intf": "Protocol",
            # Structure
            "_Struct": "Structure",
            "_Structs": "Structure",
            "struct": "Structure",
            "Сontrol Structure": "Structure",
            "Data Structures": "Structure",
            "Struct": "Structure",
            # Type
            "tag": "Type",
            "tdef": "Type",
            "Data Types": "Type",
            "Package Types": "Type",
            "Private Types": "Type",
            "Protected Types": "Type",
            "Public Types": "Type",
            "Typedefs": "Type",
            # Variable
            "var": "Variable",
        }

        return aliases.get(value, value)

    @property
    def icon(self):
        icon_path: Path = next(self.icon_files)
        icon = Gio.FileIcon.new_for_string(icon_path.as_posix())
        return icon
