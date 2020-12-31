from aiofiles import open as aioopen
from .client import ClientState


async def save(client_config: ClientState, file="./wire-nio.json"):
    async with aioopen(file, "w") as f:
        json = client_config.json()
        await f.write(json)


async def load(file="./wire-nio.json"):
    async with aioopen(file, "r") as f:
        string = await f.read()
        return ClientState.parse_raw(string)
