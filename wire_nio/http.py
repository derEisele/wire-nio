from enum import Enum, auto


class HeaderDict(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())


class Method(Enum):
    GET = auto()
    POST = auto()
    PUT = auto()
