from uuid import uuid4, UUID
import time
from dataclasses import dataclass, field
from enum import Enum, auto

from typing import (
    Optional,
    Any
)


class HeaderDict(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        return super().__getitem__(key.lower())


class Method(Enum):
    GET = auto()
    POST = auto()
    PUT = auto()


class TransportResponse:
    def __init__(self, uuid: Optional[UUID] = None, timeout: float = 0.0) -> None:
        self.headers: HeaderDict = HeaderDict()
        self.content: bytes = b""
        self.status_code: Optional[int] = None
        self.uuid = uuid or uuid4()
        self.creation_time = time.time()
        self.timeout: float = timeout
        self.send_time: Optional[float] = None
        self.receive_time: Optional[float] = None
        self.request_info: Optional[Any] = None

    def add_response(self, response):
        raise NotImplementedError

    def add_data(self, content: bytes) -> None:
        self.content = self.content + content

    def mark_as_sent(self):
        self.send_time = time.time()

    def mark_as_received(self):
        self.receive_time = time.time()

    @property
    def elapsed(self) -> float:
        if (self.receive_time is not None) and (self.send_time is not None):
            elapsed = self.receive_time - self.send_time

        elif self.send_time is not None:
            elapsed = time.time() - self.send_time

        else:
            elapsed = 0.0

        return max(0, elapsed - (self.timeout / 1000))

    @property
    def text(self):
        return self.content.decode("utf-8")

    @property
    def is_ok(self):
        if self.status_code == 200:
            return True

        return False


