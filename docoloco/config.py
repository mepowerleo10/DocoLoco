from pathlib import Path

from gi.repository import GLib


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
