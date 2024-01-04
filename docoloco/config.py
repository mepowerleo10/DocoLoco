from pathlib import Path

from gi.repository import GLib


class Config:
    def __init__(self) -> None:
        self.data_dir = "data"
        self.ui_dir = Path(__file__).parent / "ui"
        self.templates_dir = self.ui_dir / "templates"
        self.styles_dir = self.ui_dir / "styles"

    def template(self, name: str) -> str:
        return self.templates_dir/ f"{name}.ui"

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).absolute()

    def get_path_from_style(self, name: str) -> Path:
        return self.styles_dir / name

    @property
    def user_data_dir(self) -> Path:
        return Path(GLib.get_user_data_dir())

    @property
    def user_cache_dir(self) -> Path:
        return Path(GLib.get_user_cache_dir())

    @property
    def user_config_dir(self) -> Path:
        return Path(GLib.get_user_config_dir())

    @property
    def user_state_dir(self) -> Path:
        return Path(GLib.get_user_state_dir())


default_config = Config()
