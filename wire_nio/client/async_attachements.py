import asyncio
import io
from functools import partial
from pathlib import Path
from typing import Any, AsyncGenerator, AsyncIterable, Dict, Iterable, Union

from aiofiles.threadpool.binary import AsyncBufferedReader

AsyncDataT = Union[
    str,
    Path,
    bytes,
    Iterable[bytes],
    AsyncIterable[bytes],
    io.BufferedIOBase,
    AsyncBufferedReader,
]
