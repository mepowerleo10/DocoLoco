class Config:
  def __init__(self) -> None:
    self.data_path = "data"
    self.ui_path = f"{self.data_path}/ui"

  def ui(self, name: str) -> str:
    return f"{self.ui_path}/{name}.ui" 
  
default_config = Config()