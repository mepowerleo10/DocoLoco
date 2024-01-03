from typing import Dict
from urllib.parse import urlparse


def add_margin(widget, values: Dict[str, int]):
    for direction, value in values.items():
        func = getattr(widget, f"set_margin_{direction}", None)

        if callable(func):
            func(value)


def add_symmetric_margins(widget, vertical: int = None, horizontal: int = None):
    if vertical:
        add_margin(widget, {"top": vertical, "bottom": vertical})

    if horizontal:
        add_margin(widget, {"start": horizontal, "end": horizontal})

def is_valid_url(url):
    try:
        result = urlparse(url)
        return bool(result.netloc)
    except ValueError:
        return False