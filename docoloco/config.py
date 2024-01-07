import json
import shutil
from pathlib import Path

import yaml

from gi.repository import GLib

APPLICATION_ID = "org.docoloco.DocoLoco"


class Config:
    def __init__(self) -> None:
        self.data_dir = Path(__file__).parent.parent / "data"
        self.ui_dir = Path(__file__).parent / "ui"
        self.templates_dir = self.ui_dir / "templates"
        self.styles_dir = self.ui_dir / "styles"

        self.initialize_settings()
        print(self._settings)

    def template(self, name: str) -> str:
        return (self.templates_dir / f"{name}.ui").as_posix()

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
    def application_config_dir(self) -> Path:
        config_dir = self.user_config_dir / APPLICATION_ID
        config_dir.mkdir(parents=True, exist_ok=True)

        return config_dir

    @property
    def user_state_dir(self) -> Path:
        return Path(GLib.get_user_state_dir())

    def initialize_settings(self):
        settings_path = self.application_config_dir / f"{APPLICATION_ID}.yaml"
        if not settings_path.exists():
            shutil.copyfile(
                src=(self.data_dir / f"{APPLICATION_ID}.yaml").as_posix(),
                dst=settings_path.as_posix(),
            )

        with open(settings_path, "r+") as settings_file:
            self._settings = yaml.safe_load(settings_file)


default_config = Config()
