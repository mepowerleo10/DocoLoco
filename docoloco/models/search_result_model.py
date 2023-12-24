from typing import List
from . import Doc
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import  Gio, GObject


class SearchResultModel(GObject.Object, Gio.ListModel):
    __gtype_name__ = "SearchResultModel"

    _data: List[Doc] = list()

    @property
    def data(self) -> List[Doc]:
        return self._data

    @data.setter
    def data(self, new_data: List[Doc]):
        self.set(data=new_data)

    def set(self, data: List[Doc]):
        old_data_size = len(self._data)
        self._data = data
        self.items_changed(position=0, added=len(self._data), removed=old_data_size)

    def reset(self):
        old_data_size = len(self._data)
        self._data.clear()
        self.items_changed(position=0, added=0, removed=old_data_size)

    def get_n_items(self):
        return len(self._data)

    def get_item(self, position=None):
        return self._data[position]

    def get_object(self, position=None):
        return self.get_item(position)

    def get_item_type(self):
        return Doc
    
