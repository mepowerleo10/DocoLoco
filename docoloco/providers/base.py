from abc import ABC
from pathlib import Path
from typing import Dict

from ..models import DocSet


class DocumentationProvider(ABC):
    def __init__(self) -> None:
        super().__init__()

        self.name: str = None
        self.docs: Dict[str, DocSet] = dict()
        self.root_path: Path = None

    def load(self) -> None:
        pass
