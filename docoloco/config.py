from pathlib import Path


class Config:
    def __init__(self) -> None:
        self.data_dir = "data"
        self.ui_dir = f"{self.data_dir}/ui"

    def ui(self, name: str) -> str:
        return f"{self.ui_dir}/{name}.ui"

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).absolute()

    def get_path_from_data(self, name: str) -> Path:
        return self.data_path / name


default_config = Config()
