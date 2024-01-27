import json
import subprocess
from pathlib import Path
from shutil import copyfile
from typing import Dict, List

from bs4 import BeautifulSoup

from .views import ManDocsetsView
from gi.repository.Gio import ListStore

from docoloco.config import default_config
from docoloco.models import Doc, DocSet
from docoloco.providers import DocumentationProvider


class ManProvider(DocumentationProvider):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Man Pages"
        self.type = DocumentationProvider.Type.QUERYABLE
        self.icon_path = default_config.icon("providers/man.png")

    def query(self, name: str) -> List[DocSet]:
        self.query_results_model.remove_all()

        process = subprocess.Popen(
            ["man", "-k", "--regex", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, error = process.communicate()

        if process.returncode == 0:
            output_lines = output.decode().splitlines()[:100]
            for line in output_lines:
                parts = line.split("(")
                name = parts[0].strip()

                doc = ManDocSet(provider_id=self.name, name=name, description=line)
                self.query_results_model.append(doc)
        else:
            print(error.decode())

    def get_view(self):
        return ManDocsetsView(self)


class ManDocSet(DocSet):
    __gtype_name__ = "ManDocSet"

    def __init__(self, provider_id: str, name: str, description: str):
        super().__init__(provider_id)

        self.name = self.title = name
        self.description = description
        self.path: Path = None
        self.related_docs = self.new_docs_list()
        self.cache_dir = default_config.user_cache_dir / "DocoLoco/ManPages"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.icon_files = [Path(default_config.icon("providers/man.png"))]

        self.style_file = self.cache_dir / "style.css"
        if not self.style_file.exists():
            copyfile(default_config.get_path_from_style("mandoc.css"), self.style_file)

    def populate_all_sections(self) -> None:
        self.set_paths()

        if not self.index_file_path.exists():
            self.build_manpage_metadata()

        self.load_symbols()

    def set_paths(self):
        process = subprocess.Popen(
            ["man", "-w", self.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, error = process.communicate()

        if process.returncode == 0:
            self.path = Path(output.decode().strip())
            self.dir = self.path.parent

            self.dir = self.cache_dir / self.dir.name
            self.dir.mkdir(parents=True, exist_ok=True)

            self.index_file_path = self.dir / f"{self.name}.html"
            self.metadata_path = self.dir / f"{self.index_file_path.stem}.metadata.json"
        else:
            print(error.decode())

    def load_symbols(self):
        with open(self.metadata_path, "r") as metadata_file:
            metadata: Dict = json.load(metadata_file)
            type = "Section"
            for name, path in metadata.items():
                doc = Doc(name, type, path)
                self.related_docs.append(doc)

    def build_manpage_metadata(self):
        process = subprocess.Popen(
            [
                "mandoc",
                "-T",
                "html",
                "-O",
                f"style={self.style_file.as_posix()}",
                self.path.as_posix(),
            ],
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
                symbols[heading.get_text(strip=True).replace("\n", "")] = (
                    self.index_file_path / f"#{heading['id']}"
                ).as_uri()

        with open(self.metadata_path, "w") as metadata_file:
            json.dump(symbols, metadata_file)

    def related_docs_of(self, url: str) -> ListStore:
        return self.related_docs
