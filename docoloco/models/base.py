from pathlib import Path
from typing import Dict, List, Set

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gio, GObject  # noqa: E402


class IconsMixin:
    icons = {
        "Attribute": "lang-typedef-symbolic",
        "Binding": "lang-define-symbolic",
        "Category": "lang-include-symbolic",
        "Class": "lang-class-symbolic",
        "Constant": "lang-union-symbolic",
        "Constructor": "lang-method-symbolic",
        "Enumeration": "lang-enum-symbolic",
        "Event": "lang-include-symbolic",
        "Exception": "tools-check-spelling-symbolic",
        "Field": "lang-variable-symbolic",
        "Function": "lang-function-symbolic",
        "Guide": "accessories-text-editor-symbolic",
        "Interface": "lang-define-symbolic",
        "Namespace": "lang-namespace-symbolic",
        "Macro": "lang-define-symbolic",
        "Method": "lang-method-symbolic",
        "Operator": "lang-typedef-symbolic",
        "Package": "lang-namespace-symbolic",
        "Property": "lang-variable-symbolic",
        "Protocol": "lang-typedef-symbolic",
        "Structure": "lang-struct-symbolic",
        "Type": "lang-typedef-symbolic",
        "Variable": "lang-variable-symbolic",
    }


class Section(GObject.Object, IconsMixin):
    def __init__(self, title: str, count: int):
        super().__init__()

        self.title = title
        self.count = count

    @property
    def icon_name(self) -> str:
        return self.icons.get(self.title, "lang-include-symbolic")


class Doc(GObject.Object, IconsMixin):
    def __init__(self, name: str, type: str, path: str, fragment: str = None):
        super().__init__()

        self.name = name
        self.type = type
        self.path = path
        self.fragment = fragment
        self._url: str = None

    @property
    def url(self) -> str:
        if not self._url:
            real_path = None
            real_fragment = None

            if not self.fragment:
                url_parts = self.path.split("#")
                real_path = url_parts[0]
                if len(url_parts) > 1:
                    real_fragment = url_parts[1]
            else:
                real_path = self.path
                real_fragment = self.fragment

            self._url = real_path

            if real_fragment:
                self._url = f"{self._url}#{real_fragment}"

        return self._url

    @property
    def icon_name(self) -> str:
        return self.icons.get(self.type, "lang-include-symbolic")


class DocSet(GObject.Object):
    __gtype_name__ = "DocSet"

    dir: Path = None
    name: str = None
    title: str = None
    description: str = None
    version: str = None
    index_file_path: Path = None
    is_javascript_enabled = True
    icon_files: List[Path] = None

    def __init__(self, provider_id: str):
        super().__init__()

        self.provider_id = provider_id
        self.keywords: Set[str] = set()
        self.symbol_strings: Dict[str, List] = dict()
        self.symbol_counts: Dict[str, int] = dict()
        self.sections: Dict[str, Gio.ListStore] = dict()

    def search(self, value: str, section: str = None) -> List[Doc]:
        """Search the docset for a value, and return a list of `Doc` objects."""
        ...

    def populate_all_sections(self) -> None:
        """Add links to all Sections.
        It is recommended to add no more than 20 links per each section for perfomance.
        """
        ...

    def populate_section(self, name: str) -> None:
        """Populate a specific section of the documentation"""
        ...

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

    def related_docs_of(self, url: str) -> Gio.ListStore:
        ...

    def new_docs_list(self) -> Gio.ListStore:
        return Gio.ListStore(item_type=Doc)

    @property
    def is_populated(self) -> bool:
        return len(self.sections) > 0

    @property
    def icon(self):
        if self.icon_files:
            icon_path: Path = self.icon_files[0]
            icon = Gio.FileIcon.new_for_string(icon_path.as_posix())
        else:
            icon = Gio.icon_new_for_string("accessories-dictionary-symbolic")

        return icon

    @property
    def is_loaded(self):
        return len(self.sections) > 0
