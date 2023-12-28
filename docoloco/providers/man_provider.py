import json
import subprocess
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

from ..models.base import Doc

from ..models import DocSet
from .base import DocumentationProvider


class ManProvider(DocumentationProvider):
    def __init__(self, name: str, path: Path) -> None:
        super().__init__()
        self.name = name
        self.root_path = path

    def load(self) -> None:
        count = 0
        for path in self.root_path.glob("*"):
            try:
                count += 1
                doc = ManDocSet(path)
                self.docs[doc.name] = doc

                if count > 20:
                    break

            except Exception as e:
                print(e)


class ManDocSet(DocSet):
    __gtype_name__ = "ManDocSet"

    def __init__(self, path: Path):
        super().__init__()

        self.dir = path.parent
        self.path = path

        if not self.dir.exists():
            raise ValueError(f"Docset path {self.dir} does not exist")

        self.name = self.title = path.stem

    def populate_all_sections(self) -> None:
        self.cache_directory = Path.home() / ".cache/DocoLoco/ManPages" / self.dir.name
        self.cache_directory.mkdir(parents=True, exist_ok=True)

        self.index_file_path = self.cache_directory / f"{self.name}.html"
        self.metadata_path = self.cache_directory / f"{self.index_file_path.stem}.metadata.json"

        if not self.index_file_path.exists():
            self.build_manpage_metadata()
        
        self.load_symbols()

    def load_symbols(self):
        with open(self.metadata_path, "r") as metadata_file:
            metadata: Dict = json.load(metadata_file)

            type = "Section"
            self.symbol_counts[type] = len(metadata.keys())

            section_items = self.new_docs_list()
            for name, path in metadata.items():
                doc = Doc(name, type, path)
                section_items.append(doc)
            
            self.sections[type] = section_items

    def build_manpage_metadata(self):
        process = subprocess.Popen(
            ["mandoc", "-T", "html", self.path.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, error = process.communicate()

        if process.returncode == 0:
            self.write_to_html(output)
            self.extract_symbol_metadata(output)
        else:
            print(error.decode("utf-8"))

    def write_to_html(self, output):
        with open(self.index_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(output.decode("utf-8"))

    def extract_symbol_metadata(self, content: str):
        soup = BeautifulSoup(content, "html.parser")
        symbols = {}

        for section in soup.find_all("section"):
            heading_elements = section.find_all("h1", {"id": True})
            for heading in heading_elements:
                symbols[heading.get_text(strip=True).replace("\n", "")] = (self.index_file_path / f"#{heading["id"]}" ).as_uri()
        
        with open(self.metadata_path, "w") as metadata_file:
            json.dump(symbols, metadata_file)
        

def get_all_man_providers() -> List[ManProvider]:
    man_pages_path = Path("/usr/share/man")
    man_sections = {
        1: "Executable Programs or Shell Programs",
        2: "System Calls",
    }

    providers = []
    for index, name in man_sections.items():
        provider = ManProvider(name, man_pages_path / f"man{index}/")
        providers.append(provider)

    return providers
