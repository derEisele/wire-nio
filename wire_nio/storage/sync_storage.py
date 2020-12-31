from .client import ClientState


def save(client_config: ClientState, file="./wire-nio.json"):
    with open(file, "w") as f:
        json = client_config.json()
        f.write(json)


def load(file="./wire-nio.json"):
    with open(file, "r") as f:
        string = f.read()
        return ClientState.parse_raw(string)
